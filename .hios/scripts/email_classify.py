#!/usr/bin/env python3
"""AI-free Gmail classification for HiOS morning_refresh.

Reads a Gmail snapshot (as produced by server.py's _gmail_collect_snapshot)
as JSON on stdin, keyword/domain-matches each candidate into a project, and
prints one JSON manifest line matching the schema server.py's
_extract_email_manifest / _morning_refresh_finalize already expect —
identical to what the previous Claude-based classifier produced. No network
calls, no AI: this only classifies data the server already fetched.

Accuracy target is ~80%, not perfect — daily_brief (still AI-backed) reads
the resulting emails.json and can smooth over misclassifications.
"""

import json
import re
import sys

# project -> (from/to domain hints, keyword phrases). Keywords are matched
# case-insensitively against "subject snippet"; short/ambiguous words use
# \b word boundaries to avoid false positives (e.g. bare "who" would match
# almost any English sentence, so WHO relies on its domain + specific terms
# instead of the literal project name).
PROJECT_RULES = {
    "UNFPA-CSE": {
        "domains": ["unfpa.org"],
        "keywords": ["unfpa", r"\bcse\b", "comprehensive sexuality education",
                     "wafa dhaouadi", "steve petite"],
    },
    "Equitee": {
        "domains": ["equiteco.ca"],
        "keywords": ["equitee", "equite", "equitée", "équité", "false positive",
                      "fraud dashboard", "power bi", "auto theft"],
    },
    "WMO": {
        "domains": ["wmo.int"],
        "keywords": [r"\bwmo\b", "moodle", r"\bbcm\b", "articulate",
                     "validation workshop", "training module"],
    },
    "WHO": {
        "domains": ["who.int"],
        "keywords": ["household energy", r"\bhcf\b", r"\bsdg7\b", r"\bwims\b",
                     "electrification"],
    },
    "Climate-AICA": {
        "domains": [],
        "keywords": [r"\baica\b", "climate literacy", "climate data literacy",
                      "aica award"],
    },
    "Visual-Climate": {
        "domains": ["visualclimate.org"],
        "keywords": ["visual climate", "visualclimate", "youtube",
                      "xiaohongshu", "소홍슈"],
    },
}

OTHER_PROJECT = "기타"

NEEDS_ACTION_PATTERNS = [
    r"\baction required\b",
    r"\bplease (respond|reply|confirm|sign|submit|review|prepare|draft|send|share|provide)\b",
    r"\bkindly (prepare|draft|send|share|provide|confirm)\b",
    r"\bcould you\b", r"\bcan you\b", r"\brequested (to|that)\b",
    r"\bdeadline\b", r"\bdue (by|date)\b", r"\burgent\b", r"\basap\b",
    r"response needed", r"awaiting your", r"확인\s*부탁", r"회신\s*부탁",
    r"제출\s*(부탁|필요)", r"작성\s*(부탁|요청|필요)", r"준비\s*(부탁|요청)",
    r"마감", r"기한",
]
NEEDS_ACTION_RE = re.compile("|".join(NEEDS_ACTION_PATTERNS), re.I)


def _domain_of(addr):
    m = re.search(r"@([\w.-]+)", addr or "")
    return m.group(1).lower() if m else ""


def classify(candidate):
    subject = candidate.get("subject", "") or ""
    snippet = candidate.get("snippet", "") or ""
    frm = candidate.get("from", "") or ""
    to = candidate.get("to", "") or ""
    source_query = candidate.get("source_query", "") or ""
    text = f"{subject} {snippet}".lower()
    from_domain = _domain_of(frm)
    to_domain = _domain_of(to)

    # source_query is the project whose dedicated Gmail search surfaced this
    # message — a strong prior, but content can still override it below.
    scores = {}
    if source_query in PROJECT_RULES:
        scores[source_query] = scores.get(source_query, 0) + 2

    for project, rule in PROJECT_RULES.items():
        if from_domain in rule["domains"] or to_domain in rule["domains"]:
            scores[project] = scores.get(project, 0) + 3
        for kw in rule["keywords"]:
            pattern = kw if kw.startswith(r"\b") else re.escape(kw)
            if re.search(pattern, text, re.I):
                scores[project] = scores.get(project, 0) + 1

    if not scores:
        return OTHER_PROJECT
    return max(scores.items(), key=lambda kv: kv[1])[0]


def summarize(candidate):
    snippet = (candidate.get("snippet") or "").strip()
    if snippet:
        return snippet[:150]
    return (candidate.get("subject") or "").strip()[:150]


def build_email(candidate):
    needs_action = bool(NEEDS_ACTION_RE.search(
        f"{candidate.get('subject', '')} {candidate.get('snippet', '')}"))
    return {
        "project": classify(candidate),
        "subject": candidate.get("subject", ""),
        "from": candidate.get("from", ""),
        "date": candidate.get("date", ""),
        "thread_id": candidate.get("thread_id", ""),
        "summary": summarize(candidate),
        "needs_action": needs_action,
        "suggested_action": "이메일 내용 확인 후 회신/처리 필요" if needs_action else "",
    }


def main():
    raw = sys.stdin.read()
    try:
        snapshot = json.loads(raw) if raw.strip() else {}
    except ValueError:
        snapshot = {}
    if not isinstance(snapshot, dict):
        snapshot = {}

    connection = snapshot.get("connection")
    if not isinstance(connection, dict):
        connection = {"status": "error", "error": "snapshot 형식 오류"}

    manifest = {
        "emails": [],
        "searched": sorted(PROJECT_RULES.keys()),
        "connections": {"gmail": connection},
    }

    if connection.get("status") == "ok":
        candidates = snapshot.get("candidates", [])
        if isinstance(candidates, list):
            for candidate in candidates:
                if isinstance(candidate, dict):
                    manifest["emails"].append(build_email(candidate))

    print(f"이메일 분류 완료 — {len(manifest['emails'])}건 (AI 미사용, 규칙 기반)")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
