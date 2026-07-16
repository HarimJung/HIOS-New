#!/usr/bin/env python3
"""
Reddit Content Collector for HiOS Content Engine
Collects trending posts from AI and investing subreddits.

Supports two modes:
1. OAuth (recommended): Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env vars
   - Create app at https://www.reddit.com/prefs/apps → "script" type
   - Free, no user login needed, 60 requests/minute
2. Public JSON: No auth needed but Reddit blocks most requests (403)

Usage:
    # With OAuth (recommended):
    export REDDIT_CLIENT_ID=your_id
    export REDDIT_CLIENT_SECRET=your_secret
    python3 reddit_collector.py

    # Custom:
    python3 reddit_collector.py --subs wallstreetbets,artificial --timeframe week --limit 20
"""

import json
import urllib.request
import urllib.parse
import base64
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path.home() / "Documents" / "Visual Climate Hermes"
SOURCES_DIR = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / "sources"
PROCESSED_FILE = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / ".reddit_processed.json"
TOKEN_CACHE = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / ".reddit_token.json"

# Default subreddits to monitor
DEFAULT_SUBS = {
    # AI / Tech
    "artificial": "AI general",
    "MachineLearning": "ML research",
    "ChatGPT": "ChatGPT use cases",
    "LocalLLaMA": "Open source AI",
    "StableDiffusion": "AI image gen",
    "ClaudeAI": "Claude / Anthropic",
    # Investing / Finance
    "wallstreetbets": "Meme stocks & sentiment",
    "investing": "Long-term investing",
    "stocks": "Stock picks & analysis",
    "CryptoCurrency": "Crypto market",
    "personalfinance": "Personal finance",
    "FinancialIndependence": "FIRE movement",
    # Intersection
    "algotrading": "Algorithmic trading",
    "quantfinance": "Quant finance",
}

USER_AGENT = "HiOS:ContentEngine:v1.0 (by /u/visualclimate)"


def get_oauth_token() -> str | None:
    """Get Reddit OAuth token using application-only (client_credentials) flow."""
    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None

    # Check cached token
    if TOKEN_CACHE.exists():
        cached = json.loads(TOKEN_CACHE.read_text())
        if cached.get("expires_at", 0) > datetime.now().timestamp():
            return cached["access_token"]

    # Request new token
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode())
            token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600) - 60
            TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_CACHE.write_text(json.dumps(token_data))
            print(f"  [OAuth] Token acquired, expires in {token_data.get('expires_in', 0)}s")
            return token_data["access_token"]
    except Exception as e:
        print(f"  [!] OAuth token request failed: {e}")
        return None


def fetch_subreddit(sub: str, sort: str = "hot", timeframe: str = "day",
                    limit: int = 10, oauth_token: str = None) -> list:
    """Fetch top posts from a subreddit."""
    if oauth_token:
        # Use OAuth endpoint (oauth.reddit.com)
        url = f"https://oauth.reddit.com/r/{sub}/{sort}?t={timeframe}&limit={limit}"
        headers = {
            "Authorization": f"Bearer {oauth_token}",
            "User-Agent": USER_AGENT,
        }
    else:
        # Fallback to public JSON (often blocked)
        url = f"https://www.reddit.com/r/{sub}/{sort}.json?t={timeframe}&limit={limit}"
        headers = {"User-Agent": USER_AGENT}

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [!] r/{sub} failed: {e}")
        return []

    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child["data"]
        posts.append({
            "id": d["id"],
            "subreddit": sub,
            "title": d["title"],
            "score": d["score"],
            "upvote_ratio": d.get("upvote_ratio", 0),
            "num_comments": d["num_comments"],
            "url": f"https://reddit.com{d['permalink']}",
            "selftext": d.get("selftext", "")[:500],  # first 500 chars
            "created_utc": d["created_utc"],
            "author": d.get("author", "[deleted]"),
            "link_flair_text": d.get("link_flair_text", ""),
            "is_self": d.get("is_self", True),
            "external_url": d.get("url", "") if not d.get("is_self") else "",
        })

    return posts


def load_processed() -> set:
    """Load set of already-processed post IDs."""
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()


def save_processed(ids: set):
    """Save processed post IDs."""
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Keep only last 5000 IDs to prevent unbounded growth
    recent = sorted(ids)[-5000:]
    PROCESSED_FILE.write_text(json.dumps(recent, indent=2))


def score_post(post: dict) -> float:
    """Score a post for content-worthiness.
    Higher = more likely to be good content source."""
    score = 0

    # Engagement signals
    if post["score"] > 1000:
        score += 3
    elif post["score"] > 500:
        score += 2
    elif post["score"] > 100:
        score += 1

    if post["num_comments"] > 200:
        score += 2
    elif post["num_comments"] > 50:
        score += 1

    if post["upvote_ratio"] > 0.9:
        score += 1

    # Content quality signals
    if len(post.get("selftext", "")) > 200:
        score += 1  # Has substance

    # Topic relevance boost
    title_lower = post["title"].lower()
    hot_keywords = [
        "ai", "gpt", "claude", "llm", "investment", "portfolio",
        "returns", "strategy", "automation", "passive income",
        "nvidia", "sp500", "etf", "compound", "dividend",
        "beginner", "how i", "my experience", "guide",
        "data", "visualization", "python", "analysis",
    ]
    keyword_hits = sum(1 for kw in hot_keywords if kw in title_lower)
    score += min(keyword_hits, 3)

    return score


def generate_daily_digest(all_posts: list) -> str:
    """Generate a markdown digest of today's top posts."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Score and sort
    for p in all_posts:
        p["content_score"] = score_post(p)

    top_posts = sorted(all_posts, key=lambda x: x["content_score"], reverse=True)[:20]

    # Group by category
    ai_posts = [p for p in top_posts if p["subreddit"] in
                {"artificial", "MachineLearning", "ChatGPT", "LocalLLaMA",
                 "StableDiffusion", "ClaudeAI", "algotrading"}]
    finance_posts = [p for p in top_posts if p["subreddit"] in
                     {"wallstreetbets", "investing", "stocks", "CryptoCurrency",
                      "personalfinance", "FinancialIndependence", "quantfinance"}]

    md = f"""---
date: {today}
source: reddit
type: content-source
tags: [content-engine, reddit, daily-digest]
---

# Reddit Daily Digest — {today}

> 자동 수집된 콘텐츠 소스. 샤오홍슈/인스타 재가공용.
> 점수가 높을수록 콘텐츠 가치가 높음.

## AI / Tech 트렌드

"""
    for p in ai_posts[:10]:
        md += f"""### [{p['title']}]({p['url']})
- **r/{p['subreddit']}** | Score: {p['score']} | Comments: {p['num_comments']} | Content Score: {p['content_score']}
- Flair: {p.get('link_flair_text', 'none')}
{('- ' + p['selftext'][:200] + '...') if p['selftext'] else ''}
- **콘텐츠 각도:** (여기에 자기 시각 추가)

"""

    md += "\n## 투자 / 금융 트렌드\n\n"
    for p in finance_posts[:10]:
        md += f"""### [{p['title']}]({p['url']})
- **r/{p['subreddit']}** | Score: {p['score']} | Comments: {p['num_comments']} | Content Score: {p['content_score']}
- Flair: {p.get('link_flair_text', 'none')}
{('- ' + p['selftext'][:200] + '...') if p['selftext'] else ''}
- **콘텐츠 각도:** (여기에 자기 시각 추가)

"""

    md += f"""---

## 사용법
1. 위 포스트 중 콘텐츠로 만들 주제 선택
2. `/content [주제]` 실행 → 샤오홍슈 + 인스타 + YouTube 초안 동시 생성
3. 또는 `/xhs-draft [주제]` 실행 → 샤오홍슈 전용 초안

## 통계
- 수집 시각: {datetime.now().strftime("%H:%M")}
- 총 수집: {len(all_posts)}개
- AI/Tech: {len(ai_posts)}개
- 투자/금융: {len(finance_posts)}개
- 상위 20개 선별 (Content Score 기준)
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="Reddit content collector for HiOS")
    parser.add_argument("--subs", type=str, default=None,
                        help="Comma-separated subreddit names (default: all monitored)")
    parser.add_argument("--timeframe", type=str, default="day",
                        choices=["hour", "day", "week", "month"],
                        help="Time frame for 'top' sort (default: day)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Posts per subreddit (default: 10)")
    parser.add_argument("--sort", type=str, default="hot",
                        choices=["hot", "top", "new", "rising"],
                        help="Sort method (default: hot)")
    args = parser.parse_args()

    subs = args.subs.split(",") if args.subs else list(DEFAULT_SUBS.keys())
    processed = load_processed()

    # Try OAuth first
    oauth_token = get_oauth_token()
    if oauth_token:
        print("[HiOS Content Engine] Using Reddit OAuth API")
    else:
        print("[HiOS Content Engine] No OAuth credentials. Using public API (may be blocked).")
        print("  Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for reliable access.")
        print("  Create app at: https://www.reddit.com/prefs/apps (type: script)")

    print(f"Collecting from {len(subs)} subreddits...")
    all_posts = []

    for sub in subs:
        desc = DEFAULT_SUBS.get(sub, sub)
        print(f"  Fetching r/{sub} ({desc})...")
        posts = fetch_subreddit(sub, sort=args.sort, timeframe=args.timeframe,
                                limit=args.limit, oauth_token=oauth_token)

        # Filter already-processed
        new_posts = [p for p in posts if p["id"] not in processed]
        all_posts.extend(new_posts)

        # Mark as processed
        for p in posts:
            processed.add(p["id"])

        print(f"    → {len(new_posts)} new / {len(posts)} total")

    if not all_posts:
        print("[!] No new posts found.")
        return

    # Generate digest
    digest = generate_daily_digest(all_posts)
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = SOURCES_DIR / f"{today}-reddit-digest.md"
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest)

    # Save raw data
    raw_path = SOURCES_DIR / f"{today}-reddit-raw.json"
    raw_path.write_text(json.dumps(all_posts, indent=2, ensure_ascii=False))

    # Save processed IDs
    save_processed(processed)

    print(f"\n[OK] Digest saved: {output_path}")
    print(f"[OK] Raw data: {raw_path}")
    print(f"[OK] {len(all_posts)} new posts collected")


if __name__ == "__main__":
    main()
