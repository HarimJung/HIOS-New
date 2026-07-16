---
tags: [meeting, granola]
client: Equitee
status: filed
source: granola
granola_id: 89a22791-3c17-4d61-9a60-ef9dd71f2199
date: 2026-07-09
title: CGI data quality issues — date accuracy and policy period overlaps
---

# CGI data quality issues — date accuracy and policy period overlaps

**Date:** Jul 9, 2026 11:28 AM EDT
**Participants:** Harim Jung

## Summary

### Harim's Updates: Power BI Migration

- Fraud dashboard migration ongoing, longer than expected
  - Decomposition required data modeling from scratch
  - One additional page (funnel and score) to be added based on prior NTD feedback
- Tableau extraction complete with live data source, embeddable to web app for internal/external sharing
- Power BI: visualization limitations vs. Tableau, but matching as closely as possible
- CGI extraction code check: appears okay, but rechecking due to a PDF update earlier this week

### CGI Data Quality Issue

- Date accuracy problem flagged in CGI gold report
  - Extraction itself works, but insured period dates are unreliable
  - Cancellations and policy transfers cause overlapping periods, sometimes by more than a year
- Team member currently checking policy IDs one by one from the portal as a workaround
- Dash (alternative data source) identified as more reliable: has detailed dates and cancellation region info
- IB status data requested from Julia multiple times; still pending
- Dash API exists but may require going through Angel/Burim for agreement
- Aurora DB project flagged as a longer-term path to accessing member policy data directly

### Fraud Scoring Model (Shift Meeting Recap)

- Model is a classification model; score derived from a formula applied to the range between threshold (0.1) and 1
  - Threshold of 0.1 is low vs. standard 0.5
  - Full scoring explanation to be shared via email
- F1 score is low; root cause is small training set (only ~1,400 fraud samples)
  - Proposal: include internally discarded-but-confirmed fraud alerts as additional training data
  - Model trained initially on member data; EQ Sites data now being added on top
- Key open questions:
  - How our F1 score compares to other associations (not yet provided)
  - Score breakdown per scenario not yet available, only overall score
- Follow-up meeting with Shift expected next week, with Harim included specifically

### Auto Trend and Value Reports

- Auto trend: initial stats submitted for Kevin and Jung's review today
  - 2026 H1 theft rate: ~20,000 thefts, similar to 2021 levels (progress from 2021–2023 reversed)
  - 2021–2022 data flagged as unreliable due to reporting frequency; do not use for trend analysis
  - Will revert to values from older reports for earlier years
- Value reports: data collection underway; waiting on regional reporting upload (started this week, not yet complete)
- Programmatic report-building via Claude Code loop: iteratively adapts prior quarter's code to match new design
  - Currently generates PDF for pages 5 and 6 (data pages); other pages to be added today
  - Stories page still needs a programmatic solution (image sizing)
  - Visual match to designer template is close but not exact; deemed acceptable for future reports
  - Prompts saved as MD files for reuse
  - Fallback: manual assembly if programmatic solution isn't ready in time

### AI Tool Usage and Data Security

- Claude used only to write/edit Python scripts; no real data uploaded
  - Mock data generated via Python Faker library for comparison/testing
  - LLM never touches actual data; real data only read locally through the Python script
- Security flag: Claude downloaded a blockchain/crypto encoding module during development
  - Ivan reviewed; the downloaded version was signed and cleared
  - A separate colleague had downloaded an unsigned version of the same module
- Policy reminder: do not upload any proprietary data or IP to any LLM
- Enterprise Claude access would resolve data privacy concerns going forward

### Next Steps

- **Follow up with Julia on IB status data access**

  Requested multiple times; needed if transaction data via Dash cannot be obtained.

- **Recheck CGI extraction code** (Harim)

  A PDF update was pushed earlier this week; confirm extraction still works correctly.

- **Submit auto trend stats for review**

  Share raw data and per-year counts with Kevin and Jung; flag 2021–22 data as unreliable.

- **Communicate Claude Code security incident to Ivan and Julia**

  Even though the module was signed and cleared, the security team should be formally informed.

- **Schedule follow-up meeting with Shift on scoring model**

  Next meeting should include Harim specifically; confirm once Julia is back.

## Transcript

Transcripts not available (requires paid Granola tier).
