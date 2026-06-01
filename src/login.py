"""One-time Reddit login. Opens a visible browser; you log in by hand.

The session cookie is saved into the persistent profile (REDDIT_PROFILE_DIR),
so later `make run` calls reuse your logged-in session. Run with: make login
"""
from playwright.sync_api import sync_playwright

from . import reddit_client


def main() -> None:
    print("Opening a browser. Log in to Reddit, then come back here.")
    with sync_playwright() as p:
        # Login icin her zaman gorunur pencere
        ctx = reddit_client.open_context(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
        input("After you are logged in, press Enter here to save the session...")
        ctx.close()
    print("Session saved. You can now run: make run q=\"...\"")


if __name__ == "__main__":
    main()
