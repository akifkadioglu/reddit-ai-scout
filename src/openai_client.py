"""OpenAI API client — expands and summarizes search queries."""
import json
import re

from openai import OpenAI

from .config import require_openai_key, OPENAI_MODEL, OUTPUT_LANG

# Locale kodu -> model'e verilecek dil adı
_LANG_NAMES = {
    "en_US": "English",
    "en_GB": "English",
    "tr_TR": "Turkish",
    "de_DE": "German",
    "fr_FR": "French",
    "es_ES": "Spanish",
    "it_IT": "Italian",
    "pt_PT": "Portuguese",
    "pt_BR": "Portuguese",
    "ar_SA": "Arabic",
    "ru_RU": "Russian",
}


def _lang_name(locale: str) -> str:
    """Locale kodunu dil adına çevir; bilinmiyorsa kodu olduğu gibi döndür."""
    return _LANG_NAMES.get(locale, locale)


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


def _extract_json(text: str) -> str:
    """Strip ```json fences if present, return raw JSON text."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    return fenced.group(1).strip() if fenced else text


def generate_blog_topics(
    keyword: str, posts: list[dict], count: int = 10
) -> list[dict]:
    """Generate `count` blog topic ideas (title + description) from Reddit posts.

    Returns a list of {"title": str, "description": str}.
    """
    client = _get_client()
    language = _lang_name(OUTPUT_LANG)
    titles = "\n".join(f"- {p['title']} (r/{p['subreddit']})" for p in posts)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are a content strategist. The user wants blog post ideas "
                    f"about '{keyword}'. Based on these real Reddit discussions "
                    f"(post titles), propose exactly {count} blog topic ideas that "
                    f"address the questions, pains, and interests people show.\n\n"
                    f"Reddit posts:\n{titles}\n\n"
                    f"Write every title and description in {language}. "
                    f"Return ONLY a JSON array of {count} objects, each with keys "
                    f'"title" (catchy blog title) and "description" (1-2 sentences '
                    f"on what the post covers and why it matters). No extra text."
                ),
            }
        ],
    )
    raw = _extract_json(resp.choices[0].message.content)
    data = json.loads(raw)
    # Normalize to a clean list of {title, description}
    topics = []
    for item in data:
        topics.append(
            {
                "title": str(item.get("title", "")).strip(),
                "description": str(item.get("description", "")).strip(),
            }
        )
    return topics
