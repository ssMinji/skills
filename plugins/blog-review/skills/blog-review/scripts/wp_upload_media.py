#!/usr/bin/env python3
"""AWS 블로그 WordPress 미디어 라이브러리에 이미지를 올리고 wordpress.md의 이미지 경로를 CDN URL로 치환한다.

사용법:
  python3 wp_upload_media.py <작업폴더> [--channel tech] [--html wordpress.md] [--dry-run]

동작:
  1. <작업폴더>/images/*.png|jpg|jpeg|gif 를 파일명 순으로 POST /wp-json/wp/v2/media 에 업로드
     (인증: ~/.midway/cookie, 사전에 mwinit -o 필요. nonce 불필요)
  2. 응답의 source_url 을 <작업폴더>/images/upload_map.json 에 기록 (이미 기록된 파일은 재업로드하지 않음)
  3. --html 로 지정한 HTML 안의 src="images/<파일>" 또는 src="<파일>" 을 CDN URL로 치환해
     <같은이름>_uploaded.md 로 저장 (원본은 덮어쓰지 않음)

채널 path: tech (aws.amazon.com/ko/blogs/tech, blog_id 65), korea (blog_id 12) 등.
"""
import argparse, json, mimetypes, pathlib, re, subprocess, sys

BASE = "https://aws-blogs-prod.amazon.com"
COOKIE = pathlib.Path.home() / ".midway" / "cookie"
EXTS = {".png", ".jpg", ".jpeg", ".gif"}

def mcurl(args, data_file=None):
    cmd = ["/usr/bin/curl", "-sL", "--cookie", str(COOKIE), "--cookie-jar", str(COOKIE),
           "-w", "\n%{http_code}"] + args
    if data_file:
        cmd += ["--data-binary", f"@{data_file}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    body, _, code = out.rpartition("\n")
    return int(code or 0), body

def check_login(channel):
    code, body = mcurl([f"{BASE}/{channel}/wp-json/wp/v2/users/me?context=view"])
    if code != 200:
        sys.exit(f"Midway 인증 실패 (HTTP {code}). 터미널에서 mwinit -o 후 다시 실행하세요.")
    me = json.loads(body)
    print(f"로그인: {me.get('name')} ({me.get('slug')}) / 채널 /{channel}/")

def upload(channel, path):
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    code, body = mcurl(["-X", "POST", f"{BASE}/{channel}/wp-json/wp/v2/media",
                        "-H", f"Content-Type: {mime}",
                        "-H", f'Content-Disposition: attachment; filename="{path.name}"'], data_file=path)
    if code != 201:
        raise RuntimeError(f"{path.name}: HTTP {code} {body[:300]}")
    d = json.loads(body)
    md = d.get("media_details", {})
    return {"id": d["id"], "url": d["source_url"], "width": md.get("width"), "height": md.get("height")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--channel", default="tech")
    ap.add_argument("--html", default="wordpress.md")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    wd = pathlib.Path(a.workdir).expanduser().resolve()
    imgdir = wd / "images"
    files = sorted(p for p in imgdir.iterdir() if p.suffix.lower() in EXTS and p.is_file())
    if not files:
        sys.exit(f"이미지 없음: {imgdir}")
    mapf = imgdir / "upload_map.json"
    umap = json.loads(mapf.read_text()) if mapf.exists() else {}

    print(f"업로드 대상 {len(files)}개 (이미 올린 {sum(p.name in umap for p in files)}개 건너뜀)")
    for p in files:
        print(f"  {p.name}  {p.stat().st_size//1024} KB")
    if a.dry_run:
        return
    check_login(a.channel)
    for p in files:
        if p.name in umap:
            continue
        r = upload(a.channel, p)
        umap[p.name] = r
        mapf.write_text(json.dumps(umap, ensure_ascii=False, indent=2))
        print(f"  올림 {p.name} -> {r['url']} ({r['width']}x{r['height']})")

    html = wd / a.html
    if not html.exists():
        print(f"HTML 없음, 치환 생략: {html}")
        return
    t = html.read_text(encoding="utf-8")
    n = 0
    for name, r in umap.items():
        pat = re.compile(r'src="(?:\./)?(?:images/)?' + re.escape(name) + '"')
        t, k = pat.subn(f'src="{r["url"]}"', t)
        n += k
    out = html.with_name(html.stem + "_uploaded" + html.suffix)
    out.write_text(t, encoding="utf-8")
    left = re.findall(r'src="(?!https?://)[^"]+"', t)
    print(f"치환 {n}건 -> {out.name}" + (f" / 미치환 src {len(left)}건: {left[:5]}" if left else " / 미치환 없음"))

if __name__ == "__main__":
    main()
