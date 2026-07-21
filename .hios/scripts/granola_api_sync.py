#!/usr/bin/env python3
"""AI-free Granola sync via the official public API (Business/Enterprise plan).

Replaces the MCP-based granola_refresh: mcp.granola.ai requires interactive
browser OAuth per user and cannot work from a headless server session.
public-api.granola.ai uses a static Bearer token (GRANOLA_API_KEY) instead,
which is exactly what unattended automation needs.

Prints one JSON manifest line matching what server.py's
_extract_granola_manifest / _granola_refresh_finalize already expect, so
that finalize hook stays unchanged. Only meetings_seen/meetings_created are
populated here — "actions" is intentionally left empty: extracting real
action items from a transcript is a judgment call, done downstream by the
AI-backed daily_brief/project_update tasks that already read these meeting
files, not by this rule-based classifier.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://public-api.granola.ai/v1"
VAULT_ROOT = Path(__file__).resolve().parent.parent.parent  # .hios/scripts/ -> vault root
PROJECTS_DIR = VAULT_ROOT / "01-Projects"
INBOX_DIR = VAULT_ROOT / "00-Inbox"
PROCESSED_LOG = VAULT_ROOT / ".hios" / "state" / "granola_api_processed.json"
LOOKBACK_DAYS = 10

# Kept in sync with email_classify.py's PROJECT_RULES keyword lists.
PROJECT_RULES = {
    "UNFPA-CSE": ["unfpa", r"\bcse\b", "comprehensive sexuality education",
                  "wafa dhaouadi", "steve petite"],
    "Equitee": ["equitee", "equite", "equitée", "équité", "false positive",
                "fraud dashboard", "power bi", "auto theft"],
    "WMO": [r"\bwmo\b", "moodle", r"\bbcm\b", "articulate",
            "validation workshop", "training module"],
    "WHO": ["household energy", r"\bhcf\b", r"\bsdg7\b", r"\bwims\b",
            "electrification"],
    "Climate-AICA": [r"\baica\b", "climate literacy", "climate data literacy",
                      "aica award"],
    "Visual-Climate": ["visual climate", "visualclimate", "youtube",
                        "xiaohongshu", "소홍슈"],
}


def _api_get(path, token, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def classify(title, summary):
    text = f"{title} {summary}".lower()
    scores = {}
    for project, keywords in PROJECT_RULES.items():
        for kw in keywords:
            pattern = kw if kw.startswith(r"\b") else re.escape(kw)
            if re.search(pattern, text, re.I):
                scores[project] = scores.get(project, 0) + 1
    if not scores:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]


def meetings_dir_for(project):
    proj_dir = PROJECTS_DIR / project
    existing = sorted(proj_dir.glob("*-Meetings"))
    if existing:
        return existing[0]
    return proj_dir / "02-Meetings"


def format_transcript(entries, owner_name):
    """entry['speaker'] is {"source": "microphone"|"speaker"} — the API
    doesn't diarize other attendees, so "microphone" (the note owner's own
    mic) is the only identifiable voice; everything else is "상대방"."""
    if not entries:
        return "(전사 없음)"
    lines = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source = (entry.get("speaker") or {}).get("source")
        who = (owner_name or "본인") if source == "microphone" else "상대방"
        text = (entry.get("text") or "").strip()
        if text:
            lines.append(f"**{who}:** {text}")
    return "\n\n".join(lines) if lines else "(전사 없음)"


def write_note(note, project, detail):
    created = note.get("created_at") or note.get("created_after") or ""
    date_str = created[:10] if len(created) >= 10 else time.strftime("%Y-%m-%d")
    title = note.get("title") or "제목 없음"
    safe_title = re.sub(r"[^\w\s-]", "", title).strip()
    safe_title = re.sub(r"\s+", "-", safe_title)[:60] or "meeting"

    out_dir = meetings_dir_for(project) if project else INBOX_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date_str}-{safe_title}.md"

    owner = detail.get("owner") or note.get("owner") or {}
    summary = (detail.get("summary_markdown") or detail.get("summary_text") or "").strip()
    transcript_md = format_transcript(detail.get("transcript"), owner.get("name"))
    attendees = detail.get("attendees") or []
    attendee_line = ", ".join(
        a.get("name") or a.get("email", "") for a in attendees if isinstance(a, dict)
    )

    content = f"""---
date: {date_str}
title: "{title}"
granola_id: {note.get('id', '')}
project: {project or '미분류'}
type: meeting-transcript
tags: [meeting, granola{', ' + project.lower() if project else ''}]
source: granola
status: active
due: ""
priority: med
---

# {title}

**Date:** {date_str}
**Project:** {project or '미분류'}
**Owner:** {owner.get('name', '')}
**Attendees:** {attendee_line or '(정보 없음)'}
**Source:** Granola (공식 API, AI 미사용 자동 동기화)

## AI 요약 (Granola)

{summary or "(요약 없음)"}

## Transcript

{transcript_md}
"""
    path.write_text(content, encoding="utf-8")
    return path


def load_processed():
    try:
        return set(json.loads(PROCESSED_LOG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def save_processed(ids):
    PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_LOG.write_text(
        json.dumps(sorted(ids)[-2000:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    manifest = {
        "connection": {"status": "ok", "error": None},
        "meetings_seen": 0,
        "meetings_created": 0,
        "actions": [],
    }

    token = os.environ.get("GRANOLA_API_KEY", "").strip()
    if not token:
        manifest["connection"] = {
            "status": "error",
            "error": "GRANOLA_API_KEY 환경변수 없음 (.hios/.env 확인)",
        }
        print(json.dumps(manifest, ensure_ascii=False))
        return

    since = time.strftime(
        "%Y-%m-%dT00:00:00Z", time.gmtime(time.time() - LOOKBACK_DAYS * 86400)
    )
    processed = load_processed()

    try:
        listing = _api_get("/notes", token, {"created_after": since})
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        manifest["connection"] = {
            "status": "error",
            "error": f"Granola API 목록 조회 실패: {exc}"[:300],
        }
        print(json.dumps(manifest, ensure_ascii=False))
        return

    notes = listing.get("notes") if isinstance(listing, dict) else listing
    if not isinstance(notes, list):
        notes = []
    manifest["meetings_seen"] = len(notes)

    created = 0
    for note in notes:
        if not isinstance(note, dict):
            continue
        note_id = str(note.get("id", ""))
        if not note_id or note_id in processed:
            continue
        try:
            detail = _api_get(f"/notes/{note_id}", token, {"include": "transcript"})
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
            print(f"[경고] {note_id} 상세 조회 실패: {exc}", file=sys.stderr)
            continue
        if not isinstance(detail, dict):
            detail = {}
        project = classify(note.get("title", ""), detail.get("summary", ""))
        write_note(note, project, detail)
        processed.add(note_id)
        created += 1

    manifest["meetings_created"] = created
    save_processed(processed)
    print(f"그래놀라 동기화 완료 — 조회 {manifest['meetings_seen']}건, "
          f"신규 {created}건 (AI 미사용, 공식 API)")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
