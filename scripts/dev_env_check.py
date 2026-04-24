#!/usr/bin/env python3
"""Quick environment check for the m-trud audit repository."""

from __future__ import annotations

import argparse
import json
import urllib.parse
from collections import deque

import bs4
import requests


def run_check(base_url: str, max_pages: int, per_link_timeout: int) -> dict:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 env-check-bot"})

    seen: set[str] = set()
    queue: deque[str] = deque([base_url])
    checked_links: set[str] = set()
    broken_links: list[tuple[str, int]] = []

    while queue and len(seen) < max_pages:
        page_url = queue.popleft()
        if page_url in seen:
            continue

        response = session.get(page_url, timeout=20, allow_redirects=True)
        seen.add(page_url)

        if "text/html" not in response.headers.get("Content-Type", ""):
            continue

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        base_tag = soup.find("base", href=True)
        page_base = urllib.parse.urljoin(response.url, base_tag["href"]) if base_tag else response.url

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue

            absolute_url = urllib.parse.urljoin(page_base, href)
            parsed = urllib.parse.urlparse(absolute_url)
            if not parsed.netloc.endswith("m-trud.ru"):
                continue

            normalized_url = urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
            )

            if normalized_url not in seen and len(seen) + len(queue) < max_pages:
                queue.append(normalized_url)

            if normalized_url in checked_links:
                continue
            checked_links.add(normalized_url)

            link_response = session.get(normalized_url, timeout=per_link_timeout, allow_redirects=False)
            if link_response.status_code >= 400:
                broken_links.append((normalized_url, link_response.status_code))

    return {
        "pages_crawled": len(seen),
        "links_checked": len(checked_links),
        "broken_count": len(broken_links),
        "broken_sample": broken_links[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a lightweight environment sanity check.")
    parser.add_argument("--url", default="https://m-trud.ru/", help="Base URL to crawl")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum number of pages to scan")
    parser.add_argument("--link-timeout", type=int, default=15, help="Timeout for each link check (seconds)")
    args = parser.parse_args()

    result = run_check(args.url, args.max_pages, args.link_timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["broken_count"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
