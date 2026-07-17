---
tags: [unfpa, communications, draft, itso, infrastructure]
client: UNFPA-CSE
status: draft
priority: HIGH
created: 2026-07-17
---

# Technical Questions for I-G (ITSO/KM) — Draft (v1)

> **Context**: Wafa's 7/15 email introduced Isabelle-Geraldine (I-G) and invited
> Harim to write directly with technical questions. This is the reply-all draft.
> **Send from hajung@unfpa.org** on Wafa's thread (Wafa + I-G cc-ed).
>
> **Why these questions**: answers determine the tech choice for 4 of 6
> deliverables before they can start —
> - Landing Page (#1): Sites vs custom → embedding + domain policy
> - Reporting Platform (#2, due Jul 31): Apps Script deployment + finance data
> - Mapping Dashboard (#4, Nairobi Sep 22): Looker vs Tableau Public vs custom
>   — **data classification answer decides this** (finance data on a public
>   Tableau server is likely prohibited)
> - Digital Interface (#5): AI tooling availability (Gemini/API budget)
> - Signal Detection (#6): external API calls from Apps Script
>
> Timing: Wafa OOO Jul 27–Aug 2. Getting I-G's answers (or the right focal
> point) before ~Jul 25 keeps the dashboard tech decision on track for Nairobi.

**To**: Isabelle-Geraldine
**Cc**: Wafa Dhaouadi
**Thread**: Re: [Wafa's intro email, 7/15]

---

Dear Isabelle-Geraldine,

Thank you very much, Wafa, for the introduction.

Dear I-G, it's a pleasure to e-meet you. As Wafa mentioned, I'm supporting the
CSE team on visualization assets, dashboards, and internal knowledge tools —
all intended to live within the UNFPA Google Workspace environment. To scope
the work correctly (and avoid building anything that conflicts with ITSO
policy), I would appreciate your guidance on the following. I've grouped the
questions so you can also forward specific blocks to the right focal points if
they sit with different teams.

**1. Available tools and licensing**
- Which of the following are enabled for consultant accounts in the UNFPA
  Workspace: Google Sites, Looker Studio (and is Looker Studio **Pro** licensed,
  or the free tier only?), AppSheet, Apps Script, BigQuery?
- Are there approved AI tools within the environment (e.g., Gemini for
  Workspace, or a sanctioned API route such as Vertex AI)? The team is
  exploring an AI-assisted search feature for an internal resource hub.

**2. Custom development and deployment**
- Can Apps Script projects be deployed as **web apps** (domain-restricted) for
  internal users? Any approval process for OAuth scopes or advanced services?
- Is building/hosting a custom web application outside Workspace (e.g., Cloud
  Run or external hosting) permitted for internal tools, or is this restricted
  to native Google tools?
- Any policy on source-code management for Apps Script (e.g., GitHub/clasp)?

**3. Embedding and external content**
- Can external interactive content (e.g., Tableau Public, Flourish, Datawrapper
  charts, custom maps) be embedded into internal Google Sites pages?
- Conversely, can Looker Studio reports be embedded and shared with users
  outside HQ (regional/country offices) without extra licensing issues?

**4. Data governance and sharing**
- The mapping dashboard would include **programme operations and finance
  figures**. Is publishing such data to a public visualization service (e.g.,
  Tableau Public, where data is world-readable) prohibited? I assume yes, but
  want to confirm before locking the tech choice.
- What are the external-sharing settings for Sheets/Drive — can country office
  colleagues (unfpa.org accounts) access shared assets by default, and is
  tiered access (HQ edit / CO view) manageable at the Workspace level?
- Is finance data available via any scheduled export or API (e.g., from
  Quantum), or is manual extraction the standard practice?

**5. Process**
- If any of the above needs an exception or a new tool request, what is the
  process (ITSO ticket, focal point, typical review path)?
- Is there an existing KM/intranet platform where a "CSE landing page" should
  live, rather than a standalone Google Site? Happy to align with whatever the
  KM Unit recommends.

I'm equally happy to go through these on a brief call if that's easier — I can
adapt to your schedule. Even partial answers or a pointer to existing policy
documentation would be very helpful.

Thank you very much for your time and support.

Best regards,
Harim Jung
Consultant, CSE Team — Gender, Human Rights & Inclusion Branch

---

## Notes for Harim
- **가장 결정적인 답변**: §4 데이터 분류 (finance 데이터 → Tableau Public 가능 여부).
  이 답이 대시보드 기술 선택(Nairobi 9/22 데모)을 결정함. Looker Studio Pro 여부(§1)가
  그 다음.
- §2 Apps Script web app 답변은 Reporting Platform Option C(장기 로드맵) 및
  Digital Interface 설계에 직결.
- I-G가 다른 focal point로 넘길 가능성 높음 → 블록별 포워딩 가능하게 구성해둠.
- 콜을 잡게 되면: 화면 공유로 현재 Workspace에서 보이는 도구 메뉴를 직접 확인하는 게
  이메일 왕복보다 빠름.
- 7/25 전 답변 확보 목표 (Wafa OOO 7/27–8/2, 기술 선택이 8월로 밀리면 Nairobi 준비
  기간 잠식).
