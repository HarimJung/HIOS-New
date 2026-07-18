---
tags: [equitee, power-bi, dashboard, plan]
client: Equitee
status: active
due: 2026-07-25
priority: high
---

# Power BI Fraud Dashboard — Completion Plan (ESCALATED)

> 2026-07-18: 이해관계자 측에서 대시보드 미완성에 대한 강한 불만 제기.
> Harim이 직접 진행하기로 함. 툴링: Genspark 기반으로 진행 예정 (아래 ⚠️ 보안 게이트 필수 확인).

## ⚠️ Genspark 사용 전 보안 게이트 — 먼저 읽을 것

클라이언트 정책 (7/9 미팅에서 재확인됨): **"do not upload any proprietary data or IP
to any LLM."** Genspark는 외부 LLM 서비스임. 게다가 Claude Code 서명 모듈 건도
아직 Ivan/Yulia에게 공식 통보 전 상태 — 이 시점에 새 외부 AI 툴에 실데이터가
들어가면 문제가 커짐.

**허용되는 Genspark 사용 (기존 Claude 사용 원칙과 동일):**
- 레이아웃/디자인 목업, 페이지 구성 아이디어
- DAX measure / Power Query M 코드 초안 생성 (스키마 이름만, 실데이터 없이)
- Faker 목데이터 기반 시각화 프로토타이핑

**금지:**
- 실데이터가 포함된 PBIX, CSV, 스크린샷 업로드
- 실제 알림/케이스/멤버·보험사 식별 정보 붙여넣기
- Genspark가 생성한 미검증 외부 모듈/스크립트를 검토 없이 실행 (서명 모듈 건 재발 방지)

## 현재 상태 (7/9 미팅 기준)

- Tableau → Power BI 마이그레이션 진행 중, 예상보다 지연
- 데이터 모델링을 처음부터 재구축함 (decomposition 필요했음)
- Tableau 추출은 라이브 데이터소스로 완료, 웹앱 임베드 가능 상태
- Power BI 시각화가 Tableau 대비 제약 있음 → 최대한 유사하게 매칭 중
- 잔여 핵심: **funnel & score 페이지 1개 추가 (NTD 피드백 기반)**

## 완성 정의 (Definition of Done)

- [ ] 기존 Tableau 페이지 전체가 PBI에서 시각적으로 동등 수준으로 재현됨
- [ ] Funnel & score 페이지 추가 완료 (NTD 피드백 반영 확인)
- [ ] 데이터 모델: 리프레시 정상 동작 + 수치가 Tableau 원본과 대사(reconcile)됨
- [ ] 웹앱 임베드 (내부/외부 공유) 동작 확인
- [ ] 성능: 주요 페이지 로드/인터랙션 체감 지연 없음
- [ ] 이해관계자(NTD 피드백 제공자 포함) 대상 리뷰 1회 통과

## 실행 순서

1. **잔여 갭 목록화** — Tableau 원본 vs 현재 PBI 페이지 나란히 비교, 미완 항목
   체크리스트화 (오늘)
2. **Funnel & score 페이지** — NTD 피드백 원문 재확인 → 목업(Genspark 활용 가능,
   목데이터만) → PBI 구현
3. **수치 대사** — 핵심 KPI 3~5개를 Tableau/PBI 양쪽에서 비교, 불일치 원인 해소
   (로컬 작업, LLM 미사용)
4. **임베드 + 권한 확인** — 웹앱 임베드 경로, 내부/외부 접근 구분
5. **미리보기 공유** — 완성 전이라도 진행 상황 스크린샷/링크를 먼저 공유해서
   "안 되고 있다" 인식부터 차단 (목데이터 화면 사용)

## 리스크 / 판단 필요

- **Tableau 시각화 제약**: 100% 동일 재현은 불가 — "최대한 유사" 기준을
  이해관계자와 명시적으로 합의해두지 않으면 완성 후에도 불만 재발 가능.
- **CGI 날짜 신뢰성 이슈**: 대시보드가 insured period 날짜를 쓰는 페이지가 있다면
  알려진 데이터 품질 이슈(기간 중복)를 대시보드 각주로 명시할 것.
- **Genspark 계정/플랜**: 회사 정책상 승인된 툴인지 불명 — Ivan 보안 통보 메일에
  Genspark 사용 계획을 한 줄 포함시키는 것을 권장 (선제 투명성).

## 연결 문서

- [[02-Meetings/2026-07-09-equitee-cgi-data-quality]] — PBI 마이그레이션 현황, 보안 정책
- `_ACTIONS.json` → `eq-pbi-funnel` (high로 상향, 2026-07-18)
