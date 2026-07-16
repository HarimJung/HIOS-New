# /collect — 콘텐츠 소스 자동 수집

Reddit + X에서 AI/투자 트렌드를 수집하고, 오늘의 콘텐츠 소스를 정리합니다.

## Step 1: 수집 실행
```bash
cd ~/Documents/Visual\ Climate\ Hermes/01-Projects/Visual-Climate/06-Content-Engine/scripts
python3 reddit_collector.py --sort hot --timeframe day --limit 15
python3 x_collector.py
```

## Step 2: 오늘 Digest 읽기
`06-Content-Engine/sources/` 에서 오늘 날짜의 digest 파일들을 읽습니다.

## Step 3: 콘텐츠 기회 분석
수집된 소스를 분석하여 다음을 출력:

### 🔥 오늘의 핫토픽 (Top 3)
각 토픽에 대해:
- 원본 소스 (Reddit/X 링크)
- 왜 핫한지 (engagement 수치)
- 콘텐츠 각도 제안 3가지:
  1. 샤오홍슈용 (중국어, 실용 팁)
  2. 인스타 캐러셀용 (영어, 교육적)
  3. YouTube 숏폼용 (한국어, 60초)

### 📊 트렌드 감지
- AI 분야 이번 주 키워드
- 투자 분야 이번 주 키워드
- 겹치는 주제 (AI + 투자 교차점)

### 📅 추천 제작 스케줄
- 오늘 바로 만들 것: [가장 시의성 높은 1개]
- 이번 주 만들 것: [트렌드 기반 2-3개]
- 에버그린 콘텐츠: [시간에 구애받지 않는 1개]

## Step 4: 콘텐츠 캘린더 업데이트
`_CONTENT-CALENDAR.md` 에 추천 콘텐츠를 추가합니다.

$ARGUMENTS
