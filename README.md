# ssminji skills

Claude Code 스킬 모음. 현재 포함된 플러그인:

| 플러그인 | 설명 |
|---|---|
| `blog-writing` | AWS 테크 블로그 원고 작성 워크플로우 — 톤 분석, 구성안 컨펌, 섹션별 작성, 공식 문서/실측 이중 검증, 공동 저자 협업 |
| `blog-review` | AWS 테크 블로그 원고 리뷰 워크플로우 — 6개 기준 셀프 게이트 채점(중복과 군더더기 측정 스크립트 포함), WordPress HTML 변환, 유사 블로그 비교 기반 내용 피드백, 게시 후 Slack 공지 문구 |

## 설치

Claude Code에서:

```
/plugin marketplace add ssMinji/skills
/plugin install blog-writing@ssminji
/plugin install blog-review@ssminji
```

## 사용

설치 후 "블로그 작성", "블로그 초안" 같은 요청에 자동으로 활성화되며, 직접 호출하려면:

```
/blog-writing
```

`blog-review`는 "블로그 리뷰", "워드프레스 변환", "슬랙 문구" 같은 요청에 활성화되며, 직접 호출은 `/blog-review`. 중복과 군더더기 측정 스크립트는 `python-docx`가 필요합니다(`pip install python-docx`).

같은 이름의 다른 스킬이 있어 충돌하는 경우에만 전체 형태 `/blog-writing:blog-writing`을 사용하세요.

## 업데이트

```
/plugin update blog-writing
/plugin update blog-review
```

이 저장소는 커밋 단위로 버전이 갱신되므로, update 시 항상 최신 내용을 받습니다.
