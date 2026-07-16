# /start — HiOS 엔진 시작

이 커맨드는 하루를 시작할 때 실행합니다. 모든 것을 한 번에 처리합니다.

## Step 1: Inbox 처리
`00-Inbox/` 에 파일이 있으면 먼저 처리합니다.

각 파일의 내용을 읽고:
- 미팅 트랜스크립트 → 프로젝트별 `02-Meetings/`에 분류
- 액션아이템 추출 → `_STATUS.md` 갱신
- 마감일 추출 → `_TIMELINE.md` 갱신
- 새 인물/조직 → `06-Entities/` 갱신
- 처리 완료된 파일 → `04-Archive/inbox-processed/`로 이동

처리 결과를 간단히 보고:
"Inbox: {N}건 처리 — UNFPA {n}건, Equitee {n}건, ..."

## Step 2: 프로젝트 스캔
모든 `01-Projects/*/_ STATUS.md` 읽기.
오버듀, 이번 주 마감, 블로커를 정리.

## Step 3: 캘린더 확인
Google Calendar MCP가 연결되어 있으면 `list-events`로 오늘 + 3일 일정 조회.
없으면 "캘린더 수동 확인" 표시.

## Step 4: Daily Note 생성
`YYYY-MM-DD.md` 생성 (오늘 날짜):

```
### 오늘 일정
(캘린더 이벤트)

### 반드시 할 것 (최대 3개)
(오버듀 + 오늘 마감)

### 이번 주 마감
(7일 이내)

### 프로젝트 현황
| Project | Status | Next Action | Due |
(한 줄씩)

### 오늘의 우선순위
1. {왜 이것부터}
2. {이유}
3. {이유}
```

## Step 5: 한 줄 요약
마지막에 한 줄로 출력:
"오늘 핵심: {가장 중요한 한 가지}. Inbox {N}건 처리됨. 마감 {N}건."

$ARGUMENTS
