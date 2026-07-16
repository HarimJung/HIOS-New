---
tags: [equitee, false-positive, communications, draft]
client: Equitee
status: draft
priority: HIGH
created: 2026-07-16
---

# False Positive Findings — Email Draft (v1)

> **DRAFT — do not send as-is.** Harim: confirm recipients, verify numbers against
> local SQL Server data, and attach/link the flag-definitions doc before sending.
> No real case data in this file (data security rule) — placeholders in [brackets].
> Timing note: 7/15 working group announced a **new triage step + model tuning this
> quarter to reduce false positives** — this analysis feeds directly into that.
> Worth referencing to frame the work as on-agenda.

**To**: [confirm — Corner + Yulia? David? working-group lead?]
**Subject**: False positive analysis — first confirmed patterns & proposed next steps

---

Hi [names],

Following the analysis work on the extracted records (1,000+ in SQL Server, 100+
alerts manually reviewed), here is a summary of first findings on false positives.

**Confirmed pattern #1 — same-insurer before/after coverage**
Cases where before/after insurance is with the **same insurer and the policy is
still active** are consistently false positives. In these cases the CVSA
information is flagged as completely incorrect. [N cases — verify count locally]

**Related pattern (export alerts)**
Coverage marked as exported while the policy is still active at the same company —
same underlying signature. [N cases]

**Data caveats that limit certainty**
- Policy cancellation dates can be off by more than a month; duplicate periods
  were merged before analysis.
- Original policy coverage is not retained (only triggered claim coverage), so we
  cannot always determine whether a claim should have been covered. More reliable
  dates may eventually require Dash or IB status data (IB request still pending
  with Yulia).

**Proposed next steps**
1. Review all cases where the response variable is already marked false positive
   and extract further patterns (in progress).
2. Dimension table for the 10 AI-generated flag categories, aligned with the
   shared definitions doc — for consistency between Corner and me.
3. Target case list for investigator engagement (see attached structure):
   cases marked in the access sheet with questions per case and a member/insurer
   breakdown — prerequisite for the conversation with Angel. Given volume
   distribution, Intact likely provides most cases; Aviva expected to have fewer
   false positives.

Given the working group's plan to add a triage step this quarter, these patterns
could feed directly into the triage logic. Happy to walk through the cases —
[suggest slot / today's Daily EQ].

Best,
Harim

---

## Target Case List — structure (build locally in the access sheet; NO data here)

| Column | Content | Source |
|---|---|---|
| Case / Alert ID | identifier | SQL Server table (local) |
| Scenario | triggering scenario | alert record |
| Flag category (1–10) | AI category + manual check | comments + shared definitions doc |
| Pattern matched | e.g. same-insurer before/after | this analysis |
| FP confidence | high / gray area | analyst judgment |
| Insurer / Member | for distribution + contact routing | alert record |
| Investigator question | what we need them to confirm | drafted per case |
| Suggested contact | e.g. TDI / Intact super users for claim/policy alerts | Dominique (EQ Insights active-user check) |
| Status | to-review / sent / answered | tracking |

**Selection criteria**: start with response-variable-confirmed FPs; over-sample
Intact (volume), include a few Aviva for contrast; claim/policy alerts → external
investigators, network alerts → internal team.

## Resource map

| Input | Where it comes from | Status |
|---|---|---|
| Extracted records + flags | SQL Server (local only — never upload) | ✅ available |
| Flag category definitions | Shared link (Corner/Harim standard defs doc) | ✅ available |
| Access sheet | Equitee shared access sheet — mark target cases there | ✅ available |
| EQ Insights active users | **Dominique — ask (pending)** | ⏳ |
| IB status data | **Yulia — re-request (pending, multiple asks)** | ⏳ |
| More reliable dates | Dash (API agreement: Angel/Burim) | Later |
| Investigator engagement go-ahead | Angel — after this list is ready | Next |
