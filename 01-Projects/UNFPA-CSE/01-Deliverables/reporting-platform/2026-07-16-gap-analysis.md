---
tags: [unfpa, reporting-platform, deliverable, gap-analysis]
client: UNFPA-CSE
status: draft
due: 2026-07-31
priority: HIGH
created: 2026-07-16
---

# Reporting Platform — Gap Analysis & Improvement Proposal (Draft v0.1)

> Written **without script access** (Wafa handoff requested 7/14, no reply as of 7/16).
> Sections marked ⏳ require the clasp export to finalize.
> **Fallback trigger (per kickoff plan): access was due by Jul 16.** If no access by
> EOD Jul 17, pivot this document to "current tool documentation + improvement
> roadmap" — explicitly allowed by contract ("existing acceptable if no time").
> **Action today: send Wafa a short follow-up ping on the 7/14 email.**

## 1. Contract requirements, decomposed

Contract: *"improve existing Google Script tool: quarterly/annual, work-plan
submission, approval workflow, real-time finance"*

| # | Requirement | Working interpretation | Acceptance signal |
|---|---|---|---|
| R1 | Quarterly/annual reporting | Country offices submit structured quarterly + annual progress reports; HQ sees consolidated view | A CO can submit a Q3 report in <15 min; HQ views aggregate without manual copy-paste |
| R2 | Work-plan submission | Annual work-plan intake with structured fields (activities, budget lines, timelines) | Work plan enters the same data model as reports (comparable fields) |
| R3 | Approval workflow | HQ review → approve / return-with-comments cycle, visible status per submission | Submitter and approver both see current status without emailing each other |
| R4 | Real-time finance | Budget vs. expenditure visible per CO/activity without manual refresh | Finance view updates when source data updates (no monthly manual paste) |

## 2. Current-state hypotheses (verify against source ⏳)

Based on 7/8 onboarding and typical Apps Script reporting tools:

- **H1**: Google Form (or Sheet template) intake → single Sheet as database, `onFormSubmit` trigger.
- **H2**: No status machine for approvals — approval likely happens over email outside the tool.
- **H3**: Finance data manually pasted from another system (Quantum/Atlas exports?) — not live.
- **H4**: Quota/failure risks: 6-min execution limit, MailApp daily quota, no error logging.
- **H5**: No role separation (any editor can change anything).

Each hypothesis maps to a checklist item in `2026-07-13-review-kickoff.md` §A.

## 3. Gap matrix (working — fill "Exists today?" after export ⏳)

| Requirement | Exists today? | Likely gap (hypothesis) | Fix size |
|---|---|---|---|
| R1 Quarterly/annual | ⏳ | Annual cycle may be missing or a separate form; no consolidation view | S–M |
| R2 Work-plan submission | ⏳ | Probably not structured — free-form docs | M |
| R3 Approval workflow | ⏳ | Likely absent (email-based) — highest-value gap | M |
| R4 Real-time finance | ⏳ | Almost certainly manual — depends on finance data source access | M–L |

## 4. Improvement options (scope to Jul 31 — config-driven, stay in Google Workspace)

**Option A — Minimal hardening (fits Jul 31 even with late access)**
Status column + protected ranges for approvals; email notifications on submit/approve;
error logging. No new surfaces. *Risk: low. Value: medium.*

**Option B — Approval workflow + consolidated dashboard (recommended if access lands by Jul 18)**
A + a status-driven approval flow (submitted → under review → approved/returned) and
a Looker Studio (or Sheets pivot) consolidation view for R1/R4. *Risk: medium. Value: high.*

**Option C — Rebuild intake as web app**
Out of scope for Jul 31. Park as post-extension roadmap item.

Tradeoff note for Wafa: B delivers R3 (probable biggest pain) + visible R1/R4 progress;
A is the guaranteed-delivery floor.

## 5. Questions for Wafa (validate scope — must land before Jul 25 OOO)

1. Which of R1–R4 hurts most today? (ranking = scope priority)
2. Where does finance data come from, and can we get a scheduled export? (R4 feasibility)
3. Who are the approvers (HQ only, or regional)? (R3 design)
4. Country office feedback on the current tool — top 3 complaints? (already in handoff list)
5. Confirm: is Option A/B framing acceptable as the Jul 31 deliverable + progress report?

## 6. Resource map — where every input comes from

| Input | Source | How to get it | Status |
|---|---|---|---|
| Script source code | UNFPA Google Workspace | Wafa → editor access → `clasp clone` → `src/` snapshot | ⏳ requested 7/14 — **ping today** |
| Underlying Sheets/Forms | Same container | Same access grant | ⏳ |
| Country office feedback | Wafa | In 7/14 handoff email | ⏳ |
| Finance data structure | Wafa / UNFPA finance system export | Q2 in §5 | ⏳ not yet asked |
| Approver list & roles | Wafa | Q3 in §5 | ⏳ not yet asked |
| Contract requirement text | Local: `UNFPA-CSE/CLAUDE.md` + kickoff doc | Done | ✅ |
| Progress report template (payment trigger) | Draft alongside Option A/B | Self | To draft Jul 19+ |

## 7. Plan (updated from kickoff)

- **Jul 16**: this draft + Wafa follow-up ping (access + §5 questions)
- **Jul 17–18**: on access → clasp export → verify H1–H5 → finalize gap matrix → send Option A/B to Wafa
- **No access by EOD Jul 17** → fallback: finalize this doc as roadmap deliverable + document tool from user-side behavior (screenshots/CO feedback)
- **Jul 19–28**: implement chosen option
- **Jul 29–31**: test, progress report (1–2 pages), handover

## Log
- 2026-07-16 12:01 [메모] HiOS 캘린더 시스템 v1 가동 — 이 파일은 이제 캘린더 아이템으로 추적됨 (메모/AI 요청 가능)
