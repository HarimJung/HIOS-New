---
type: dashboard
updated: 2026-07-08
tags: [dashboard, hios]
---

# HiOS Dashboard

## Active Projects

| Project | Client | Priority | Status | Next Milestone |
|---------|--------|----------|--------|---------------|
| [[01-Projects/UNFPA-CSE/_STATUS\|UNFPA-CSE]] | UNFPA | HIGH | Active | Jul 31: Reporting platform |
| [[01-Projects/Equitee/_STATUS\|Equitee]] | Equitee | MED | Awaiting kickoff | TBD |
| [[01-Projects/Climate-AICA/_STATUS\|Climate-AICA]] | AICA | MED | Framing | Module 1 scope |
| [[01-Projects/Visual-Climate/_CONTENT-CALENDAR\|Visual Climate]] | Personal | STEADY | Ongoing | First YouTube longform |

## Quick Links
- [[CLAUDE|System Prompt]]
- [[00-Inbox/|Inbox]]
- [[07-Queue/|Queue]]
- [[02-Areas/finance/revenue-tracker|Revenue Tracker]]

## Upcoming Deadlines
- **Jul 31** — UNFPA Reporting Platform
- **Sep 22-24** — Nairobi Meeting (UNFPA)
- **Oct 2026** — UNFPA Contract End

## This Week's Focus
(Updated by /today command — see latest daily note)

---

## Dataview Queries (for Obsidian)

### Overdue Tasks
```dataview
TASK
WHERE due < date(today) AND !completed
SORT due ASC
```

### Recent Meeting Notes
```dataview
TABLE date, client, tags
FROM "01-Projects" AND #meeting
SORT date DESC
LIMIT 10
```

### Unprocessed Inbox
```dataview
LIST
FROM "00-Inbox"
SORT file.ctime DESC
```
