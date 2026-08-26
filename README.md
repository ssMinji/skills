# ssminji skills

Claude Code 스킬 모음. 현재 포함된 플러그인:

| 플러그인 | 설명 |
|---|---|
| `blog-writing` | AWS 테크 블로그 원고 작성 워크플로우 — 톤 분석, 구성안 컨펌, 섹션별 작성, 공식 문서/실측 이중 검증, 공동 저자 협업 |

## 설치

Claude Code에서:

```
/plugin marketplace add ssMinji/skills
/plugin install blog-writing@ssminji
```

## 사용

설치 후 "블로그 작성", "블로그 초안" 같은 요청에 자동으로 활성화되며, 직접 호출하려면:

```
/blog-writing:blog-writing
```

## 업데이트

```
/plugin update blog-writing
```

이 저장소는 커밋 단위로 버전이 갱신되므로, update 시 항상 최신 내용을 받습니다.
