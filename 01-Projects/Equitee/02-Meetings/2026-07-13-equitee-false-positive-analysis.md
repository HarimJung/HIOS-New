---
tags: [meeting, granola]
client: Equitee
status: processed
source: granola
granola_id: abc014f6-f7a6-4a78-9116-a1119b62d0e2
date: 2026-07-13
title: False Positive
---

# False Positive Detection

**Date:** Jul 13, 2026 10:00 AM EDT
**Participants:** Harim Jung

## Summary

### False Positive Detection: Current Status

- Extracted 1,000+ records; data and table now available in SQL Server for analysis
- Corner extracted all PDFs; history loaded into a chronic response table per speaker
- ~100+ alerts manually reviewed; 20-30% flagged manually (especially closed investigations)
- AI-generated flags also in place: two-flag system (comment-based + AI)
- 10 flag categories defined; AI-categorized from comments, so not 100% accurate
  - Standard definitions documented in a shared link for consistency between Corner and Harim

### Data Quality Issues

- Policy date accuracy: cancellation dates sometimes off by more than a month
- Duplicate periods exist in the history; combined to avoid interfering with decisions
- Coverage information not available in the current database
  - Only triggered claim coverage is retained, not original policy coverage
  - Limits ability to determine whether a claim should have been covered
- More accurate data may eventually be needed from Dash or IP Stat

### False Positive Patterns Found

- One confirmed pattern: before/after insurance from the same insurer, policy still active
  - CVSA information flagged as completely incorrect in these cases
- Export false positive example: coverage exported but policy still active at same company
- Next step: review cases where response variable is already marked as false positive, then identify patterns
- Goal: build an algorithm to identify false positives; gray areas expected

### Investigator Engagement Strategy

- No current scenario for detecting false positives; pattern research is the first step
- Suggested approach: mark target cases in the access sheet, note questions for investigators
  - Identify insurers/members tied to those cases; find relevant contacts
  - Internal team mainly uses network alerts; claim/policy alerts better suited to external investigators (e.g., TDI, Intact super users)
- Check with Dominique on who is actively using EQ Insights
- Acceptance working group feedback on scenarios can be shared
- Intact likely has the most cases; Aviva expected to have fewer false positives

### Next Steps

- **Summarize first findings and share by email** — capture early false positive patterns and insights
- **Build a target case list with investigator questions** — mark cases in access sheet, member/insurer breakdown
- **Talk to Angel about investigator engagement** — have target list and member split ready first
- **Create a dimension/categorization table for false positive flag types** — clarity for the 10 AI-generated categories
