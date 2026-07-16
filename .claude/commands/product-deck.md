# /product-deck — Product Deck Generator

Read the project folder specified in $ARGUMENTS.
Read all deliverables, research, and status files for that project.

## Generate Product Deck
Save to: `01-Projects/Visual-Climate/05-Product-Decks/deck-{project-name}.md`

```yaml
---
project: {project}
type: product-deck
version: 1
date: YYYY-MM-DD
tags: [product-deck, {project}]
---
```

## Deck Structure (10-12 slides in Markdown)

### Slide 1: Title
- Project name + Harim's tagline
- Visual concept description

### Slide 2: The Problem
- 3 data points showing the pain (cite sources)
- Make it visceral — who is suffering and why

### Slide 3: Who Feels This
- Target audience profile with specifics
- Job titles, organizations, pain frequency

### Slide 4: Current Landscape
- What solutions exist today
- What's missing (the gap Harim fills)

### Slide 5: The Solution
- Harim's unique approach in one sentence
- 3 pillars/features

### Slide 6-8: How It Works
- Module/feature walkthrough
- Describe mockup/visual for each slide
- Show the user journey

### Slide 9: Case Study / Proof
- Sample output description
- Pilot result or testimonial
- Before/after comparison

### Slide 10: Why Harim
- Multilingual (KR/EN/FR/AR)
- UN system experience
- Data visualization + AI + domain expertise intersection
- Specific credentials relevant to this project

### Slide 11: Engagement Model
- Pricing tiers (discovery / standard / premium)
- Timeline expectations
- Deliverable list per tier

### Slide 12: Next Steps
- CTA (schedule a call, request a demo)
- Contact information

## Also Generate
- 1-page executive summary version (same file, appended at end)
- Key talking points (bullet list for verbal pitch)

$ARGUMENTS
