#!/usr/bin/env python3
"""wordpress.md 표의 라벨 열을 한글 어절 단위로 줄바꿈하고 열 너비를 고정한다.

WordPress 저장 시 일반 저자 권한에서는 kses가 인라인 스타일의 word-break, white-space를
지워 한글이 글자 단위로 쪼개진다("세 션", "묶/음"). 지워지지 않는 수단만 쓴다:
  - 라벨 열(첫 열, 또는 모든 셀이 짧은 열)의 <th>에 width/min-width(em)를 넣어 라벨이 한 줄에 들어가게 한다
  - 긴 라벨은 어절 경계에 <br>을 넣어 줄 길이를 맞춘다 (예: 특화 관리형<br>에이전트). 괄호 묶음은 "(" 앞에서 끊는다
  - <code>가 든 열은 건드리지 않는다

사용법:
  python3 table_ko_layout.py <wordpress.md> [--dry-run]
"""
import argparse
import itertools
import math
import re
import sys
import unicodedata

SINGLE_LINE_MAX = 7.0   # 이 폭(em) 이하 라벨은 줄바꿈하지 않는다
SHORT_COL_MAX = 7.0     # 첫 열이 아니어도 모든 셀이 이 폭 이하면 너비를 고정한다
PAD_EM = 1.2            # AWS 블로그 테마는 셀이 border-box(14px, 좌우 padding 8px)라 width에 padding이 포함된다


def text_width(s):
    """대략적인 표시 폭(em). 한글·전각 1, 공백 0.3, 그 외 ASCII 0.55"""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.3
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 1.0
        else:
            w += 0.55
    return w


def tokens(label):
    """(토큰, 앞에 공백 여부) 목록. 괄호 안 공백에서는 끊지 않고 "(" 앞에서 끊을 수 있다"""
    out, depth, cur, space_before = [], 0, "", False
    for ch in label:
        if ch == "(" and depth == 0 and cur:
            out.append((cur, space_before))
            cur, space_before = "", False
        if ch == " " and depth == 0:
            if cur:
                out.append((cur, space_before))
            cur, space_before = "", True
            continue
        depth += ch == "("
        depth -= ch == ")"
        cur += ch
    if cur:
        out.append((cur, space_before))
    return out


def join(toks):
    return "".join((" " if sp and i else "") + t for i, (t, sp) in enumerate(toks))


def splits(label, max_lines=3):
    """줄 목록 후보 전부"""
    toks = tokens(label)
    n = len(toks)
    yield [label]
    for k in range(1, max_lines):
        for cuts in itertools.combinations(range(1, n), k):
            bounds = (0,) + cuts + (n,)
            yield [join(toks[a:b]) for a, b in zip(bounds, bounds[1:])]


def best_split(label, limit=None, max_lines=3):
    """limit이 없으면 가장 고른 분할, 있으면 limit 안에서 줄 수가 가장 적고 앞줄을 최대한 채운 분할"""
    best = None
    for lines in splits(label, max_lines):
        widths = [text_width(l) for l in lines]
        if limit is not None and max(widths) > limit + 1e-9:
            continue
        key = (max(widths), len(lines), -widths[0]) if limit is None else (len(lines), [-w for w in widths])
        if best is None or key < best[0]:
            best = (key, lines)
    return best[1] if best else [label]


CELL_RE = re.compile(r"(<t[hd][^>]*>)(.*?)(</t[hd]>)", re.S)


def plain(html):
    return re.sub(r"<[^>]+>", "", html.replace("<br>", " ")).strip()


def set_width(open_tag, em):
    style = f"width: {em}em; min-width: {em}em;"
    open_tag = re.sub(r"\s*(min-)?width:\s*[\d.]+em;", "", open_tag)
    if 'style="' in open_tag:
        return open_tag.replace('style="', f'style="{style} ', 1)
    return open_tag[:-1] + f' style="{style}">'


def fix_table(table):
    rows = re.findall(r"<tr>.*?</tr>", table, re.S)
    grid = [CELL_RE.findall(r) for r in rows]
    ncol = max(len(r) for r in grid)
    changes = []
    new_grid = [list(r) for r in grid]
    for c in range(ncol):
        cells = [r[c] for r in grid if c < len(r)]
        if any("<code" in body for _, body, _ in cells):
            continue
        labels = [plain(body) for _, body, _ in cells]
        widths = [text_width(l) for l in labels]
        if c > 0 and max(widths) > SHORT_COL_MAX:
            continue
        # 열 폭 = 각 라벨을 두 줄로 가장 고르게 나눴을 때의 최대 줄 폭 (짧은 라벨은 통째로)
        need = max(
            w if w <= SINGLE_LINE_MAX else max(text_width(l) for l in best_split(lab, max_lines=2))
            for lab, w in zip(labels, widths)
        )
        limit = max(need, max(text_width(t) for lab in labels for t, _ in tokens(lab)))
        for ri, r in enumerate(new_grid):
            if c >= len(r):
                continue
            o, body, cl = r[c]
            lab = plain(body)
            manual = "<br>" in body and all(text_width(l.strip()) <= limit + 1e-9 for l in body.split("<br>"))
            if not manual and text_width(lab) > limit + 1e-9 and "<" not in body.replace("<br>", ""):
                lines = best_split(lab, limit)
                new_body = "<br>".join(lines)
                if new_body != body:
                    changes.append(f"{body!r} → {new_body!r}")
                    body = new_body
            if ri == 0:
                o = set_width(o, math.ceil((limit + 0.4 + PAD_EM) * 10) / 10)
            r[c] = (o, body, cl)
        changes.append(f"열 {c + 1} 너비 {math.ceil((limit + 0.4 + PAD_EM) * 10) / 10}em")
    out = table
    for old_row, cells in zip(rows, new_grid):
        it = iter(cells)
        new_row = CELL_RE.sub(lambda m: "".join(next(it)), old_row)
        out = out.replace(old_row, new_row, 1)
    return out, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    src = open(a.html, encoding="utf-8").read()
    out, n = src, 0
    for i, t in enumerate(re.findall(r"<table.*?</table>", src, re.S), 1):
        new, changes = fix_table(t)
        print(f"표 {i}: " + ("; ".join(changes) if changes else "변경 없음"))
        out = out.replace(t, new, 1)
        n += 1
    if not a.dry_run and out != src:
        open(a.html, "w", encoding="utf-8").write(out)
        print(f"{a.html} 저장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
