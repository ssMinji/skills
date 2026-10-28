---
name: blog-review
description: AWS 테크 블로그 원고(docx/md)를 WordPress HTML로 변환하고 구조·내용 품질을 리뷰. "블로그 리뷰", "워드프레스 변환", "블로그 검토", "blog review", "publish 문구", "슬랙 문구" 요청 시 사용. 이미지/동영상/테이블 구조 점검 + 유사 블로그 비교 기반 내용 피드백 + 게시 후 Slack publish 문구 작성 포함.
---

# Blog Review — AWS 테크 블로그 WordPress 변환 & 품질 리뷰

원고(docx 또는 md)를 WordPress에 붙여넣을 수 있는 HTML로 변환하면서, 구조적 문제를 점검하고 내용 품질 피드백을 제공하는 워크플로우.

## 전체 흐름

0. **게이트 확인** — 작업 폴더에 `gate-report.md`가 있는지 확인. 없으면 `gate.md`의 6개 기준으로 먼저 채점해 리포트를 만든다 (중복과 군더더기는 이 스킬 폴더의 `scripts/redundancy_metrics.py` 실행). 리포트가 있으면 미달 항목과 "의도적으로 유지" 표시만 확인하고, 통과한 항목(오타·정합성·문체)은 다시 보지 않는다. 리뷰어의 몫은 기술적 정확성과 고객 관점이다
1. **원고 추출** — docx면 python-docx로 구조 추출 (pandoc 의존 없음, `pip install python-docx`)
2. **구조 변환 + 이미지 업로드** — 아래 WordPress 구조 체크리스트에 따라 HTML을 `wordpress.md`로 생성한 뒤, 같은 단계에서 `scripts/wp_upload_media.py <작업폴더> --channel tech` 로 `images/`를 WordPress 미디어 라이브러리에 올리고 `wordpress.md`의 이미지 경로를 CDN URL로 바로 치환한다 (아래 "이미지 업로드 자동화" 참고). 중간 파일을 두지 않고 `wordpress.md` 하나가 최종 붙여넣기본이다. 사용자가 수동 업로드를 원할 때만 생략
2-1. **특성 이미지** — 팀 헤드라인 템플릿(pptx)에 슬라이드를 추가해 PNG로 내보내고 같은 채널에 올린다 (아래 "특성 이미지 만들기" 참고)
2-2. **임시저장 글** — 제목, slug, 저자, 특성 이미지, 카테고리를 채워 WP 임시저장(draft) 글을 만들고 미리보기를 확인한 뒤 링크를 준다 (아래 "WordPress 임시저장 글 만들기" 참고)
3. **내용 리뷰** — 유사 주제 테크 블로그 검색·비교, 저자 피드백 작성
4. **산출물** — 아래 위치 규칙에 따라 저장 + 리뷰 내용을 코멘트 형식으로 정리 (아래 형식 참고)
5. **게시 후** — 사용자가 publish 완료를 알리면 Slack publish 문구 작성 (아래 워크플로우 참고)

## 산출물 위치 규칙

작업 폴더: 사용자에게 확인한다. 정해진 폴더가 없으면 `~/Documents/Work/Blog/`를 제안.

```
<작업 폴더>/<YYYY-MM-DD>-<블로그-타이틀>/
├── src/                  # 원본 원고(docx/md)를 mv로 이동 보관
├── wordpress.md          # 워드프레스 붙여넣기용 변환본
├── review.md             # 저자 전달용 코멘트
├── gate-report.md        # 셀프 게이트 채점 결과 (gate.md 참고)
└── images/               # 업로드용 이미지 (공백 없는 파일명, 01_ 접두사 번호)
    └── tables-reference/ # 표를 HTML로 재구성한 경우 원본 스크린샷 보관
```

- 폴더명: 오늘 날짜 + 블로그 타이틀 (공백은 `-`, 괄호 제거)
- 이미지 파일명: `01_<의미있는-이름>.png` 형식 — 공백·특수문자 금지 (macOS U+202F 문제 예방)

## docx 추출 방법

```python
import docx
d = docx.Document(path)
# 문단: p.style.name (Heading 1/2/3, Body Text, Compact=리스트, Source Code=코드블록)
# 이미지: p._element.findall('.//' + qn('a:blip')) → r:embed rel id → media 파일명
# 하이퍼링크: w:hyperlink 요소 — 본문 중간에 인라인으로 위치. 추출 시 위치가 어긋나기 쉬우므로
#   변환 시 반드시 문장 안에 자연스럽게 넣을 것 ("이 글에서는 와 을 활용해" 같은 빈자리 문장이 단서)
# 임베디드 이미지: zipfile로 word/media/* 추출
```

- docx의 bold run은 잘게 쪼개져 나옴 (`**단어****공백**` 연속) — 변환 시 병합·정리
- 이미지 alt/파일명에 `.mov`가 있으면 원본은 동영상 — 정지 이미지로 변환된 것. 원본 동영상 파일을 별도 요청할 것
- **협업 문서 도구에서 내보낸 docx는 다단(2열) 블록 안의 이미지가 빠질 수 있다.** 캡션("그림 N.")은 있는데 이미지 자리가 빈 1행 2열 표로 나오면, 원본 문서에서 이미지 파일을 받아 넣는다. 같은 그림 번호로 파일이 여러 개면 나중에 올린 것이 최신이므로 이미지를 열어 캡션과 내용이 맞는지 확인하고 고른다

## WordPress 구조 체크리스트 (실전 검증됨)

### 붙여넣기
- 반드시 **코드 편집기(HTML 모드)**에 붙여넣기 — 비주얼 모드는 태그가 글자로 보임
- 문서 제목(h1)과 부제는 본문에 넣지 않음 — WP 제목 필드 사용. 본문은 `<h2>`부터 시작

### hr (구분선)
- 테마가 `<hr>`을 가운데 정렬된 짧은 선으로 렌더링함 (깨진 게 아니라 테마 디자인)
- h2 제목이 섹션을 구분해 주므로 **hr은 전부 제거** 권장

### 이미지
- **base64 데이터 URI 금지** — 미디어 라이브러리에 업로드 후 URL 참조
- 업로드는 아래 "이미지 업로드 자동화" 스크립트로 처리 가능. 수동 업로드 시에만 사용자에게 URL을 받아 치환
- `src`에 `-300xNNN`(medium) 등 축소본 접미사가 있으면 **원본 크기로 표시할 때 화질 깨짐** — 접미사 없는 원본 URL 사용, `width`/`height` 속성으로 표시 크기 지정 (원본이 표시 크기보다 커야 선명)
- 이미지 삽입 시 크기는 "Full Size" 선택 권장
- macOS 스크린샷 파일명의 특수 공백 **U+202F** (`10.15.27 PM` 형태) 주의 — URL 인코딩은 `%E2%80%AF`, `%20` 아님. 업로드 전 파일명에서 공백/특수문자 제거 권장
- URL 검증: `curl -sI <url>`로 200 확인, `sips -g pixelWidth`로 원본 크기 확인

### 동영상
- `<a href="...mov">`는 텍스트 링크로만 보임 — 인라인 재생은 `<video>` 태그 필요:
  ```html
  <video src="URL.mov" controls playsinline preload="metadata" width="642" style="max-width: 100%; height: auto;"></video>
  ```
- 코덱 확인 필수: `ffprobe -select_streams v:0 -show_entries stream=codec_name <file>` — H.264면 Safari/Chrome/Edge 재생 OK. HEVC(macOS 최신 화면녹화 기본)면 Chrome 미재생 → mp4(H.264) 재인코딩
- Firefox는 .mov 컨테이너를 거부할 수 있음 — 완전한 호환은 mp4 변환: `ffmpeg -i in.mov -c copy out.mp4` (H.264면 무손실 컨테이너 변환)

### 테이블
- **표를 스크린샷 이미지로 넣지 말 것** — 검색 불가, 접근성 저하, 확대 시 흐림, 수정 불가. docx에서 표가 이미지로 굳어 왔으면 이미지 내용을 읽어 실제 HTML 표로 재구성
- 테마 기본 테이블은 테두리가 회색이거나 없음 — 검은 테두리는 인라인 스타일 필수. 표 스타일 규칙:
  - 표는 **중앙 정렬** + 하단 여백 8px (`margin: 0 auto 8px auto;`) — 테마 기본 table 하단 마진이 커서 캡션과 벌어지는 문제 방지
  - 헤더 행은 `<thead>` + `<th>`로 분리하고 **연회색 배경** `background-color: #f2f3f3;` 적용
  - 열이 적어 좁아 보이는 표는 `width: 70%` 등으로 너비 지정
  - **WordPress에 저장하면 인라인 스타일의 `word-break`·`white-space`가 사라진다** (`unfiltered_html` 권한이 있어도 지워지고 `width`·`min-width`·`<br>`은 남는다). 그래서 한글 라벨이 "묶/음"처럼 글자 단위로 갈리지 않게 하는 데는 이 둘에 기대지 않는다. 테마 표 셀은 `box-sizing: border-box`, 14px, 좌우 padding 8px라서 `width`에 padding 16px(약 1.2em)가 포함된다. 변환 후 `scripts/table_ko_layout.py wordpress.md`를 실행한다
    - 첫 열(그리고 모든 셀이 7자 이하인 열)의 `<th>`에 `width`/`min-width`(em)를 넣어 짧은 라벨이 한 줄에 들어가게 한다
    - 7자를 넘는 라벨은 어절 경계에 `<br>`을 넣어 최대 2줄로 나누고 앞줄을 채운다 ("특화 관리형<br>에이전트"). 괄호 묶음은 "(" 앞에서 끊는다. 결과를 보고 의미 단위가 갈라진 곳은 손으로 고친다
    - 열이 많은 표(8열 이상)는 숫자 열 머리글도 두 줄로 나누고("요청당<br>처리 시간") `min-width`를 줘야 "150 ms"·"0.49 GB" 같은 값이 줄바꿈되지 않는다
  - 셀 안의 `<code>`는 `style="word-break: break-all;"`을 붙인다. 긴 식별자 하나가 열 전체를 넓혀 옆 열이 글자 단위로 쪼개지는 것을 막는다
  - 변환 후 로컬 미리보기로 표를 확인한다: `word-break`·`white-space`를 지운 사본을 `python3 -m http.server`로 띄워 본문 폭 760px에서 열 너비와 한글 끊김을 잰다. 가장 확실한 검증은 실제 초안 미리보기(`/<채널>/?p=<id>&preview=true`)에서 JS로 재는 것
  ```html
  <table style="border-collapse: collapse; border: 1px solid #000; margin: 0 auto 8px auto;">
  <th style="border: 1px solid #000; padding: 8px; background-color: #f2f3f3;">
  <td style="border: 1px solid #000; padding: 8px;">
  ```
- 표/그림 캡션은 표 바로 아래 **가운데 정렬**로 붙임: `<p style="text-align: center; margin-top: 0;"><em>표 N. ...</em></p>`

### 코드/기타
- 코드 블록은 `<pre><code class="lang-bash">…</code></pre>` 형식으로 언어 클래스를 붙인다 (lang-bash, lang-json, lang-python, lang-javascript, lang-text 등. 테마가 이 클래스로 구문 강조). 인라인 코드는 `<code>`. 본문의 환경 변수, 설정 이름, 오류 이름, CLI 명령도 `<code>`로 감싼다
- 링크는 문장 안에 인라인으로 (docx 추출 시 위치 어긋남 주의)
- 리스트는 `<ul><li>`

## 이미지 업로드 자동화

AWS 블로그 WordPress는 REST API가 열려 있고 Midway 쿠키만으로 쓰기까지 된다 (nonce 불필요, 2026-10-16 /tech/ 채널에서 업로드 확인).

- 엔드포인트: `https://aws-blogs-prod.amazon.com/<채널>/wp-json/wp/v2/media` (POST, `Content-Type: image/png`, `Content-Disposition: attachment; filename="..."`)
- 채널 path: 한국 기술 블로그 `tech` (aws.amazon.com/ko/blogs/tech, blog_id 65), 한국 블로그 `korea` (blog_id 12). CDN URL의 해시는 blog_id의 SHA1이라 채널별 고정 (tech = `2a459380…`)
- 인증: `mwinit -o` 후 `~/.midway/cookie`. 401이면 사용자에게 mwinit 실행을 요청
- 실행: `python3 -I scripts/wp_upload_media.py <작업폴더> --channel tech [--html wordpress.md] [--dry-run]`
  - `images/upload_map.json`에 파일별 id, URL, 크기 기록. 재실행 시 기록된 파일은 건너뜀
  - 치환 결과는 `--html` 파일에 바로 쓴다 (기본 `wordpress.md`). 미치환 src가 남으면 출력에 표시
- 프로덕션 쓰기이므로 실행 전 `--dry-run`으로 대상 목록을 사용자에게 보여주고 확인받는다. 저자 사진 등 본문에 안 쓰는 파일은 `images/` 밖으로 빼 둔다
- 잘못 올린 파일 삭제: `DELETE .../wp/v2/media/<id>?force=true`
- 같은 달에 같은 파일명으로 올리면 WP가 `-1`을 붙인다 (`01_architecture-1.png`). 동작에는 문제없지만 파일명 앞에 글 식별자를 붙이면 헷갈리지 않는다

## WordPress 임시저장 글 만들기

이미지와 특성 이미지를 올린 뒤 같은 REST API로 임시저장(draft) 글까지 만든다. 사용자는 미리보기를 확인만 하면 된다. **`status`는 항상 `draft`** — 게시(publish)나 검토 대기(pending)로 바꾸지 않는다.

- 실행: `python3 -I scripts/wp_draft.py <작업폴더>/draft.json [--post-id <id>]`. `draft.json`의 `content_file`(보통 `wordpress.md`)을 본문으로 넣어 `POST /<채널>/wp-json/wp/v2/posts`(수정은 `/posts/<id>`)로 보내고, `status`가 draft가 아니면 거부한다
  ```json
  {"channel":"tech","title":"…","slug":"my-post-slug","status":"draft","author":12345,"featured_media":67890,"categories":[13,263],"content_file":"wordpress.md"}
  ```
- 필드 값 정하기
  - `title`: 블로그 요청 티켓이나 원고의 제목. "2부 : " 같은 띄어쓰기는 "2부: "로 정리하고 사용자에게 알린다
  - `slug`: 요청 티켓의 Permalink 마지막 경로. 응답의 `target_link`가 게시 URL이다
  - `author`: `GET /wp/v2/users?search=<별칭>`으로 저자 WP 사용자 ID를 찾는다 (`context=edit`를 붙이면 403, 기본 context는 된다)
  - `featured_media`: 특성 이미지의 미디어 ID (`images/upload_map.json`)
  - `categories`: 원고 바이라인("in [Advanced (300)](…/category/learning-levels/advanced-300/), …")의 카테고리 링크 slug로 `GET /wp/v2/categories?slug=<slug>`를 조회해 ID 목록을 만든다. Uncategorized는 넣지 않는다. 학습 레벨이 요청 티켓과 바이라인에서 다르면 사용자에게 알린다
- **공동 저자는 REST로 넣을 수 없다.** 글 응답에 `authors`(ID 배열)·`contributors` 필드가 보이지만 `authors: [A, B]`를 보내도 `author` 한 명만 남는다. 공동 저자 글은 초안 생성 후 편집 화면에서 추가하도록 안내한다
- **저자가 WP 계정이 있으면 본문에 저자 소개를 넣지 않는다.** 테마가 WP 사용자 프로필(사진 포함)로 `blog-author-box`를 본문 아래에 자동으로 붙여서, 본문에도 넣으면 두 번 나온다. 고객사 저자처럼 WP 계정이 없는 사람만 본문에 `blog-author-box`로 넣는다
- 같은 글의 초안이 이미 있는지 먼저 `GET /posts?search=<키워드>&status=draft,pending,publish,future&context=edit`로 확인하고, 다른 사람이 만든 초안은 묻지 않고 덮어쓰지 않는다
- 저장 후 `GET /posts/<id>?context=edit`의 `content.raw`를 보낸 HTML과 비교한다. `word-break`·`white-space` 제거와 style 공백 정리 외에 차이가 없어야 한다
- 미리보기 `https://aws-blogs-prod.amazon.com/<채널>/?p=<id>&preview=true`를 브라우저로 열어 확인한다: 이미지는 lazy loading이라 스크롤 후 `naturalWidth`로 로드 여부를 보고, 표 열 너비와 한글 끊김, `blog-author-box` 개수(1개), 카테고리를 확인한다

## 특성 이미지 만들기

WP 특성 이미지(featured image)는 팀 헤드라인 템플릿(pptx)의 슬라이드를 PNG로 뽑아 올린다. 템플릿 경로는 사용자에게 확인한다.

1. **슬라이드 추가** — 템플릿을 백업한 뒤 기존 슬라이드 하나를 복제해 맨 끝에 추가하고 제목 `<a:t>`만 바꾼다 (zip 안의 XML 직접 편집). 추가할 때 `ppt/slides/slideN.xml`과 `_rels/slideN.xml.rels`, `[Content_Types].xml`의 Override, `ppt/_rels/presentation.xml.rels`의 새 rId, `ppt/presentation.xml`의 `<p:sldId>`(최댓값+1)를 함께 넣고, 모든 XML이 파싱되는지 확인한 뒤 원본을 교체한다
2. **줄바꿈** — 렌더링해 보고 단어가 줄 끝에서 갈리면("오/리진") `<a:br>`로 줄을 직접 나눈다
3. **렌더링** — PowerPoint로 한다. LibreOffice는 템플릿 폰트를 다른 글꼴로 바꿔 기존 이미지와 모양이 달라질 수 있다. macOS PowerPoint는 샌드박스라 컨테이너 경로에 **HFS 경로 문자열**로 PDF를 저장해야 파일이 생긴다 (POSIX file을 그대로 넘기거나 `save as PNG`는 오류 없이 아무 파일도 만들지 않는다)
   ```bash
   C=~/Library/Containers/com.microsoft.Powerpoint/Data/Documents/headline-export; mkdir -p "$C"
   osascript <<EOF
   set outPath to (POSIX file "$C/deck.pdf") as string
   tell application "Microsoft PowerPoint"
     open POSIX file "<템플릿.pptx 절대 경로>"
     delay 3
     save active presentation in outPath as save as PDF
     delay 5
     close active presentation saving no
   end tell
   EOF
   pdftoppm -png -scale-to-x 2000 -scale-to-y 1125 -f <N> -l <N> "$C/deck.pdf" headline
   ```
   이미지를 열어 기존 슬라이드와 폰트·배치가 같은지 비교한다. 끝나면 컨테이너의 `headline-export` 폴더를 지운다
4. **업로드** — `images/00_featured_headline.png`로 두고 `wp_upload_media.py`를 다시 실행한다 (본문에서 참조하지 않으므로 치환 0건이 정상). 미디어 ID를 임시저장 글의 `featured_media`에 넣는다

## 내용 리뷰 체크리스트

1. **유사 블로그 비교** — WebSearch로 같은 주제의 AWS 공식 블로그/벤더 블로그 검색. 차별점이 분명한지, 이미 공식 기능/문서로 나온 걸 놓쳤는지 확인 (예: 관련 서비스의 신기능 릴리스)
2. **그림/표 번호 순서** — 캡션의 "그림 N"이 본문 등장 순서와 일치하는지
3. **수치 일관성** — 본문 서술 수치 vs 표/차트 수치, 퍼센트 계산 재검증
   - **심볼·식별자 일관성도 동일하게** — 본문 서술에 등장하는 메서드/클래스/변수 이름이 해당 문단의 예시 코드·실행 결과와 일치하는지 대조 (실제 누락 사례: isEmpty 예시를 설명하다 마지막 문장에서 isBlank로 잘못 씀)
   - **문장 호응** — 주어-서술어, 목적어-동사 호응이 어긋난 비문 점검 (실제 누락 사례: "좌표를 줄 뿐 길을 주지 못합니다" → "길을 알려주지 못합니다")
4. **코드 스니펫** — 모델 ID·API 파라미터가 실제와 맞는지 (Claude/Bedrock 관련이면 공식 API 문서로 모델 ID와 파라미터명 검증), 실행 흐름에 논리 오류 없는지
   - 코드 예시 스타일이 문서 전체에서 통일됐는지 (bash CLI vs JSON 조각 혼재 금지)
   - 예시 도메인은 RFC 2606 계열(`*.example.com`), 환경변수·출력에 시크릿/계정 ID 노출 여부
   - 코드 블록 언어 라벨이 내용과 일치하는지 (실제 사례: Python 코드에 javascript 라벨)
5. **링크 유효성** — 본문 링크 curl로 200 확인
6. **구조 완결성** — 도입(문제 제기) → 본론 → 실전 → 정리 흐름, 다음 글 예고와 CTA 존재 여부
7. **AWS 블로그 관례** — 비용 안내, 리소스 정리(clean-up) 섹션, 서비스 정식 명칭(Amazon/AWS 접두사) 사용 여부
8. **용어 3층위 검증** — 신기능을 다룰 때 ①공식 발표 기능명(What's New) ②문서 페이지명 ③API 파라미터명을 구분해 썼는지, 출시 시점은 What's New 게시일로 확인 (실제 사례: 기능명은 "VPC egress", API 블록은 `privateEndpoint` — 혼용 시 독자 혼란)
9. **한국어 표기** — AWS 공식 한국어 문서 용어 우선 (실제 사례: "공인 인증서"✗ → ACM 공식 용어 "퍼블릭 인증서"✓), 영어 직역 번역투 제거 ("신뢰 앵커", "~에 예외를 두지 않습니다"), 첫 등장 "한국어(English)" 병기 후 이후 영문 통일
10. **표기 통일** — 컴포넌트 축약 표기 vs 풀네임 일관성 (예: Runtime vs AgentCore Runtime — 전수 검색으로 확인). 슬래시(A/B)를 풀 때: 어느 쪽이든→"이나/또는", 둘 다→"와/및", 나열→쉼표. 유사 명칭 리소스와 혼동 금지 (예: AgentCore Gateway ≠ Lattice Resource Gateway ≠ Internet Gateway — 이들은 치환 대상 아님)
11. **상호참조 정합** — 본문에서 섹션 번호 하드참조("앞서 6.2에서") 금지, 내용 지칭으로 ("앞서 VPC 모드로 배포한"). 아키텍처 흐름 번호를 참조하는 문장은 참조 라벨과 흐름 목록의 실제 항목이 일치하는지 대조 (실제 사례: "6번(토큰 검증)"이라 썼는데 목록 6번은 "도구 조회")
12. **공동 편집 유입 오류** — 협업 도구(Notion 등)에 붙여넣은 원고는 다음 패턴을 전수 점검: 문장 중복, 수정 전 구버전 문장 잔존, 문단이 불릿 안에 병합, URL이 `<https://...>` 꺾쇠로 감싸짐(마크다운 자동링크 잔재 — 코드 블록이면 복사 시 오류 유발), 이전 과정에서 생긴 새 오타

## 피드백 작성 원칙

- 구조적 문제(변환 시 직접 수정)와 내용 피드백(저자 판단 필요)을 구분해 제시
- 내용 피드백은 근거(비교한 블로그 URL, 재계산 수치)와 함께
- 심각도 구분: 게시 전 필수 수정 / 권장 / 선택

### 코멘트 형식 (저자 전달용)

내용 피드백은 저자에게 그대로 전달할 수 있는 코멘트 형식으로 정리한다. 원문 문장을 인용(`>`)하고 수정안을 제시:

```
> (원문 문장 그대로 인용)

위 문장을 아래로 수정 부탁드립니다.
"(수정된 문장)"
— 이유: (한 줄 근거)
```

- 코멘트 단위는 문장/문단 하나씩, 원고 등장 순서대로
- 직접 수정한 구조적 변경(이미지, 표, 링크 위치 등)은 코멘트가 아니라 별도 "변환 시 수정 사항" 목록으로 요약

## Slack publish 문구 작성

게시 완료 후 사내 Slack 채널에 올릴 공지 문구를 작성하는 워크플로우. "publish 문구", "슬랙 문구" 요청 시 사용.

### 흐름 (반드시 이 순서로)

1. **원고 파악** — 작업 폴더에서 해당 블로그의 `wordpress.md`를 읽고 핵심 내용(문제 제기 → 접근법 → 실전 사례) 파악
2. **필수 정보 질문** — 문구 작성 전에 먼저 사용자에게 묻는다 (플레이스홀더로 초안을 먼저 만들지 말 것):
   - 작성자 정보: 팀명/직함, 성함, Slack 핸들 (예: OO팀 Sr. SA 길동님(@gildong)). 공동 작성자 있으면 모두
   - 게시된 블로그 URL
3. **full text 전달** — 답변을 받으면 정보가 모두 채워진 완성본을 한 번에 전달. 플레이스홀더 없이 바로 복사-붙여넣기 가능한 상태여야 함

### 문구 구조 (2문단)

1. 인사 + 작성자 소개(팀/직함, 성함(@핸들) — 공동 저자는 "~과 ~께서 함께 작성하신") + 블로그 제목(게시 URL 링크) + "이 게시되었습니다."
2. 요약·추천·감사를 한 문단으로: 문제의식+접근법 한 문장 → 실전 내용과 추천 대상을 잇는 마무리 문장 → "OO님, OO님 좋은 글 포스팅 감사드립니다! `:tada:`"

전체 분량은 3~4문장으로 짧게. 길게 나열하지 말 것.

마무리 문장은 같은 채널에 반복 게시되므로 한 패턴("~한 고객에게 바로 공유하기 좋은 글입니다")으로 굳히지 말고 글의 차별점에 맞춰 아래 유형을 돌아가며 쓴다:

1. 고객 미팅 근거 자료형: "~를 검토하는 고객 미팅에서 근거 자료로 쓰기 좋습니다"
2. 문서 공백 보완형: "공식 문서가 답하지 않는 ~를 실측으로 채워주셔서 검증 시간을 줄여주는 글입니다"
3. 문의 대응형: "~문의를 받았을 때 이 글 하나로 답변이 정리될 만큼 흐름이 명확합니다"
4. 타깃 고객 구체화형: "~가 필수인 OO 업종 고객과의 대화에서 든든한 레퍼런스가 될 글입니다"
5. 독자 질문 응답형: "'문서에는 없는데 실제로는?'이라는 질문에 수치로 답해주는 글입니다"

#### 확정 예시 (이 톤 그대로)

> 안녕하세요! OO팀 Sr. SA 길동님(@gildong)과 AI Specialist SA 철수님(@chulsoo)께서 함께 작성하신 블로그 AI Agent를 위한 OpenSearch 검색 품질 평가하기 (Part 1) 이 게시되었습니다.
> RAG Agent의 답변 품질은 검색이 상한을 정하는데도 이를 숫자로 재는 팀은 드물다는 문제의식에서, OpenSearch와 Bedrock으로 검색 품질 정량 평가 시스템을 만든 경험을 다룹니다. LLM Judge를 사람 정답과 교차 검증하는 과정과 BM25·시멘틱·하이브리드 비교에서 만난 함정들을 실측 수치로 담아주셔서 RAG 검색 품질을 고민하는 고객에게 바로 공유하기 좋은 글입니다. 길동님, 철수님 좋은 글 포스팅 감사드립니다! :tada:
