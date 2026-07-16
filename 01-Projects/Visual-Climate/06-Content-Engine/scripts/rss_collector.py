#!/usr/bin/env python3
"""
RSS-based Content Collector for HiOS Content Engine

Uses RSS feeds from Reddit, tech blogs, and finance sites.
No API keys needed. Works immediately.

Usage:
    python3 rss_collector.py
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path.home() / "Documents" / "Visual Climate Hermes"
SOURCES_DIR = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / "sources"
PROCESSED_FILE = VAULT_DIR / "01-Projects" / "Visual-Climate" / "06-Content-Engine" / ".rss_processed.json"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HiOS/1.0"

# RSS feeds to monitor
FEEDS = {
    # Reddit (RSS still works)
    "Reddit: AI": "https://www.reddit.com/r/artificial+MachineLearning+ChatGPT+LocalLLaMA+ClaudeAI/.rss?limit=20",
    "Reddit: Investing": "https://www.reddit.com/r/wallstreetbets+investing+stocks+CryptoCurrency/.rss?limit=20",
    "Reddit: AlgoTrading": "https://www.reddit.com/r/algotrading+quantfinance/.rss?limit=15",
    # Tech / AI blogs
    "Hacker News": "https://hnrss.org/best?count=15",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    # Finance
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Investopedia": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
}


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_atom_or_rss(xml_data: str) -> list:
    """Parse both RSS 2.0 and Atom feeds."""
    items = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return []

    # Detect feed type
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # Try Atom first
    for entry in root.findall(".//atom:entry", ns):
        title = entry.findtext("atom:title", "", ns)
        link_el = entry.find("atom:link[@rel='alternate']", ns)
        if link_el is None:
            link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        content = entry.findtext("atom:content", "", ns) or entry.findtext("atom:summary", "", ns)
        published = entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns)
        author = entry.findtext("atom:author/atom:name", "", ns)

        items.append({
            "title": clean_html(title),
            "url": link,
            "content": clean_html(content)[:500],
            "published": published,
            "author": author,
        })

    # Try RSS 2.0
    if not items:
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            author = item.findtext("author", "") or item.findtext("dc:creator", "")

            items.append({
                "title": clean_html(title),
                "url": link,
                "content": clean_html(description)[:500],
                "published": pub_date,
                "author": author,
            })

    return items


def fetch_feed(name: str, url: str) -> list:
    """Fetch and parse an RSS/Atom feed."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode("utf-8", errors="replace")
        items = parse_atom_or_rss(xml_data)
        for item in items:
            item["source"] = name
            item["id"] = item.get("url", "") or f"{name}:{item.get('title', '')[:50]}"
        return items
    except Exception as e:
        print(f"  [!] {name} failed: {e}")
        return []


def score_item(item: dict) -> float:
    """Score an item for content-worthiness."""
    score = 0
    title = item.get("title", "").lower()
    content = item.get("content", "").lower()
    text = f"{title} {content}"

    # AI keywords
    ai_keywords = ["ai", "gpt", "claude", "llm", "machine learning", "deep learning",
                    "openai", "anthropic", "google", "nvidia", "transformer", "neural"]
    ai_hits = sum(1 for kw in ai_keywords if kw in text)
    score += min(ai_hits * 1.5, 5)

    # Finance keywords
    fin_keywords = ["invest", "stock", "portfolio", "return", "dividend", "etf",
                    "crypto", "bitcoin", "market", "trading", "fund", "wealth"]
    fin_hits = sum(1 for kw in fin_keywords if kw in text)
    score += min(fin_hits * 1.5, 5)

    # Content quality
    if len(item.get("content", "")) > 200:
        score += 1

    # Viral indicators
    viral = ["how to", "guide", "beginner", "explained", "vs", "best",
             "why", "secret", "mistake", "surprising"]
    score += sum(1 for v in viral if v in title) * 1.5

    return round(score, 1)


def load_processed() -> set:
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()


def save_processed(ids: set):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    recent = sorted(ids)[-3000:]
    PROCESSED_FILE.write_text(json.dumps(recent, indent=2))


def generate_digest(all_items: list) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    # Score and sort
    for item in all_items:
        item["content_score"] = score_item(item)

    top = sorted(all_items, key=lambda x: x["content_score"], reverse=True)[:25]

    # Categorize
    ai_items = [i for i in top if any(kw in (i["title"] + i["content"]).lower()
                for kw in ["ai", "gpt", "llm", "machine learning", "claude", "openai", "nvidia"])]
    fin_items = [i for i in top if any(kw in (i["title"] + i["content"]).lower()
                for kw in ["invest", "stock", "crypto", "market", "trading", "fund", "portfolio"])]

    md = f"""---
date: {today}
source: rss-feeds
type: content-source
tags: [content-engine, rss, daily-digest]
---

# RSS Daily Digest — {today}

> Reddit + Tech blogs + Finance news에서 자동 수집.
> Content Score 기준 상위 25개 선별.

## AI / Tech ({len(ai_items)}개)

"""
    for i in ai_items[:12]:
        md += f"### [{i['title']}]({i['url']})\n"
        md += f"- **{i['source']}** | Score: {i['content_score']}\n"
        if i["content"]:
            md += f"- {i['content'][:200]}...\n"
        md += f"- **콘텐츠 각도:** (자기 시각 추가)\n\n"

    md += f"\n## 투자 / 금융 ({len(fin_items)}개)\n\n"
    for i in fin_items[:12]:
        md += f"### [{i['title']}]({i['url']})\n"
        md += f"- **{i['source']}** | Score: {i['content_score']}\n"
        if i["content"]:
            md += f"- {i['content'][:200]}...\n"
        md += f"- **콘텐츠 각도:** (자기 시각 추가)\n\n"

    md += f"""
---
## 사용법
1. 주제 선택 → `/xhs-draft [주제]` 또는 `/ig-draft [주제]`
2. 또는 `/content [주제]` → 전 플랫폼 동시 생성

## 통계
- 수집 시각: {datetime.now().strftime("%H:%M")}
- 피드 수: {len(FEEDS)}
- 총 수집: {len(all_items)}개
- AI/Tech: {len(ai_items)}개
- 투자/금융: {len(fin_items)}개
"""
    return md


def main():
    print(f"[HiOS Content Engine] RSS Collector — {len(FEEDS)} feeds")
    processed = load_processed()
    all_items = []

    for name, url in FEEDS.items():
        print(f"  Fetching {name}...")
        items = fetch_feed(name, url)
        new_items = [i for i in items if i["id"] not in processed]
        all_items.extend(new_items)
        for i in items:
            processed.add(i["id"])
        print(f"    → {len(new_items)} new / {len(items)} total")

    if not all_items:
        print("[!] No new items found.")
        return

    digest = generate_digest(all_items)
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = SOURCES_DIR / f"{today}-rss-digest.md"
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest)

    raw_path = SOURCES_DIR / f"{today}-rss-raw.json"
    raw_path.write_text(json.dumps(all_items, indent=2, ensure_ascii=False))

    save_processed(processed)

    print(f"\n[OK] Digest: {output_path}")
    print(f"[OK] {len(all_items)} new items collected")


if __name__ == "__main__":
    main()
