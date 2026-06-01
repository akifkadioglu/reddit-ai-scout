"""Reddit scraper via a real browser (Playwright).

Reddit blocks plain HTTP scripts (403). A real browser context gets a guest
session cookie, so navigating to the .json endpoints works without OAuth.
Uses installed Google Chrome when available (channel="chrome") — far less
likely to be flagged than the bundled headless shell.
"""
import json
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from .config import REDDIT_HEADLESS

BASE_URL = "https://www.reddit.com"


def _launch(p):
    """Önce gerçek Chrome'u dene, yoksa paketli chromium'a düş."""
    for kwargs in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(headless=REDDIT_HEADLESS, **kwargs)
        except Exception:
            continue
    raise RuntimeError("Could not launch a browser. Run: python -m playwright install chromium")


def _parse_json(text: str) -> dict:
    """Body metnini JSON'a çevir; blok sayfasıysa net hata ver."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(
            "Reddit returned a non-JSON page (likely a network/bot block). "
            "Try REDDIT_HEADLESS=0 in .env, or use a different network."
        )


def _fetch_endpoints(paths_params: list[tuple[str, dict]]) -> list[dict]:
    """Tek browser oturumunda birden çok .json endpoint çek."""
    results: list[dict] = []
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_context().new_page()
        # Önce reddit.com'a gir -> guest session cookie al
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        for path, params in paths_params:
            url = f"{BASE_URL}{path}.json?{urlencode(params)}"
            # JSON URL'sine dogrudan git; Chrome ham JSON'u <pre> icinde gosterir
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            results.append(_parse_json(page.evaluate("() => document.body.innerText")))
        browser.close()
    return results


def search(query: str, limit: int = 10) -> tuple[list[dict], list[dict]]:
    """Subreddit ve gönderileri tek oturumda ara.

    Returns:
        (subreddits, posts) tuple'ı.
    """
    sub_raw, post_raw = _fetch_endpoints(
        [
            ("/subreddits/search", {"q": query, "limit": limit}),
            ("/search", {"q": query, "limit": limit, "sort": "relevance"}),
        ]
    )

    subreddits = [
        {
            "name": c["data"].get("display_name"),
            "subscribers": c["data"].get("subscribers"),
            "description": (c["data"].get("public_description") or "").strip(),
        }
        for c in sub_raw.get("data", {}).get("children", [])
    ]
    posts = [
        {
            "title": c["data"].get("title"),
            "subreddit": c["data"].get("subreddit"),
            "score": c["data"].get("score"),
            "url": f"{BASE_URL}{c['data'].get('permalink', '')}",
        }
        for c in post_raw.get("data", {}).get("children", [])
    ]
    return subreddits, posts
