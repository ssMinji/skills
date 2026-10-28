"""Create or update a WordPress draft from wordpress.md. usage: wp_draft.py <json-spec> [--post-id N]"""
import json, subprocess, pathlib, sys
CK=str(pathlib.Path.home()/".midway"/"cookie")
spec=json.load(open(sys.argv[1]))
B=f"https://aws-blogs-prod.amazon.com/{spec.pop('channel','tech')}/wp-json/wp/v2"
spec["content"]=open(spec.pop("content_file")).read()
spec.setdefault("status","draft")
assert spec["status"]=="draft", "this tool only writes drafts"
pid = sys.argv[3] if len(sys.argv)>3 and sys.argv[2]=="--post-id" else None
url = f"{B}/posts/{pid}?context=edit" if pid else f"{B}/posts?context=edit"
tmp=pathlib.Path(sys.argv[1]).with_suffix(".body.json"); tmp.write_text(json.dumps(spec,ensure_ascii=False))
out=subprocess.run(["/usr/bin/curl","-sL","--cookie",CK,"--cookie-jar",CK,"-X","POST","-H","Content-Type: application/json; charset=utf-8","--data-binary",f"@{tmp}",url],capture_output=True,text=True).stdout
r=json.loads(out)
if "id" not in r: print(json.dumps(r,ensure_ascii=False)[:800]); sys.exit(1)
print(json.dumps({k:r.get(k) for k in ["id","status","slug","author","authors","contributors","featured_media","categories","tags","link","target_link"]},ensure_ascii=False,indent=1))
print("content chars sent/saved:", len(spec["content"]), len(r["content"]["raw"]))
