"""Reddit AI Scout — fetches Reddit data for a keyword, enriched with OpenAI."""
import argparse
import json
import re
import sys
from pathlib import Path

from src import reddit_client, openai_client
from src.config import OPENAI_API_KEY

RESULT_DIR = Path("result")


def _slugify(text: str) -> str:
    """Build a filesystem-safe slug from text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[\s]+", "_", slug)
    return slug or "query"


def save_result(keyword: str, data: dict) -> Path:
    """Write the result to result/<keyword>.json."""
    RESULT_DIR.mkdir(exist_ok=True)
    path = RESULT_DIR / f"{_slugify(keyword)}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit AI Scout")
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--limit", type=int, default=10, help="Number of results")
    parser.add_argument(
        "--ai", action="store_true", help="Smart search + summary via OpenAI"
    )
    args = parser.parse_args()

    query = args.keyword

    # Expand the query with OpenAI (only if key is set and --ai is given)
    if args.ai and OPENAI_API_KEY:
        query = openai_client.expand_query(args.keyword)
        print(f"[OpenAI] Optimized query: {query}\n")
    elif args.ai:
        print("[Warning] OPENAI_API_KEY missing, running plain search.\n")

    # Fetch via headless browser (single session)
    try:
        subreddits, posts = reddit_client.search(query, args.limit)
    except Exception as e:
        print(f"\n[error] Reddit fetch failed: {e}", file=sys.stderr)
        print(
            "If this is the first run, install the browser with: "
            "python -m playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    print("=== Subreddits ===")
    for sub in subreddits:
        print(f"  r/{sub['name']} — {sub['subscribers']} subscribers")

    print("\n=== Posts ===")
    for p in posts:
        print(f"  [{p['score']}] {p['title']}\n      {p['url']}")

    # Collected data
    result = {
        "keyword": args.keyword,
        "query": query,
        "limit": args.limit,
        "subreddits": subreddits,
        "posts": posts,
        "summary": None,
    }

    # OpenAI summary
    if args.ai and OPENAI_API_KEY and posts:
        print("\n=== OpenAI Summary ===")
        summary = openai_client.summarize_results(args.keyword, posts)
        print(summary)
        result["summary"] = summary

    # Write to result/<keyword>.json
    path = save_result(args.keyword, result)
    print(f"\n[saved] {path}")


if __name__ == "__main__":
    main()
