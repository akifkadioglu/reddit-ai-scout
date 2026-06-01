"""OpenAI API client — expands and summarizes search queries."""
from openai import OpenAI

from .config import require_openai_key, OPENAI_MODEL


def _get_client() -> OpenAI:
    """Initialize the OpenAI client with the API key."""
    return OpenAI(api_key=require_openai_key())


def expand_query(keyword: str) -> str:
    """Turn the user's keyword into a better Reddit search query."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The user is searching for '{keyword}'. Produce a short, "
                    f"optimized keyword query for Reddit's own search. Use plain "
                    f"keywords only — no search operators like site:, quotes, or "
                    f"boolean. Return only the query, no explanation."
                ),
            }
        ],
    )
    return resp.choices[0].message.content.strip()


def summarize_results(keyword: str, posts: list[dict]) -> str:
    """Summarize Reddit results with OpenAI."""
    client = _get_client()
    titles = "\n".join(f"- {p['title']} (r/{p['subreddit']})" for p in posts)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The user is researching '{keyword}'. Write a short summary "
                    f"based on these Reddit post titles:\n\n{titles}"
                ),
            }
        ],
    )
    return resp.choices[0].message.content.strip()
