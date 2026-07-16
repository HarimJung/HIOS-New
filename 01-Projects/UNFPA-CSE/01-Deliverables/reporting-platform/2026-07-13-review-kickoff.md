---
tags: [unfpa, reporting-platform, deliverable]
client: UNFPA-CSE
status: in-progress
due: 2026-07-31
priority: HIGH
created: 2026-07-13
---

# Reporting Platform — Review Kickoff

> Contract requirement: "improve existing Google Script tool: quarterly/annual,
> work-plan submission, approval workflow, real-time finance"
> Deadline: **Jul 31** (contract note: existing tool acceptable if no time)

## Blocker #1 — Script access (resolve first, today/tomorrow)

The existing Google Apps Script lives in UNFPA's Google Workspace. Nothing is
stored locally. Before any review can happen:

- [ ] Ask Wafa for **editor access** to the Apps Script project (or the
  container-bound Sheet/Form it's attached to)
- [ ] Once access granted, export source locally:
  `npm i -g @google/clasp && clasp login && clasp clone <scriptId>`
  → commit snapshot to `01-Deliverables/reporting-platform/src/`
- [ ] Identify: standalone script vs container-bound (affects deployment)

## Review checklist (once source is in hand)

### A. Current-state audit
- [ ] Map entry points: menus, triggers (time-based / onEdit / onFormSubmit), web app endpoints
- [ ] Data model: which Sheets/ranges are the source of truth
- [ ] Users & roles today: who submits, who approves, who reads
- [ ] Quotas & failure points: execution time limits, email quotas, error handling

### B. Gap analysis vs contract requirements
| Requirement | Exists today? | Gap |
|---|---|---|
| Quarterly/annual reporting | ? | |
| Work-plan submission | ? | |
| Approval workflow | ? | |
| Real-time finance view | ? | |

### C. Improvement design (scope to Jul 31 — keep minimal)
- Must stay in Google Workspace (contract rule)
- Prefer config-driven changes over rewrites (deadline risk)
- Deliverable payment trigger: 1–2 page progress report → draft alongside

## Realistic plan to Jul 31
1. **Jul 14–15**: get script access (Wafa), clasp export, current-state audit
2. **Jul 16–18**: gap analysis + improvement proposal (validate scope with Wafa — she's reachable until ~Jul 25)
3. **Jul 19–28**: implement highest-value fixes
4. **Jul 29–31**: test with real data, write progress report, hand over

## Risks
- Wafa OOO Jul 27–Aug 2 → any approval/questions must land **before Jul 25**
- If access is delayed past Jul 16, invoke fallback: document existing tool +
  improvement roadmap (contract allows "existing acceptable if no time")
