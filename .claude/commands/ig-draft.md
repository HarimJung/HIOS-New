# /ig-draft — Instagram 캐러셀 초안 생성

주어진 주제를 Instagram 캐러셀 포스트로 변환합니다.

## 소스 확인
`01-Projects/Visual-Climate/06-Content-Engine/sources/` 에서 오늘 digest 확인.

## 캐러셀 구조 (7-10 슬라이드)

### 슬라이드 1: Hook
- 굵은 텍스트, 질문 또는 도발적 문장
- 예: "AI is replacing $400B worth of jobs. Here's how to be on the right side."

### 슬라이드 2: Problem/Context
- 왜 이게 중요한지
- 데이터 포인트 1개

### 슬라이드 3-7: Content
- 한 슬라이드 = 한 포인트
- 짧은 문장 (3줄 이내)
- 아이콘/숫자로 시각화

### 슬라이드 8-9: Summary/Framework
- 핵심 정리
- 기억할 프레임워크

### 슬라이드 10: CTA
- Follow for more
- Save this post
- Share with someone who needs this

## 언어
- **영어** 기본 (글로벌 리치)
- 투자/AI 니치에서 영어가 도달률 훨씬 높음

## 캡션 규칙
- 첫 줄: Hook (피드에서 보이는 부분)
- 2-3 문단: 추가 컨텍스트
- CTA: "Save this for later" / "Which one surprised you?"
- 해시태그 20-25개 (첫 댓글에 넣어도 됨)

## 카테고리별 톤
- **AI:** Educational, "Here's what most people miss..."
- **Investing:** Data-driven, "The numbers don't lie..."
- **Productivity:** Framework, "The 3-step system for..."

## 금융 콘텐츠 주의사항
- "Not financial advice" 캡션 포함
- 교육적 프레이밍만
- 구체적 종목 추천 금지

## 출력 형식
```markdown
---
platform: instagram
format: carousel
date: YYYY-MM-DD
topic: [주제]
source: [reddit/x/original]
status: draft
tags: [instagram, investing, AI]
---

# [캐러셀 제목]

## Slide 1 — Hook
**[텍스트]**
Visual: [배경/레이아웃 설명]

## Slide 2 — Context
**[텍스트]**
Visual: [설명]

...

## Caption
[캡션 텍스트]

## Hashtags
#ai #investing #... (20-25개)

## 제작 노트
- Color palette: [제안]
- Font: [제안]
- Style reference: [참고할 계정/스타일]
```

## 저장 위치
`01-Projects/Visual-Climate/04-Social/instagram/YYYY-MM-DD-{slug}.md`

한 번에 2개 캐러셀을 생성합니다 (AI 1개, 투자 1개).

$ARGUMENTS
