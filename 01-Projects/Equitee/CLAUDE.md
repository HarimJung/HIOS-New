# Equitee Project Context

## Overview
Insurance fraud & vehicle crime analytics engagement (Équité-type insurance
industry client). Confirmed by Harim 2026-07-13 — the earlier "DEI consulting,
awaiting kickoff" description was incorrect.
Status: **Active** — dashboard migration and reporting work in progress.

## Workstreams (from 2026-07-09 meeting; expand as confirmed)
- **Fraud dashboard migration**: Tableau → Power BI (data modeling rebuilt from
  scratch; funnel & score page to add per NTD feedback)
- **CGI gold report extraction**: PDF extraction code; known data quality issue —
  insured period dates unreliable (cancellations/policy transfers overlap)
- **Fraud scoring model (Shift)**: classification model, threshold 0.1, low F1
  (~1,400 fraud training samples); follow-up meetings include Harim
- **Auto trend & value reports**: theft statistics (2026 H1 ~20k thefts),
  programmatic report generation via Claude Code
- Data sources: CGI, Dash (more reliable dates), IB status data (pending via Julia),
  Aurora DB (longer-term direct access)

## Key Contacts (roles TBC)
- Julia — data access requests (IB status), scoring model follow-ups
- Ivan — security review
- Kevin, Jung — auto trend stats review
- Angel, Burim — Dash API agreement

## Data Security Rules
- Never upload real/proprietary client data to any LLM.
- Claude used only to write/edit Python scripts; real data read locally only.
- Mock data via Python Faker for testing.

## Rules for This Project
- Reference global CLAUDE.md for workflow rules.
- Update contacts/scope as details are confirmed in meetings.
