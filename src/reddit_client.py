"""Reddit public JSON API istemcisi (OAuth gerektirmez)."""
import requests

from .config import REDDIT_USER_AGENT

BASE_URL = "https://www.reddit.com"


def search_subreddits(query: str, limit: int = 10) -> list[dict]:
    """search_subreddits.json endpoint'i ile subreddit ara.

    Args:
        query: Aranacak kelime.
        limit: Maks sonuç sayısı.

    Returns:
        Subreddit dict listesi (name, subscribers, description).
    """
    url = f"{BASE_URL}/api/search_subreddits.json"
    headers = {"User-Agent": REDDIT_USER_AGENT}
    data = {"query": query, "limit": limit}

    resp = requests.post(url, headers=headers, data=data, timeout=10)
    resp.raise_for_status()

    subreddits = resp.json().get("subreddits", [])
    return [
        {
            "name": s.get("name"),
            "subscribers": s.get("subscriber_count"),
            "description": s.get("description", "").strip(),
        }
        for s in subreddits
    ]


def search_posts(query: str, limit: int = 10) -> list[dict]:
    """Tüm Reddit'te gönderi ara (search.json)."""
    url = f"{BASE_URL}/search.json"
    headers = {"User-Agent": REDDIT_USER_AGENT}
    params = {"q": query, "limit": limit, "sort": "relevance"}

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()

    children = resp.json().get("data", {}).get("children", [])
    return [
        {
            "title": c["data"].get("title"),
            "subreddit": c["data"].get("subreddit"),
            "score": c["data"].get("score"),
            "url": f"{BASE_URL}{c['data'].get('permalink', '')}",
        }
        for c in children
    ]
