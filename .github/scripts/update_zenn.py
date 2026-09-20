#!/usr/bin/env python3
"""Regenerate the Zenn article list in README.md between the marker comments.

Stdlib only. Exits non-zero (without writing) when the feed is empty or the
markers are missing, so the workflow never commits a broken README.
"""
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED_URL = "https://zenn.dev/midomo/feed"
README = Path(__file__).resolve().parents[2] / "README.md"
START = "<!-- ZENN-ARTICLES:START -->"
END = "<!-- ZENN-ARTICLES:END -->"
MAX_ITEMS = 8


def local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def fetch_latest_articles() -> list[tuple[str, str]]:
    req = urllib.request.Request(
        FEED_URL, headers={"User-Agent": "profile-readme-updater/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        tree = ET.fromstring(res.read())
    articles = []
    for item in (e for e in tree.iter() if local_name(e.tag) == "item"):
        def text(tag: str) -> str:
            el = next((c for c in item if local_name(c.tag) == tag), None)
            return (el.text or "").strip() if el is not None else ""
        title, link = text("title"), text("link") or text("guid")
        if title and link:
            articles.append((title, link))
    return articles[:MAX_ITEMS]


def main() -> None:
    articles = fetch_latest_articles()
    if not articles:
        sys.exit("no articles found in feed; aborting without changes")
    listing = "\n".join(f"- [{t}]({u})" for t, u in articles)

    content = README.read_text(encoding="utf-8")
    if START not in content or END not in content:
        sys.exit("ZENN-ARTICLES markers not found in README.md")
    start_i = content.index(START) + len(START)
    end_i = content.index(END)
    README.write_text(
        content[:start_i] + "\n" + listing + "\n" + content[end_i:],
        encoding="utf-8",
    )
    print(f"article list updated: {len(articles)} items")


if __name__ == "__main__":
    main()
