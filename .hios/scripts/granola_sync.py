#!/usr/bin/env python3
"""
DEPRECATED: This script no longer works as of Granola v7+.

Granola now encrypts all credential files (supabase.json.enc).
Use Granola MCP server instead via Claude Desktop.

See: 05-AI/2026-07-13-granola-sync-troubleshooting.md

---

HiOS Granola Sync — Fetch meetings from Granola API and export to vault.

Uses WorkOS tokens from Granola's local supabase.json (no paid plan needed).
Exports meeting notes and transcripts as Markdown to 00-Inbox/.

Usage:
    python3 granola_sync.py                  # Fetch last 24h meetings
    python3 granola_sync.py --hours 48       # Fetch last 48h meetings
    python3 granola_sync.py --all            # Fetch all meetings
    python3 granola_sync.py --since 2026-07-01  # Fetch since date
"""

import json
import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Paths
GRANOLA_CONFIG = Path.home() / "Library" / "Application Support" / "Granola" / "supabase.json"
VAULT_ROOT = Path(__file__).resolve().parent.parent.parent  # .hios/scripts/ -> vault root
INBOX_DIR = VAULT_ROOT / "00-Inbox" / "granola-sync"
PROCESSED_LOG = VAULT_ROOT / ".hios" / "granola_processed.json"

API_BASE = "https://api.granola.ai"

# Project routing keywords
PROJECT_KEYWORDS = {
    "UNFPA-CSE": [
        "unfpa", "cse", "comprehensive sexuality education", "wafa",
        "steve petite", "sexuality education", "country mapping",
        "baseline", "signal detection", "reporting platform",
        "landing page", "nairobi"
    ],
    "Equitee": [
        "equitée", "equitee", "dei", "diversity equity inclusion",
        "inclusion", "equity dashboard"
    ],
    "Climate-AICA": [
        "aica", "climate literacy", "misconception detector",
        "data narrator", "cop", "climate data", "sids",
        "climate negotiat", "climate module"
    ],
    "Visual-Climate": [
        "youtube", "소홍슈", "xiaohongshu", "content",
        "thumbnail", "newsletter", "brand", "subscriber",
        "visual climate"
    ],
}


def get_access_token():
    """Extract WorkOS access token from Granola's supabase.json."""
    if not GRANOLA_CONFIG.exists():
        print(f"Error: Granola config not found at {GRANOLA_CONFIG}")
        sys.exit(1)

    with open(GRANOLA_CONFIG) as f:
        data = json.load(f)

    # Double-decode: workos_tokens is a JSON string inside the outer JSON
    workos_tokens = json.loads(data["workos_tokens"])
    return workos_tokens["access_token"]


def api_request(endpoint, body=None, token=None):
    """Make an authenticated request to Granola API."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        # Granola API rejects requests without app client identification
        # ("Unsupported client") — mirror the desktop app's headers.
        "User-Agent": "Granola/6.4.0 Electron/33.0.0",
        "X-Client-Version": "6.4.0",
    }

    payload = json.dumps(body).encode() if body else None
    req = Request(url, data=payload, headers=headers, method="POST")

    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 401:
            print("Error: Access token expired. Restart Granola app to refresh.")
            sys.exit(1)
        print(f"API Error {e.code}: {e.read().decode()[:200]}")
        sys.exit(1)
    except URLError as e:
        print(f"Network error: {e.reason}")
        sys.exit(1)


def fetch_documents(token, limit=100, offset=0):
    """Fetch meeting documents from Granola API."""
    return api_request("/v2/get-documents", {
        "limit": limit,
        "offset": offset,
        "include_last_viewed_panel": True,
    }, token)


def fetch_transcript(token, document_id):
    """Fetch transcript for a specific document."""
    return api_request("/v1/get-document-transcript", {
        "document_id": document_id,
    }, token)


def prosemirror_to_markdown(node, depth=0):
    """Convert ProseMirror JSON to Markdown (simplified)."""
    if not node or not isinstance(node, dict):
        return ""

    node_type = node.get("type", "")
    content = node.get("content", [])
    text = node.get("text", "")
    marks = node.get("marks", [])
    attrs = node.get("attrs", {})

    result = ""

    if node_type == "text":
        t = text
        for mark in marks:
            mt = mark.get("type", "")
            if mt == "bold":
                t = f"**{t}**"
            elif mt == "italic":
                t = f"*{t}*"
            elif mt == "code":
                t = f"`{t}`"
            elif mt == "link":
                href = mark.get("attrs", {}).get("href", "")
                t = f"[{t}]({href})"
        return t

    if node_type == "heading":
        level = attrs.get("level", 1)
        prefix = "#" * level + " "
        inner = "".join(prosemirror_to_markdown(c, depth) for c in content)
        return f"\n{prefix}{inner}\n\n"

    if node_type == "paragraph":
        inner = "".join(prosemirror_to_markdown(c, depth) for c in content)
        return f"{inner}\n\n"

    if node_type == "bulletList":
        return "".join(prosemirror_to_markdown(c, depth) for c in content)

    if node_type == "orderedList":
        return "".join(prosemirror_to_markdown(c, depth) for c in content)

    if node_type == "listItem":
        inner = "".join(prosemirror_to_markdown(c, depth + 1) for c in content)
        indent = "  " * depth
        lines = inner.strip().split("\n")
        first = f"{indent}- {lines[0]}\n" if lines else ""
        rest = "\n".join(f"{indent}  {l}" for l in lines[1:] if l.strip())
        return first + (rest + "\n" if rest else "")

    if node_type == "blockquote":
        inner = "".join(prosemirror_to_markdown(c, depth) for c in content)
        return "\n".join(f"> {line}" for line in inner.strip().split("\n")) + "\n\n"

    if node_type == "codeBlock":
        lang = attrs.get("language", "")
        inner = "".join(prosemirror_to_markdown(c, depth) for c in content)
        return f"\n```{lang}\n{inner}\n```\n\n"

    if node_type == "horizontalRule":
        return "\n---\n\n"

    if node_type == "hardBreak":
        return "\n"

    # Default: recurse into content
    for child in content:
        result += prosemirror_to_markdown(child, depth)

    return result


def classify_project(title, notes_text, transcript_text):
    """Determine which project a meeting belongs to based on content."""
    combined = f"{title} {notes_text} {transcript_text}".lower()

    scores = {}
    for project, keywords in PROJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[project] = score

    if scores:
        return max(scores, key=scores.get)
    return "Unclassified"


def format_transcript(utterances):
    """Format transcript utterances into readable Markdown."""
    if not utterances:
        return "(No transcript available)"

    lines = []
    for u in utterances:
        source = u.get("source", "unknown")
        text = u.get("text", "").strip()
        if not text:
            continue
        speaker = "You" if source == "microphone" else "Other"
        lines.append(f"**{speaker}:** {text}")

    return "\n\n".join(lines)


def load_processed():
    """Load set of already-processed document IDs."""
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG) as f:
            return set(json.load(f))
    return set()


def save_processed(processed_ids):
    """Save processed document IDs."""
    PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_LOG, "w") as f:
        json.dump(sorted(processed_ids), f, indent=2)


def export_meeting(doc, transcript, output_dir):
    """Export a single meeting to Markdown file."""
    doc_id = doc.get("id", "unknown")
    title = doc.get("title", "Untitled Meeting")
    created = doc.get("created_at", "")
    updated = doc.get("updated_at", "")

    # Parse date
    try:
        date_obj = datetime.fromisoformat(created.replace("Z", "+00:00"))
        date_str = date_obj.strftime("%Y-%m-%d")
        time_str = date_obj.strftime("%H:%M")
    except (ValueError, AttributeError):
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = ""

    # Extract notes from ProseMirror
    panel = doc.get("last_viewed_panel", {})
    notes_md = ""
    if panel and isinstance(panel, dict):
        notes_md = prosemirror_to_markdown(panel)

    # Format transcript
    transcript_md = format_transcript(transcript) if transcript else "(No transcript)"

    # Classify project
    project = classify_project(title, notes_md, transcript_md)

    # Sanitize filename
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
    safe_title = re.sub(r'[\s]+', '-', safe_title)[:60]
    filename = f"{date_str}-{safe_title}.md"

    # Build Markdown
    content = f"""---
date: {date_str}
title: "{title}"
granola_id: {doc_id}
project: {project}
type: meeting-transcript
tags: [meeting, granola, {project.lower()}]
---

# {title}

**Date:** {date_str} {time_str}
**Project:** {project}
**Source:** Granola (auto-synced)

## Notes

{notes_md.strip() if notes_md.strip() else "(No notes)"}

## Transcript

{transcript_md}
"""

    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        f.write(content)

    return filepath, project


def main():
    parser = argparse.ArgumentParser(description="Sync Granola meetings to HiOS vault")
    parser.add_argument("--hours", type=int, default=24,
                        help="Fetch meetings from last N hours (default: 24)")
    parser.add_argument("--all", action="store_true",
                        help="Fetch all meetings")
    parser.add_argument("--since", type=str,
                        help="Fetch meetings since date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max meetings to fetch (default: 50)")
    parser.add_argument("--force", action="store_true",
                        help="Re-process already synced meetings")
    args = parser.parse_args()

    print("HiOS Granola Sync")
    print("=" * 40)

    # Get auth token
    print("Reading Granola credentials...")
    token = get_access_token()

    # Determine time filter
    if args.since:
        cutoff = datetime.fromisoformat(args.since)
    elif args.all:
        cutoff = None
    else:
        cutoff = datetime.now() - timedelta(hours=args.hours)

    if cutoff:
        print(f"Fetching meetings since: {cutoff.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("Fetching all meetings")

    # Load processed IDs
    processed = load_processed() if not args.force else set()

    # Fetch documents
    print(f"Fetching documents (limit={args.limit})...")
    docs = fetch_documents(token, limit=args.limit)

    if not isinstance(docs, list):
        docs = docs.get("documents", docs.get("data", []))

    print(f"Found {len(docs)} documents")

    # Filter by date and processed status
    new_docs = []
    for doc in docs:
        doc_id = doc.get("id", "")
        if doc_id in processed:
            continue

        created = doc.get("created_at", "")
        if cutoff and created:
            try:
                doc_date = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                if doc_date < cutoff:
                    continue
            except ValueError:
                pass

        new_docs.append(doc)

    print(f"New meetings to process: {len(new_docs)}")

    if not new_docs:
        print("No new meetings to sync.")
        return

    # Process each meeting
    results = {"total": 0, "by_project": {}, "files": []}

    for doc in new_docs:
        doc_id = doc.get("id", "unknown")
        title = doc.get("title", "Untitled")

        print(f"\nProcessing: {title}")

        # Fetch transcript
        try:
            transcript = fetch_transcript(token, doc_id)
        except SystemExit:
            transcript = None

        # Export
        filepath, project = export_meeting(doc, transcript, INBOX_DIR)

        results["total"] += 1
        results["by_project"][project] = results["by_project"].get(project, 0) + 1
        results["files"].append(str(filepath))

        processed.add(doc_id)

        print(f"  -> {filepath.name} [{project}]")

    # Save processed IDs
    save_processed(processed)

    # Summary
    print("\n" + "=" * 40)
    print(f"Synced: {results['total']} meetings")
    for proj, count in sorted(results["by_project"].items()):
        print(f"  {proj}: {count}")
    print(f"\nFiles saved to: {INBOX_DIR}")
    print("\nRun '/process-inbox' in Claude Code to route these to project folders.")


if __name__ == "__main__":
    main()
