"""Çevre değişkenlerini .env'den yükler."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Browser görünür mü? Blok yersen REDDIT_HEADLESS=0 dene (gerçek pencere açar)
REDDIT_HEADLESS = os.getenv("REDDIT_HEADLESS", "1") not in ("0", "false", "False")


def require_openai_key() -> str:
    """Raise a clear error if the OpenAI key is missing."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY missing in .env. Copy .env.example and fill it in."
        )
    return OPENAI_API_KEY
