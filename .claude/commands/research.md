# /research — Research Agent

Read $ARGUMENTS for topic and scope.
Check `03-Resources/` and `06-Entities/concepts/` for existing knowledge.

## Execute

### 1. Search
Use web search to find latest information on the topic.
Cross-reference with existing vault knowledge.

### 2. Generate Research Brief
Save to: `01-Projects/{relevant-project}/04-Research/YYYY-MM-DD-{topic}.md`
(If broadly useful, also save to `03-Resources/{category}/`)

```yaml
---
date: YYYY-MM-DD
topic: {topic}
project: {project}
tags: [research, {topic-tags}]
---
```

#### Executive Summary
(5 lines max — the key takeaway)

#### Key Findings
1. {finding with source URL}
2. {finding with source URL}
3. ...

#### Data Points
(Quotable statistics, ready to use in presentations/content)
- {stat} — Source: {url}
- {stat} — Source: {url}

#### Implications for Harim's Projects
| Project | How This Is Relevant | Recommended Action |
|---------|---------------------|-------------------|

#### Competitive / Landscape Analysis
(If applicable — who else is doing this, what gaps exist)

#### Sources
1. {title} — {full URL}
2. {title} — {full URL}

### 3. Entity Updates
If new organizations or people were discovered:
- Create/update files in `06-Entities/`

### 4. Concept Notes
If a new concept was researched:
- Create `06-Entities/concepts/{concept}.md` with definition and context

$ARGUMENTS
