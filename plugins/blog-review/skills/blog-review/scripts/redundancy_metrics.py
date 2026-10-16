#!/usr/bin/env python3
"""블로그 원고의 중복과 군더더기 정량 지표 측정.

사용법: python3 -I redundancy_metrics.py <원고.docx|.md|.txt>
출력: 마크다운 점수표 (stdout). 점수는 0~100, 높을수록 읽기에 방해되는 요소가 적음.

측정 대상은 독자가 읽는 데 방해되는 요소만이다. AI가 썼는지 여부를 판별하지 않는다.
(구호형 불릿, 섹션 구조 동형성, 문장 길이 분산, 과거형 비율은 가독성과 무관해 측정하지 않는다)
"""
import re, sys, collections, pathlib

def load_blocks(path):
    """(kind, text) 목록. kind: h1/h2/h3/h4/p/li/code"""
    p = pathlib.Path(path)
    blocks = []
    if p.suffix.lower() == ".docx":
        import docx
        d = docx.Document(str(p))
        for para in d.paragraphs:
            t = para.text.strip()
            if not t:
                continue
            s = para.style.name.lower()
            if s.startswith("heading"):
                m = re.search(r"\d", s)
                kind = "h" + (m.group(0) if m else "2")
            elif "code" in s or "source" in s:
                kind = "code"
            elif "list" in s or "compact" in s:
                kind = "li"
            else:
                kind = "p"
            blocks.append((kind, t))
        return blocks
    text = p.read_text(encoding="utf-8")
    in_code = False
    for line in text.splitlines():
        st = line.strip()
        if st.startswith("```"):
            in_code = not in_code
            continue
        if st.startswith("<pre"):
            in_code = True
        if in_code:
            if "</pre>" in line:
                in_code = False
            blocks.append(("code", line))
            continue
        t = re.sub(r"<[^>]+>", "", line).strip()
        if not t:
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", t)
        if m:
            blocks.append(("h%d" % len(m.group(1)), m.group(2)))
        elif re.match(r"^([-*]|\d+\.)\s+", t):
            blocks.append(("li", re.sub(r"^([-*]|\d+\.)\s+", "", t)))
        else:
            blocks.append(("p", t))
    return blocks

def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[다요까])[.?!]\s+|(?<=[.?!])\s+(?=[가-힣A-Z])", text) if len(s.strip()) > 3]

def main(path):
    blocks = load_blocks(path)
    prose = [(k, t) for k, t in blocks if k != "code"]
    prose_text = "\n".join(t for _, t in prose)
    n_chars = max(len(prose_text), 1)
    sents = [s for _, t in prose for s in sentences(t)]

    rows, penalty, samples = [], 0, []

    # 1. 보일러플레이트 문단 반복 (같은 안내 문장이 섹션마다 등장)
    norm_p = collections.Counter(t for k, t in prose if k in ("p", "h4") and len(t) >= 10)
    boiler = {k for k, c in norm_p.items() if c > 1}
    dup_para = sum(c - 1 for c in norm_p.values() if c > 1)
    pen = min(20, dup_para * 6)
    rows.append(("보일러플레이트 문단 반복", f"{dup_para}회", "0", pen)); penalty += pen
    samples += [("보일러플레이트", k) for k in boiler]

    # 2. 문장 반복 (보일러플레이트로 이미 센 것은 제외. 토씨만 다른 재진술도 한글 공통 구절 20자로 잡음)
    cand = [re.sub(r"\s+", " ", s) for s in sents if len(s) >= 15 and re.sub(r"\s+", " ", s) not in boiler]
    norm = collections.Counter(cand)
    exact = sum(c - 1 for c in norm.values() if c > 1)
    uniq = list(norm.keys())
    # 서비스명 같은 고유명사 반복은 제외: 공통 구절은 한글 12자 이상 포함해야 함
    def hangul_grams(u, n=20):
        return {u[i:i+n] for i in range(len(u) - n + 1) if len(re.findall(r"[가-힣]", u[i:i+n])) >= 12}
    grams = [hangul_grams(u) for u in uniq]
    near = []
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            shared = grams[i] & grams[j]
            if shared:
                near.append((uniq[i], uniq[j], max(shared, key=len)))
    dup_sent = exact + len(near)
    pen = min(25, dup_sent * 8)
    rows.append(("문장 반복 (동일 또는 한글 공통 구절 20자)", f"동일 {exact}, 유사 {len(near)}", "0", pen)); penalty += pen
    samples += [("반복 문장", k) for k, c in norm.items() if c > 1]
    samples += [("유사 문장", f"'{g}' ← {a[:25]}… / {b[:25]}…") for a, b, g in near]

    # 3. 메타 강조 문장 ("핵심입니다" 류. 중요하다고 말하는 대신 내용으로 보여 줘야 함)
    meta = [s for s in sents if re.search(r"핵심|중요한 점은|주목할|요컨대|결론적으로|바로 이것|이 한 문장", s)]
    pen = min(15, max(0, len(meta) - 1) * 5)
    rows.append(("메타 강조 문장", f"{len(meta)}회", "≤ 1", pen)); penalty += pen
    samples += [("메타 문장", m) for m in meta]

    # 4. 따옴표 조어 밀도 (일반 명사구를 따옴표로 감싸 개념어처럼 쓰는 것. 읽기 흐름을 끊음)
    quotes = re.findall(r"[\"“]([^\"”]{2,40})[\"”]", prose_text)
    coined = [q for q in quotes if not re.search(r"[A-Za-z_]{3,}|\d", q)]
    dens = len(coined) / n_chars * 1000
    pen = min(12, int(max(0, dens - 1.0) * 5))
    rows.append(("따옴표 조어 밀도 (1000자당)", f"{dens:.1f} ({len(coined)}회)", "≤ 1.0", pen)); penalty += pen
    samples += [("따옴표 조어", q) for q in coined]

    # 5. 긴 문단 (한 문단 6문장 이상)
    long_paras = [t for k, t in prose if k == "p" and len(sentences(t)) >= 6]
    pen = min(15, len(long_paras) * 5)
    rows.append(("6문장 이상 문단", f"{len(long_paras)}개", "0", pen)); penalty += pen
    samples += [("긴 문단", t[:50] + "…") for t in long_paras]

    # 6. 군더더기 표현 (뜻 없이 붙는 상투어)
    filler_re = r"다양한|효과적으로|효율적으로|원활하게|적절한|적절히|성공적으로|쉽게|간단히|보다 나은|더욱|매우|상당히"
    fillers = re.findall(filler_re, prose_text)
    f_dens = len(fillers) / n_chars * 1000
    pen = min(13, int(max(0, f_dens - 1.5) * 4))
    rows.append(("상투어 밀도 (1000자당)", f"{f_dens:.1f} ({len(fillers)}회)", "≤ 1.5", pen)); penalty += pen
    if fillers: samples.append(("상투어", ", ".join(f"{w}×{c}" for w, c in collections.Counter(fillers).most_common(6))))

    score = max(0, 100 - penalty)
    print(f"## 중복과 군더더기 지표: {pathlib.Path(path).name}\n")
    print(f"**점수: {score}/100** (높을수록 읽기에 방해되는 요소가 적음, 최저선 60)\n")
    print("| 지표 | 측정값 | 기준 | 감점 |\n|---|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} | -{r[3]} |")
    print("\n### 근거 샘플")
    by = collections.defaultdict(list)
    for k, v in samples: by[k].append(v)
    for k, vs in by.items():
        print(f"- {k}: " + "; ".join(v[:45] for v in vs[:8]))
    print("\n같은 뜻을 다른 문장으로 되풀이하는 재진술은 스크립트가 잡지 못한다. 채점자가 섹션별 핵심 메시지를 한 줄씩 적어 보고 겹치는 것을 세어 이 점수에 반영한다 (재진술 1건당 -5).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
