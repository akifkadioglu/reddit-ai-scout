"""Çevre değişkenlerini .env'den yükler."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Kalıcı browser profili — bir kere login olunca cookie burada saklanır
REDDIT_PROFILE_DIR = os.getenv("REDDIT_PROFILE_DIR", ".reddit_profile")

# Hangi yerel tarayıcıdan Reddit cookie'si okunacak (chrome/brave/edge/firefox/safari)
REDDIT_COOKIE_BROWSER = os.getenv("REDDIT_COOKIE_BROWSER", "chrome")
# Cookie'leri hangi domain için okuyalım
REDDIT_COOKIE_DOMAIN = os.getenv("REDDIT_COOKIE_DOMAIN", "reddit.com")

# Çıktı (blog konuları) hangi dilde üretilsin — locale kodu, örn: en_US, tr_TR
OUTPUT_LANG = os.getenv("OUTPUT_LANG", "en_US")


def require_openai_key() -> str:
    """Raise a clear error if the OpenAI key is missing."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY missing in .env. Copy .env.example and fill it in."
        )
    return OPENAI_API_KEY
