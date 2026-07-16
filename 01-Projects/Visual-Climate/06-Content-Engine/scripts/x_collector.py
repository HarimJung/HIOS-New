#!/usr/bin/env python3
"""
X (Twitter) Content Collector for HiOS Content Engine

Uses Nitter instances (public Twitter frontend) for RSS-based collection.
No API key needed. Falls back to curated list approach if Nitter is down.

Also supports X API Bearer Token if available (set X_BEARER_TOKEN env var).

Usage:
    python3 x_collector.py
    X_BEARER_TOKEN=xxx python3 x_collector.py --mode api
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
import os
import sys
import argparse
import re
import html
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path.home() / "Documents" / "Visual Climate Hermes"
SOURCES_DIR = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / "sources"
PROCESSED_FILE = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / ".x_processed.json"

# Accounts to monitor — curated for AI + investing content
MONITORED_ACCOUNTS = {
    # AI / Tech thought leaders
    "AndrewYNg": "Andrew Ng — AI education",
    "kaboroy": "Yann LeCun — Meta AI",
    "demaboroy": "Demis Hassabis — DeepMind",
    "sama": "Sam Altman — OpenAI",
    "AnthropicAI": "Anthropic",
    "OpenAI": "OpenAI official",
    "GoogleDeepMind": "Google DeepMind",
    "elaborationai": "AI news aggregator",
    # Investing / Finance
    "chaaboroy": "Chamath — venture/investing",
    "mcaboroy": "Michael Burry (when active)",
    "unusual_whales": "Options flow data",
    "zaboroy": "ZeroHedge — macro finance",
    "WSJ": "Wall Street Journal",
    "business": "Bloomberg",
    # AI + Finance intersection
    "quantian1": "Quant finance + AI",
    "yaboroy": "AI trading signals",
}

# RSS/Nitter instances (try multiple, they go down frequently)
NITTER_INSTANCES = [
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.woodland.cafe",
]

USER_AGENT = "HiOS-ContentEngine/1.0"


def fetch_nitter_rss(username: str) -> list:
    """Try to fetch tweets via Nitter RSS. Returns list of tweet dicts."""
    for instance in NITTER_INSTANCES:
        url = f"https://{instance}/{username}/rss"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read().decode()
                root = ET.fromstring(xml_data)

                tweets = []
                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    description = item.findtext("description", "")

                    # Clean HTML from description
                    clean_text = re.sub(r'<[^>]+>', '', html.unescape(description))

                    tweets.append({
                        "id": link.split("/")[-1] if "/" in link else link,
                        "username": username,
                        "text": clean_text[:500],
                        "title": title,
                        "url": link.replace(instance, "x.com"),
                        "published": pub_date,
                        "source": f"nitter ({instance})",
                    })
                return tweets
        except Exception:
            continue

    return []


def fetch_x_api(username: str, bearer_token: str) -> list:
    """Fetch tweets using X API v2 (requires Bearer Token)."""
    # First get user ID
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode())
            user_id = user_data["data"]["id"]
    except Exception as e:
        print(f"  [!] @{username} user lookup failed: {e}")
        return []

    # Get recent tweets
    url = (f"https://api.twitter.com/2/users/{user_id}/tweets"
           f"?max_results=10&tweet.fields=created_at,public_metrics,text")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [!] @{username} tweets failed: {e}")
        return []

    tweets = []
    for t in data.get("data", []):
        metrics = t.get("public_metrics", {})
        tweets.append({
            "id": t["id"],
            "username": username,
            "text": t["text"][:500],
            "url": f"https://x.com/{username}/status/{t['id']}",
            "published": t.get("created_at", ""),
            "likes": metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "source": "x_api_v2",
        })

    return tweets


def load_processed() -> set:
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()


def save_processed(ids: set):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    recent = sorted(ids)[-5000:]
    PROCESSED_FILE.write_text(json.dumps(recent, indent=2))


def generate_digest(all_tweets: list) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    # Separate by category
    ai_accounts = {"AndrewYNg", "kaboroy", "demaboroy", "sama",
                   "AnthropicAI", "OpenAI", "GoogleDeepMind", "elaborationai"}
    finance_accounts = {"chaaboroy", "mcaboroy", "unusual_whales",
                        "zaboroy", "WSJ", "business"}

    ai_tweets = [t for t in all_tweets if t["username"] in ai_accounts]
    finance_tweets = [t for t in all_tweets if t["username"] in finance_accounts]
    other_tweets = [t for t in all_tweets
                    if t["username"] not in ai_accounts and t["username"] not in finance_accounts]

    md = f"""---
date: {today}
source: x-twitter
type: content-source
tags: [content-engine, x, twitter, daily-digest]
---

# X/Twitter Daily Digest — {today}

> 모니터링 계정에서 수집한 트윗. 샤오홍슈/인스타 재가공용.

## AI / Tech

"""
    for t in ai_tweets[:10]:
        md += f"""**@{t['username']}** — [{t['text'][:80]}...]({t['url']})
{t['text'][:200]}

---

"""

    md += "\n## 투자 / 금융\n\n"
    for t in finance_tweets[:10]:
        md += f"""**@{t['username']}** — [{t['text'][:80]}...]({t['url']})
{t['text'][:200]}

---

"""

    if other_tweets:
        md += "\n## AI + Finance 교차점\n\n"
        for t in other_tweets[:5]:
            md += f"""**@{t['username']}** — [{t['text'][:80]}...]({t['url']})
{t['text'][:200]}

---

"""

    md += f"""
## 통계
- 수집 시각: {datetime.now().strftime("%H:%M")}
- 총 수집: {len(all_tweets)}개
- AI/Tech: {len(ai_tweets)}개
- 투자/금융: {len(finance_tweets)}개
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="X/Twitter content collector for HiOS")
    parser.add_argument("--mode", type=str, default="nitter",
                        choices=["nitter", "api"],
                        help="Collection mode (default: nitter RSS)")
    parser.add_argument("--accounts", type=str, default=None,
                        help="Comma-separated usernames (default: all monitored)")
    args = parser.parse_args()

    accounts = args.accounts.split(",") if args.accounts else list(MONITORED_ACCOUNTS.keys())
    bearer_token = os.environ.get("X_BEARER_TOKEN", "")
    processed = load_processed()

    if args.mode == "api" and not bearer_token:
        print("[!] X_BEARER_TOKEN not set. Falling back to Nitter RSS.")
        args.mode = "nitter"

    print(f"[HiOS Content Engine] Collecting from {len(accounts)} X accounts ({args.mode} mode)...")
    all_tweets = []

    for username in accounts:
        desc = MONITORED_ACCOUNTS.get(username, username)
        print(f"  Fetching @{username} ({desc})...")

        if args.mode == "api":
            tweets = fetch_x_api(username, bearer_token)
        else:
            tweets = fetch_nitter_rss(username)

        new_tweets = [t for t in tweets if t["id"] not in processed]
        all_tweets.extend(new_tweets)
        for t in tweets:
            processed.add(t["id"])

        print(f"    → {len(new_tweets)} new / {len(tweets)} total")

    if not all_tweets:
        print("[!] No new tweets found. Nitter instances may be down.")
        print("    Try: python3 x_collector.py --mode api (with X_BEARER_TOKEN)")
        return

    # Generate digest
    digest = generate_digest(all_tweets)
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = SOURCES_DIR / f"{today}-x-digest.md"
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest)

    raw_path = SOURCES_DIR / f"{today}-x-raw.json"
    raw_path.write_text(json.dumps(all_tweets, indent=2, ensure_ascii=False))

    save_processed(processed)

    print(f"\n[OK] Digest: {output_path}")
    print(f"[OK] {len(all_tweets)} new tweets collected")


if __name__ == "__main__":
    main()
