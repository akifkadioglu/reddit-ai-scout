"""Çevre değişkenlerini .env'den yükler."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-ai-scout/0.1")


def require_openai_key() -> str:
    """OpenAI anahtarı yoksa net hata fırlat."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            ".env içinde OPENAI_API_KEY yok. .env.example'ı kopyala ve doldur."
        )
    return OPENAI_API_KEY
