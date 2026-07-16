---
tags: [climate, aica, application, module1]
client: AICA
status: draft
priority: MED
created: 2026-07-16
---

# Module 1 — Misconception Detector: Scope & Data Sources (Framing v1)

> Unblocks the AICA application (stalled since 07-09). This is the framing draft;
> once Harim validates scope, this becomes the Module 1 section of the application.

## Problem statement

Climate data is abundant but routinely misread. Negotiators, researchers, and SIDS
government staff (core AICA users) work with charts and statistics they did not
produce — and 31% of researchers already face data access barriers before
interpretation even starts. Module 1 targets the interpretation layer: an AI tool
that detects *data-literacy* misconceptions in a claim or chart reading, explains
the error, and links the authoritative correction.

**Positioning note**: this is NOT a generic climate-denial debunker (crowded space
— Skeptical Science etc. already do this). The differentiator is **data-literacy
misconceptions** — how people misread legitimate data — aimed at professional
users in the Discover → Understand step of the AICA pipeline.

## Scope v1 (application MVP)

**In scope**
- Input: a text claim or a user's interpretation of a dataset/chart
- Detection: classify against a curated taxonomy of climate *data* misconceptions
- Output: (1) misconception class, (2) plain-language correction, (3) linked
  authoritative source, (4) "what the data actually supports" restatement

**Out of scope v1 (roadmap for v2+)**
- Chart/image parsing (v2)
- Multilingual (FR/AR — natural fit for Harim, v2)
- Real-time social media monitoring
- COP-specific negotiation texts (that's Module 5's bridge)

## Misconception taxonomy — seed (10 classes, data-literacy specific)

1. Weather vs. climate — single events cited as trend evidence
2. Baseline/anomaly confusion — misreading anomaly charts as absolute values
3. Cherry-picked timeframes — e.g. 1998 start-point trends
4. Model projections read as predictions — scenario vs. forecast
5. Uncertainty ranges misread — "scientists aren't sure" from confidence intervals
6. Global vs. regional averages conflated
7. Per-capita vs. absolute emissions conflated
8. CO2 vs. CO2e vs. short-lived pollutants mixed up
9. Correlation presented as attribution — vs. formal attribution science
10. Scale/unit errors — mm vs. m sea level, °C anomaly vs. absolute temperature

## Data sources — where to get them

| Source | What it provides | Access | License/note |
|---|---|---|---|
| Skeptical Science rebuttal database | 200+ rebutted claims, structured by taxonomy | skepticalscience.com | CC — verify reuse terms |
| FLICC taxonomy (John Cook) | Denial-technique classification framework | Published papers + crankyuncle materials | Academic citation |
| CARDS corpus (Coan et al. 2021) | ML-labeled contrarian-claim dataset (training/eval) | GitHub (verify current repo) | Academic |
| Climate Feedback / Science Feedback | Expert-annotated claim reviews | climatefeedback.org | Verify scraping/reuse terms |
| IPCC AR6 SPM + FAQs | Authoritative corrections + citable ground truth | ipcc.ch (free) | Open |
| Our World in Data (climate) | Clean datasets + methodology notes for "what the data supports" | ourworldindata.org | CC-BY |
| NASA climate.nasa.gov FAQ / NOAA climate.gov | Plain-language canonical explanations | Public | US-gov public domain |
| Google Fact Check Tools API | Claim-review feed for eval set | API key (free tier) | Rate-limited |

**Collection plan**: start with Skeptical Science + IPCC FAQs to build the
taxonomy-to-correction mapping (curated, ~50 exemplars per class not needed — 5–10
each suffices for retrieval); CARDS only if we add a trained classifier later.

## Build approach (application-level description)

- LLM classification + retrieval over the curated correction corpus (RAG) — no
  custom model training needed for MVP; defensible and cheap.
- Each output cites its source (IPCC/NASA/OWID) — "data-backed claims only" rule.
- Eval: held-out set of ~100 claims (mix from Climate Feedback + self-written
  professional-context claims), measure class accuracy + correction quality.

## Application framing hooks

- Users: negotiators, researchers, SIDS governments (matches AICA brief)
- Pipeline fit: Discover → **Understand** (Module 1) → Question → Build → Act
- Interoperability: taxonomy + corpus reused by Module 3 (Data Narrator warns
  against misread-prone chart types) and Module 5 (COP Advisor)

## Next steps

1. Harim: validate scope + taxonomy (15 min read) — adjust classes
2. Confirm AICA application deadline (still TBD — **blocking the timeline**; check
   AICA award site/email)
3. Draft Module 1 application section from this framing (1 page)
4. Start corpus collection (Skeptical Science + IPCC FAQ mapping) in `02-Research/`
