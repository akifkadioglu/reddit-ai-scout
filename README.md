# reddit-blog-scout

Mine Reddit discussions for blog topic ideas. Give it a keyword, get the real posts and
subreddits back as Markdown, then feed that into SEO-focused blog topic discovery. Pure
JavaScript (npm package). It beats Reddit's 403 anti-bot wall by harvesting a guest cookie
with headless Chrome once, then making fast plain `fetch` requests with that cookie.

Two ways to use it:

1. **`/generate-blog` (Claude Code command — the main path)** — end-to-end and interactive: Reddit research → topic pick → full SEO blog + images. **No OpenAI** (Claude does query + topic generation). Needs `GEMINI_API_KEY` for images.
2. **`reddit-scout` (standalone CLI / library)** — just scrapes Reddit and writes the raw posts + subreddits to `.previous/<keyword>.md`. No AI, no keys.

## Install

```bash
npm i -D reddit-blog-scout   # installs puppeteer + stealth + bundled Chromium
```

Requires Node >= 20.6 (uses `process.loadEnvFile` for `.env`).

## CLI

```bash
npx reddit-scout "instagram dm automation"          # writes .previous/<keyword>.md
npx reddit-scout "bitcoin trading" --limit 15
npx reddit-scout "bitcoin trading" --deep 3          # also pull the 3 top posts' bodies + comments
```

Flags:

| Flag        | Description                                                              | Default |
|-------------|--------------------------------------------------------------------------|---------|
| `--limit N` | Number of posts / subreddits to fetch.                                   | `10`    |
| `--deep N`  | Deep mode: also fetch the body (selftext) + top comments of the `N` highest-scoring posts. `0` = surface only (titles/scores). | `0`     |

Output `.previous/<keyword>.md`:

```
# Reddit Research: <keyword>

_Query: `<query>` — N posts across M subreddits. No AI applied; topic ideas are generated downstream._

## Posts
- [title](url) — r/subreddit (score pts)
...

## Subreddits
- r/name (subscribers subs) — description
...
```

With `--deep N`, a **Deep Dive** section is appended below (the sections above are unchanged):

```
## Deep Dive (post bodies + top comments)

### <title> — r/<subreddit> (<score> pts)
<url>

<post body / selftext>

**Top comments:**
- (<score>) <comment body>
- ...
```

Deep mode is best-effort: if a single thread is blocked, that post falls back to an empty
body / no comments instead of failing the whole run.

## Programmatic use (devDependency)

```js
import { search } from "reddit-blog-scout";

const { subreddits, posts, threads } = await search("instagram dm automation", 10, 3);
// posts:      [{ title, subreddit, score, url, numComments, upvoteRatio, permalink }, ...]
// subreddits: [{ name, subscribers, description }, ...]
// threads:    [{ title, subreddit, score, url, selftext, comments: [{ body, score }] }, ...]
//             (the 3rd arg is `deep`; 0/omitted -> threads is [])
```

On the first call the cookie is harvested with headless Chrome and cached; later calls
return straight from the cache over plain fetch (no browser launch).

## `.env` variables

| Variable               | Description                                      | Required             | Default          |
|------------------------|--------------------------------------------------|----------------------|------------------|
| `GEMINI_API_KEY`       | Image generation — `/generate-blog` image step   | Yes for images       | —                |
| `IMG_ASPECT`           | Image aspect ratio                               | Optional             | `16:9`           |
| `IMG_WIDTH`            | Image width (px, via macOS `sips`)               | Optional             | `1200`           |
| `IMG_HEIGHT`           | Image height (px, via macOS `sips`)              | Optional             | `630`            |
| `REDDIT_COOKIE_TTL_MS` | Guest-cookie cache lifetime (ms)                 | Optional             | `21600000` (6h)  |

## The `/generate-blog` command (main path)

`/generate-blog` is a **Claude Code command**; it is NOT shipped inside the npm package
(`npm i` only pulls the CLI + library). To use it, copy the command file from this repo into
your own project:

```bash
# 1) Install the CLI as a devDependency (ships reddit-scout + blog-image)
npm i -D reddit-blog-scout

# 2) Drop the command file into your project's .claude/commands/
mkdir -p .claude/commands
curl -o .claude/commands/generate-blog.md \
  https://raw.githubusercontent.com/akifkadioglu/reddit-ai-scout/main/.claude/commands/generate-blog.md
# (or copy .claude/commands/generate-blog.md from this repo by hand)

# 3) Key for images
echo "GEMINI_API_KEY=..." >> .env
```

Then fill in the `──── CONFIG ────` block at the top of that file (brand, author pool,
category whitelist, image style, tone, paths) — everything below it is generic and reads
those values. Now, inside Claude Code:

```
/generate-blog <locale> <keyword>     # locale optional, defaults to en
```

1. **Research** — Claude turns the keyword into a Reddit query and pulls posts via `npx reddit-scout "<query>"`.
2. **Pick a topic** — it offers 4 blog topics from the real discussions; pick with arrow keys or type your own.
3. **Additions** — it asks "anything to add?" (angle, audience, tone, length…).
4. **Generate** — it writes the full SEO blog post to `content/blog/<locale>/<slug>.md`.
5. **Images** — Claude generates the cover + in-content images directly via `npx blog-image` (`GEMINI_API_KEY`).

## How it reaches Reddit

Reddit blocks plain HTTP with a **403** on most IPs (both stdlib `urllib` and node `fetch`).
This tool gets past that in two steps:

1. **Cookie harvest (headless Chrome).** Once, headless Chrome (Puppeteer + stealth) visits reddit.com and harvests the **guest cookie** via `page.cookies()` (including httpOnly cookies). The cookie is cached in the OS cache dir (`~/.cache/reddit-blog-scout/cookie.json`, `%LOCALAPPDATA%` on Windows), so the consumer's repo stays clean.
2. **Requests (plain fetch).** Every later search is a plain `fetch` with the cookie header and the same Chrome UA — no browser launch, so it's fast. Once the cookie goes stale past `REDDIT_COOKIE_TTL_MS` (default 6h) it is re-harvested automatically.

> **Note:** Reddit blocks the `HeadlessChrome` UA, so both the harvest and the fetch use the same normal Chrome UA (a UA mismatch is itself a 403 trigger).

If a request is blocked (an HTML wall instead of JSON), the cookie is force-refreshed **once**
and retried. On anti-bot **flagged IPs** (datacenter / VPN) the guest cookie may still not be
enough — in that case you get a clear error; try a clean network (there is no interactive
login fallback).

## Image CLI (blog-image)

`/generate-blog` calls this for every image; you can also run it by hand:

```bash
PROMPT='bright modern home office, no text, no logos' \
OUT='public/images/blogs/my-post/cover.jpg' \
npx blog-image
```

It generates with Gemini `gemini-2.5-flash-image` (Nano Banana) and skips if `OUT` already
exists (idempotent). On macOS it resizes to exact pixels via `sips`; elsewhere it stays at
the API aspect ratio.

## Layout

```
reddit-blog-scout/
├── .claude/commands/
│   └── generate-blog.md       # /generate-blog command (CONFIG + rules)
├── bin/
│   ├── reddit-scout.js         # CLI: research
│   └── blog-image.js           # CLI: Gemini image generation
├── src/
│   ├── cookie.js               # Guest-cookie harvest (headless) + OS cache
│   ├── reddit.js               # Reddit search (plain fetch + cookie)
│   └── markdown.js             # Markdown render + .previous/ output
├── .previous/                  # reddit-scout output (<keyword>.md)
├── package.json
└── .env.example
```

## Notes

- The Reddit cookie is harvested once with a headless browser (Puppeteer), then requests are plain fetch — no OAuth/API key. `npm i` also downloads Chromium.
- `/generate-blog` needs **no OpenAI**; Claude does query + topic generation.
- Image generation needs `GEMINI_API_KEY`; without it `blog-image` warns.
- The cookie cache lives in the OS cache dir, not the consumer's repo; `.env` is git-ignored.

## License

MIT © Akif
