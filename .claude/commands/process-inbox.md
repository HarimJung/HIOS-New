# /process-inbox — Inbox Auto-Processor

Scan `00-Inbox/` for unprocessed files and route each to the correct project.

## Step 1: Scan
List all files in `00-Inbox/` (excluding `granola-exports/` subdirectory files
that have already been processed). Check each file's content.

## Step 2: Classify
For each file, determine the project by scanning content for keywords:

**UNFPA-CSE** indicators:
- "UNFPA", "CSE", "comprehensive sexuality education", "Wafa", "Steve Petite"
- "sexuality education", "country mapping", "baseline", "signal detection"
- "reporting platform", "landing page"

**Equitee** indicators:
- "Equitée", "Equitee", "DEI", "diversity equity inclusion"
- "inclusion", "equity dashboard"

**Climate-AICA** indicators:
- "AICA", "climate literacy", "misconception detector", "data narrator"
- "COP", "climate data", "SIDS", "climate negotiat"

**Visual Climate** indicators:
- "YouTube", "소홍슈", "Xiaohongshu", "content", "thumbnail"
- "newsletter", "brand", "subscriber"

**Unclassified**: If no clear match, flag for manual classification.

## Step 3: Process Each File

### If meeting transcript/notes:
1. Create meeting note in `01-Projects/{project}/02-Meetings/YYYY-MM-DD-{topic}.md`
2. Extract action items → update `01-Projects/{project}/_STATUS.md`
3. Extract deadlines → update `01-Projects/{project}/_TIMELINE.md`
4. Extract people → create/update `06-Entities/people/` files
5. Append summary to today's daily note

### If email:
1. Extract action items and deadlines
2. Update relevant project's `_STATUS.md`
3. If contains a request, create entry in `07-Queue/`

### If idea/note:
1. Create note in appropriate project folder or `03-Resources/`
2. Add to daily note under "Ideas"

## Step 4: Archive
Move processed files to `04-Archive/inbox-processed/YYYY-MM-DD-{filename}`

## Step 5: Report
Print summary:
- Files processed: {count}
- By project: {project: count}
- Action items created: {count}
- Entities updated: {count}
- Unclassified (needs manual review): {list}

$ARGUMENTS
