---
client: Equitee
updated: 2026-07-20
tags: [equitee, status]
---

# Equitee — Status Tracker

## Status: Active — insurance fraud & vehicle crime analytics

| Workstream | Status | Next Step |
|---|---|---|
| False-positive detection | **9월 초기 결과 커밋** (Viva 미팅: Julia + VP of Fraud Crime, FP 비율 우려) — 471개 알림 개별 리뷰 중, 근본원인 2종 확인 (CBSA/CP 데이터 레거시, 비즈니스 룰 갭). 스코프는 CBS/CP 데이터로 한정 | 패턴 category/subcategory 재구성 (Claude Code, 이번 주) → 2주 내 케이스 리뷰 완료·분류 결과 공유 → 내부 정렬 후 Julia 싱크 → Jackie(Desjardins 슈퍼유저) 인터뷰. Findings email + target case list (**draft ready 7/16** → review & send) → Angel |
| Fraud dashboard migration (Tableau → Power BI) | **ESCALATED 7/18** — stakeholder pressure; Harim driving directly (Genspark-assisted, mock data only) | Completion plan: `2026-07-18-pbi-fraud-dashboard-completion-plan.md` — gap list → funnel & score page → reconcile → embed |
| CGI gold report extraction | Working; known data quality issue (insured period dates unreliable) | Re-check code against this week's PDF update |
| Auto trend & value reports | Submitted for Kevin/Jung review | Await feedback |
| Fraud scoring model (Shift) | Threshold 0.1, low F1 (~1,400 training samples) | Follow-up meetings incl. Harim; model tuning planned this quarter |

## Context from 7/15 working group
- June alert volume 1,780 (≈4x May's 481); 4 new scenarios contributed 1,245 alerts
- This quarter: prior-damage detection improvements, high-interest claim scenario,
  third-party vehicle alert removal, **new triage step** for low-qualification alerts
- Entity resolution improvements NOT planned this quarter (examples → existing tickets)
- Member survey on working-session cadence coming (David) — respond when it arrives

## Blockers / pending asks
- IB status data — Yulia (re-requested multiple times)
- PC/노트북 업그레이드 — Julia 승인 대기 (AI 모델 로컬 실행 속도에 필요, 7/20 기준 pending)
- EQ Insights active-user list — Dominique
- Dash API agreement — Angel/Burim (longer-term)

## Recent Updates
- 2026-07-20: **AI False Positive 미팅** — Viva 미팅(Julia + VP of Fraud Crime)에서 FP 비율 우려 제기, 9월 초기 결과 커밋. 471개 알림 개별 리뷰 진행, 근본원인 2종(CBSA/CP 데이터 레거시 vs 비즈니스 룰 갭). 패턴을 category/subcategory 구조로 재편(Claude Code 전환) 예정, 2주 내 케이스 리뷰 완료 목표. 스코프 크립 경계 — CBSA/CP 데이터 신뢰성 이슈 우선. 이후 순서: 내부 정렬 → Julia 싱크 → Jackie(Desjardins) 인터뷰. master table의 기존 FP 플래그에 신규 컬럼 추가 방식. PC 업그레이드 Julia 승인 대기
- 2026-07-20: 이메일 스캔 — Equitee 관련 신규 항목 없음 (뉴스레터만). David의 워킹세션 주기 설문 아직 미수신
- 2026-07-19: _ACTIONS.json에 7/13 false-positive 미팅 액션 7건 자동 등록 — 모두 기존 오픈 항목과 중복 (신규 할 일 없음)
- 2026-07-18: **PBI fraud 대시보드 에스컬레이션** — 이해관계자 불만; 완성 플랜 + Genspark 보안 게이트 문서화 (`2026-07-18-pbi-fraud-dashboard-completion-plan.md`)
- 2026-07-16: findings email + target case list structure drafted (`03-Communications/`)
- 2026-07-15: working group meeting (alert volume spike, triage step announced)
- 2026-07-13: false-positive meeting — 1 confirmed pattern; scope corrected (old "DEI Dashboard / Awaiting Kickoff" description removed)
- 2026-07-08: project folder created
