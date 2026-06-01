"""Reddit scraper via a real browser (Playwright) with a persistent profile.

Reddit blocks plain HTTP scripts (403). A real browser works: we first visit a
normal Reddit page so a guest cookie is set, then read the .json endpoints. No
login or OAuth needed. The cookie persists in REDDIT_PROFILE_DIR across runs.

When the IP is anti-bot blocked, guest traffic gets an HTML block page instead
of JSON. To pass it, we auto-read your logged-in Reddit cookies from your local
browser (REDDIT_COOKIE_BROWSER) and inject them into the context — no `make
login` needed. If that read fails, we fall back to guest mode.
"""
import json
import sys
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from .config import REDDIT_COOKIE_BROWSER, REDDIT_COOKIE_DOMAIN, REDDIT_PROFILE_DIR

BASE_URL = "https://www.reddit.com"
# Sirayla denenecek host'lar — biri bloklarsa digerine gec
HOSTS = ["https://www.reddit.com", "https://old.reddit.com"]

# Headless Chrome'un UA'sinda "HeadlessChrome" gecer -> Reddit blokluyor.
# Normal Chrome UA'si ile maskele ki headless'da da 403 yemeyelim.
_REAL_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def load_browser_cookies() -> list[dict]:
    """Yerel tarayıcıdan Reddit cookie'lerini oku, Playwright formatına çevir.

    Hata olursa (paket yok / okuma izni yok) misafir moda düş: uyarı bas, [] dön.
    """
    try:
        import browser_cookie3

        loader = getattr(browser_cookie3, REDDIT_COOKIE_BROWSER, browser_cookie3.chrome)
        jar = loader(domain_name=REDDIT_COOKIE_DOMAIN)

        cookies = []
        for c in jar:
            cookie = {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path or "/",
                "secure": bool(c.secure),
                "sameSite": "Lax",
            }
            if c.expires:
                cookie["expires"] = int(c.expires)
            cookies.append(cookie)
        return cookies
    except Exception as e:
        print(
            f"[cookies] could not read {REDDIT_COOKIE_BROWSER} cookies ({e}); "
            "falling back to guest mode.",
            file=sys.stderr,
        )
        return []


def open_context(p, headless: bool = True):
    """Kalıcı profille bir browser context aç. Gerçek Chrome > paketli chromium.

    UA maskesi + automation flag kapatma sayesinde headless'da da Reddit blok yemez.
    """
    common = {
        "user_agent": _REAL_UA,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    for kwargs in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch_persistent_context(
                REDDIT_PROFILE_DIR, headless=headless, **common, **kwargs
            )
        except Exception:
            continue
    raise RuntimeError("Could not launch a browser. Run: playwright install chromium")


def _fetch_one(page, path: str, params: dict) -> dict:
    """Bir endpoint'i host'lar arasinda dene; ilk JSON donen kazanir."""
    qs = urlencode(params)
    for host in HOSTS:
        # JSON URL'sine dogrudan git; Chrome ham JSON'u <pre> icinde gosterir
        page.goto(f"{host}{path}.json?{qs}", wait_until="domcontentloaded", timeout=20000)
        text = page.evaluate("() => document.body.innerText")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue  # blok sayfasi -> sonraki host
    raise RuntimeError(
        "All Reddit hosts returned a block page. Confirm you're logged into "
        f"Reddit in {REDDIT_COOKIE_BROWSER} (REDDIT_COOKIE_BROWSER). "
        "Last resort: `make login` or a different network/VPN."
    )


def _fetch_endpoints(paths_params: list[tuple[str, dict]]) -> list[dict]:
    """Tek browser oturumunda birden çok .json endpoint çek."""
    results: list[dict] = []
    with sync_playwright() as p:
        # UA maskesi sayesinde headless'da da blok yemiyoruz -> pencere acilmaz
        ctx = open_context(p, headless=True)
        # Logged-in cookie'leri yerel tarayıcıdan enjekte et -> block'u gec
        cookies = load_browser_cookies()
        if cookies:
            ctx.add_cookies(cookies)
            print(
                f"[cookies] loaded {len(cookies)} reddit cookies "
                f"from {REDDIT_COOKIE_BROWSER}"
            )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # Once normal HTML sayfasina ugra -> misafir cookie olussun
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        for path, params in paths_params:
            results.append(_fetch_one(page, path, params))
        ctx.close()
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
