# /meeting — Meeting Processor

Meetings are auto-synced from Granola every 2h (notes + todos land in
`01-Projects/{client}/02-Meetings/` automatically). This command does the
DEEP processing the auto-sync skips: entities, calendar, timeline, daily note.

## 0. Get the meeting
- If `$ARGUMENTS` names a meeting (title/date/id) or contains a pasted transcript, use that.
- Otherwise: use the **granola MCP tools** (`list_meetings` with time_range
  "this_week" AND "last_week", merged) to find recent meetings. Cross-check
  `granola_id` against files in `01-Projects/*/02-Meetings/` and `00-Inbox/`:
  - Meeting has NO note file yet → fetch with `get_meetings` and create one (step 1).
  - Note file exists but front-matter lacks `status: processed` → deep-process it (steps 2-5).
  - Everything processed → say so and stop.

## 1. Meeting Note (only if missing)
Create: `01-Projects/{client}/02-Meetings/YYYY-MM-DD-{client-lowercase}-{topic}.md`

```yaml
---
tags: [meeting, granola]
client: {client}
attendees: [list]
status: processed
source: granola
granola_id: {id}
date: YYYY-MM-DD
title: {title}
---
```

Sections: **Summary** (5 lines max), **Key Decisions**, **Discussion Points**,
**Action Items** table (Owner | Action | Due Date | Priority), **Transcript** (if available).

## 2. Action Items to Tasks
For each action item assigned to Harim:
- Append to the project's `_TODO.md` under `## Open` as
  `- [ ] {item} — from {date} 미팅` (skip if already there — the auto-sync may have added it).
- Check if a related task file already exists in the deliverable folder; if not,
  create a task note in the appropriate `01-Deliverables/` subfolder.
- Update `_STATUS.md` with new items.
- Update `_TIMELINE.md` if deadlines were mentioned (projects that have one).

## 3. Calendar Events
Identify scheduling mentions (next meetings, deadlines, travel).
If Google Calendar MCP is available, propose the events and create them on
confirmation. Otherwise format as a checklist Harim can confirm.

## 4. Entity Updates
Check `06-Entities/` for people/orgs mentioned:
- New person → `06-Entities/people/{name}.md` (role, org, professional contact only).
- Existing → append new info. Same for `06-Entities/organizations/`.

## 5. Daily Note
Append to today's daily note (`YYYY-MM-DD.md` in vault root):
```
## Meetings
- [HH:MM] {client} — {topic}: {one-line summary} → [[link to meeting note]]
```

## 6. Finalize
Set `status: processed` in the meeting note front-matter. Print:
- Notes path, action items extracted, calendar events identified,
  entity files created/updated, items needing Harim's clarification.

$ARGUMENTS
