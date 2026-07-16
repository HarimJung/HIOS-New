# /today — Morning Brief

## Read (gather context from these sources)
1. All `_STATUS.md` and `_TODO.md` files in `01-Projects/` subdirectories
2. All tasks due within 7 days (scan YAML front-matter `due:` fields across vault)
3. Yesterday's daily note (most recent `YYYY-MM-DD.md` in vault root)
4. `00-Inbox/` for unprocessed items
5. `07-Queue/` for pending requests
6. Recent files in `05-AI/generated/` for overnight outputs
7. **Calendar**: Google Calendar MCP `list-events` if available; otherwise
   `curl -s http://127.0.0.1:8787/api/calendar` (HiOS dashboard reads macOS
   Calendar — no OAuth needed). If both fail, note "check calendar manually".
8. **Recent meetings**: meeting notes from the last 2 days in
   `01-Projects/*/02-Meetings/` (auto-synced from Granola every 2h).
   Notes with `status: filed` have NOT been deep-processed — flag them for /meeting.
9. **Email (Gmail MCP)**: `search_threads` with query `is:unread newer_than:2d`.
   Separate real/actionable mail (client threads, requests, deadlines) from
   newsletters/promos. Never auto-send anything; drafts only, and only if asked.
10. **UNFPA work email**: hajung@unfpa.org auto-forwards into this mailbox
    (enabled 2026-07-15). Run a second query `to:hajung@unfpa.org newer_than:2d`
    and treat every hit as work mail (never promo). List these FIRST in the
    "Needs Reply" section under a **[UNFPA]** prefix — UNFPA is HIGH priority.
    Replies must be sent from the UNFPA account, not the personal one — note
    "reply from hajung@unfpa.org" on any UNFPA item needing a response.
    Auto-label: apply the Gmail label `UNFPA` (label_id `Label_2`) via
    `label_thread` to every matching thread that doesn't have it yet. Also check
    `in:spam to:hajung@unfpa.org` — forwarded mail sometimes lands in spam;
    if found, flag it loudly in the brief.

## Auto-Process Before Generating
- Meetings are auto-filed by the Granola sync; do NOT re-classify them.
- Granola files still sitting in `00-Inbox/` mean auto-classification failed —
  mention them and point Harim to the dashboard filing card (one click to file).
- Extract action items and upcoming deadlines from the last 2 days of meeting
  notes and include them under relevant sections.

## Generate: Daily Note
Create `YYYY-MM-DD.md` in vault root with this structure:

```yaml
---
date: YYYY-MM-DD
type: daily-note
---
```

### Today's Schedule
(Use Google Calendar MCP `list-events` if available. Show all events with times,
calendar source, and attendees. If calendar not connected, note "check calendar manually.")

### Needs Reply (email)
(Actionable unread threads only: `{sender} — {subject}: {what they need}`.
UNFPA-addressed mail (`to:hajung@unfpa.org`) first with **[UNFPA]** prefix and
a "reply from hajung@unfpa.org" reminder where a response is needed.
Skip newsletters/promos entirely. If none, "No actionable email.")

### Recent Meetings (last 2 days)
(One line per meeting: `{date} {client} — {title}: {one-line takeaway} → [[link]]`.
Flag any not yet deep-processed: "→ /meeting 실행 권장". If none, omit section.)

### Must Do Today
(Due today or overdue items. Max 3. If more than 3, prioritize and note the rest.)

### This Week's Deadlines
(Due within 7 days, ordered by date)

### Project Status
| Project | Status | Next Action | Due |
|---------|--------|-------------|-----|
(One row per active project from CLAUDE.md project table)

### Inbox ({count} unprocessed)
(List unprocessed items in `00-Inbox/`. If empty, say "Inbox clear.")

### Queue ({count} pending)
(List items in `07-Queue/`. If empty, say "Queue clear.")

### Recommended Priority Order
Based on deadlines, client priority (from global CLAUDE.md), and dependencies,
recommend today's work order with brief reasoning for each item.
Format:
1. **{task}** — {why this first}
2. **{task}** — {reasoning}
3. **{task}** — {reasoning}

### Notes
(Empty section for Harim to fill during the day)

### Done
(Empty section — Harim logs completed items here throughout the day)

$ARGUMENTS
