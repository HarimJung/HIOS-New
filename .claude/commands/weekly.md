# /weekly — Weekly Review

Read all data from this week and generate a comprehensive weekly review.

## Data Sources
1. All daily notes from this week (`YYYY-MM-DD.md` in vault root)
2. All `_STATUS.md` files in `01-Projects/`
3. All meeting notes created this week (`01-Projects/*/02-Meetings/`)
4. Content calendar (`01-Projects/Visual-Climate/_CONTENT-CALENDAR.md`)
5. Finance entries in `02-Areas/finance/`
6. Any files in `05-AI/generated/` from this week

## Generate: Weekly Review
Save to `05-AI/summaries/YYYY-WXX-weekly-review.md`

```yaml
---
type: weekly-review
week: YYYY-WXX
date: YYYY-MM-DD
tags: [weekly-review]
---
```

### Week Summary
(3-5 sentence narrative of the week)

### Project Progress
| Project | Start of Week | End of Week | Key Movement |
|---------|--------------|-------------|--------------|
(one row per project, showing status change)

### Completed This Week
(bulleted list of everything marked DONE in daily notes)

### Meetings Held
| Date | Client | Topic | Key Outcome |
|------|--------|-------|-------------|

### Action Items Status
| Item | Project | Status | Due | Notes |
|------|---------|--------|-----|-------|
(all action items: new, in-progress, completed, overdue)

### Content Published
| Platform | Title | Performance | Notes |
|----------|-------|-------------|-------|

### Financial Summary
- Revenue received this week:
- Invoices pending:
- Expenses:

### Blockers & Risks
(anything stalled, overdue, or at risk — with recommended action)

### Next Week Priorities
1. **{task}** — {why, which project}
2. **{task}** — {why}
3. **{task}** — {why}

### Reflection
- What went well:
- What didn't:
- What to adjust:

$ARGUMENTS
