"""Reddit AI Scout — keyword -> Reddit research -> 10 blog topic ideas (Markdown).

OpenAI is required: the query is optimized, Reddit is scraped, then OpenAI turns
the real discussions into blog topic ideas. Output is a Markdown file.
"""
import argparse
import re
import sys
from pathlib import Path

from src import reddit_client, openai_client
from src.config import OPENAI_API_KEY

RESULT_DIR = Path(".previous")


def _slugify(text: str) -> str:
    """Build a filesystem-safe slug from text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[\s]+", "_", slug)
    return slug or "query"


def build_markdown(keyword: str, query: str, topics: list[dict], posts: list[dict]) -> str:
    """Render the blog topics (and source posts) as a Markdown document."""
    lines = [
        f"# Blog Topic Ideas: {keyword}",
        "",
        f"_Optimized query: `{query}` — {len(topics)} ideas from Reddit discussions._",
        "",
        "## Topics",
        "",
    ]
    for i, t in enumerate(topics, 1):
        lines.append(f"### {i}. {t['title']}")
        lines.append("")
        lines.append(t["description"])
        lines.append("")

    lines.append("## Sources (Reddit)")
    lines.append("")
    for p in posts:
        lines.append(f"- [{p['title']}]({p['url']}) — r/{p['subreddit']} ({p['score']} pts)")
    lines.append("")
    return "\n".join(lines)


def save_markdown(keyword: str, content: str) -> Path:
    """Write the result to .previous/<keyword>.md."""
    RESULT_DIR.mkdir(exist_ok=True)
    path = RESULT_DIR / f"{_slugify(keyword)}.md"
    path.write_text(content, encoding="utf-8")
    return path


def build_raw_markdown(keyword: str, query: str, subreddits: list[dict], posts: list[dict]) -> str:
    """Render raw Reddit research (no AI) as Markdown for an external LLM to use."""
    lines = [
        f"# Reddit Research: {keyword}",
        "",
        f"_Query: `{query}` — {len(posts)} posts across {len(subreddits)} subreddits. "
        "No AI applied; topic ideas are generated downstream._",
        "",
        "## Posts",
        "",
    ]
    for p in posts:
        lines.append(f"- [{p['title']}]({p['url']}) — r/{p['subreddit']} ({p['score']} pts)")
    lines.append("")
    lines.append("## Subreddits")
    lines.append("")
    for s in subreddits:
        subs = s.get("subscribers")
        desc = s.get("description") or ""
        lines.append(f"- r/{s['name']} ({subs} subs) — {desc}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reddit AI Scout — keyword -> 10 blog topic ideas (Markdown)"
    )
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--limit", type=int, default=10, help="Number of Reddit results")
    parser.add_argument(
        "--topics", type=int, default=10, help="Number of blog topic ideas"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Reddit-only mode: no OpenAI. Fetch posts and dump them so an "
        "external LLM (e.g. Claude) does query expansion + topic generation.",
    )
    args = parser.parse_args()

    # --raw: skip OpenAI entirely. The keyword is used directly as the query.
    if args.raw:
        query = args.keyword
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
        if not posts:
            print("[error] No Reddit posts found.", file=sys.stderr)
            sys.exit(1)
        md = build_raw_markdown(args.keyword, query, subreddits, posts)
        path = save_markdown(args.keyword, md)
        print(f"[reddit] {len(posts)} posts across {len(subreddits)} subreddits")
        print(f"[saved] {path}")
        return

    # OpenAI is required for the default (AI) mode.
    if not OPENAI_API_KEY:
        print(
            "[error] OPENAI_API_KEY missing. Copy .env.example to .env and add your key.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Optimize the keyword into a better Reddit query.
    query = openai_client.expand_query(args.keyword)
    print(f"[OpenAI] Optimized query: {query}\n")

    # Fetch Reddit data (single headed browser session).
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

    if not posts:
        print("[error] No Reddit posts found — cannot generate topics.", file=sys.stderr)
        sys.exit(1)

    print(f"[reddit] {len(posts)} posts across {len(subreddits)} subreddits\n")

    # Generate blog topic ideas from the real discussions.
    print(f"[OpenAI] Generating {args.topics} blog topics...\n")
    topics = openai_client.generate_blog_topics(args.keyword, posts, count=args.topics)

    print("=== Blog Topics ===")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t['title']}\n     {t['description']}")

    # Write Markdown output.
    md = build_markdown(args.keyword, query, topics, posts)
    path = save_markdown(args.keyword, md)
    print(f"\n[saved] {path}")


if __name__ == "__main__":
    main()
