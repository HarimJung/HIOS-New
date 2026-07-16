# /content — Multi-Platform Content Generator

Read `01-Projects/Visual-Climate/CLAUDE.md` for voice guide and brand rules.
Read `01-Projects/Visual-Climate/_BRAND-GUIDE.md` for tone and style.
Read `01-Projects/Visual-Climate/_CONTENT-CALENDAR.md` for scheduled topics.

Based on the topic provided, generate content for ALL platforms simultaneously.

## Input
$ARGUMENTS — the core topic/idea to turn into content.

## Output: Multi-Platform Content Package

### 1. YouTube Longform (10-20 min)
Save to: `01-Projects/Visual-Climate/01-YouTube/longform/scripts/YYYY-MM-DD-{title}.md`

Structure:
- **Hook** (first 30 seconds — the most important part)
- **Problem/Context** — why this matters
- **Segment 1-3** — main content with data points
- **CTA** — subscribe, comment prompt, next video teaser
- **Thumbnail concepts** — 3 options (text, visual layout, color scheme)

### 2. YouTube Shorts (3 scripts, 30-60s each)
Save to: `01-Projects/Visual-Climate/01-YouTube/shorts/YYYY-MM-DD-{title}-short{N}.md`

Each short must:
- Hook in first 3 seconds
- One clear insight per short
- End with curiosity gap or CTA

### 3. Xiaohongshu (3 posts, Chinese Simplified)
Save to: `01-Projects/Visual-Climate/02-Xiaohongshu/drafts/YYYY-MM-DD-{title}-xhs{N}.md`

Each post must:
- Be culturally adapted (NOT translated from Korean)
- Include relevant Chinese hashtags
- Describe visual layout (carousel slides or single image)
- Use friendly, practical Chinese tone with natural emojis

### 4. LinkedIn (1 post, English)
Save to: `01-Projects/Visual-Climate/04-Social/linkedin/YYYY-MM-DD-{title}.md`

Format:
- Strong opening line (hook)
- 3-5 short paragraphs with data-backed insights
- Professional but conversational tone
- End with question to drive engagement

### 5. Update Content Calendar
Append all generated content to `_CONTENT-CALENDAR.md` with status "Draft".

## Rules
- Each platform version should feel native to that platform.
- Never directly translate between platforms.
- All claims must be data-backed (cite sources).
- Follow voice guide strictly.
- Korean for YouTube, Chinese for Xiaohongshu, English for LinkedIn.

$ARGUMENTS
