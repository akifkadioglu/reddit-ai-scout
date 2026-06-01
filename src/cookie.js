// Reddit guest-cookie harvest + on-disk cache.
//
// Reddit blocks plain HTTP (403) on most IPs, but a real browser visiting reddit.com
// gets a guest cookie that authenticates later requests. We harvest that cookie ONCE
// with headless Chrome (Puppeteer + stealth), cache it in the OS cache dir, then let
// src/reddit.js replay it over plain `fetch` — no browser per request.
//
// Note: `document.cookie` omits httpOnly cookies (Reddit's session token among them),
// so we read the full set via page.cookies() (CDP). A partial cookie still gets 403'd.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";

puppeteer.use(StealthPlugin());

// Headless Chrome's UA contains "HeadlessChrome" -> Reddit blocks it. Mask with a
// normal Chrome UA. The SAME UA must be used by both harvest and fetch — a mismatch
// between the cookie's origin UA and the request UA is itself a 403 trigger.
export const REAL_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";

// Guest tokens go stale; refresh past this age. Override with REDDIT_COOKIE_TTL_MS.
const DEFAULT_TTL_MS = 6 * 60 * 60 * 1000; // 6h

/** OS cache dir for the cached cookie. Keeps the consumer's repo clean. */
function cacheDir() {
  if (process.platform === "win32") {
    const base = process.env.LOCALAPPDATA || tmpdir();
    return join(base, "reddit-ai-scout");
  }
  const base = process.env.XDG_CACHE_HOME || join(homedir(), ".cache");
  return join(base, "reddit-ai-scout");
}

function cachePath() {
  return join(cacheDir(), "cookie.json");
}

function ttlMs() {
  const v = parseInt(process.env.REDDIT_COOKIE_TTL_MS || "", 10);
  return Number.isFinite(v) && v > 0 ? v : DEFAULT_TTL_MS;
}

/** Read a fresh cached cookie, or null if missing/stale/unreadable. */
function readCache() {
  try {
    const raw = readFileSync(cachePath(), "utf-8");
    const data = JSON.parse(raw);
    if (!data?.cookie || typeof data.ts !== "number") return null;
    if (Date.now() - data.ts > ttlMs()) return null;
    return { cookie: data.cookie, ua: data.ua || REAL_UA };
  } catch {
    return null;
  }
}

function writeCache(cookie) {
  try {
    mkdirSync(cacheDir(), { recursive: true });
    writeFileSync(cachePath(), JSON.stringify({ cookie, ua: REAL_UA, ts: Date.now() }), "utf-8");
  } catch {
    /* cache is best-effort; harvest still returns the cookie */
  }
}

/**
 * Launch a headless browser. Real Chrome channel > bundled chromium. Ephemeral profile
 * (no userDataDir) so nothing is written to the consumer's working directory.
 */
async function launch() {
  const common = { headless: true, args: ["--disable-blink-features=AutomationControlled"] };
  // Try the installed Chrome first, then puppeteer's bundled chromium.
  for (const extra of [{ channel: "chrome" }, {}]) {
    try {
      return await puppeteer.launch({ ...common, ...extra });
    } catch {
      continue;
    }
  }
  throw new Error("Could not launch a browser. Run: npx puppeteer browsers install chrome");
}

/** Harvest a fresh guest cookie via headless Chrome and cache it. */
async function harvest() {
  const browser = await launch();
  try {
    const pages = await browser.pages();
    const page = pages.length ? pages[0] : await browser.newPage();
    await page.setUserAgent(REAL_UA);
    // Visit a normal HTML page so Reddit sets the guest cookie(s). Wait for network idle:
    // domcontentloaded fires before Reddit's JS sets token_v2/loid/csv/session, leaving
    // only `edgebucket` — an incomplete cookie still gets 403'd on the .json endpoints.
    await page.goto("https://www.reddit.com", { waitUntil: "networkidle2", timeout: 30000 });
    // page.cookies() returns httpOnly cookies too (unlike document.cookie).
    const cookies = await page.cookies();
    const cookie = cookies
      .filter((c) => c.name && c.value)
      .map((c) => `${c.name}=${c.value}`)
      .join("; ");
    if (!cookie) throw new Error("harvested empty cookie set from reddit.com");
    writeCache(cookie);
    return { cookie, ua: REAL_UA };
  } finally {
    await browser.close();
  }
}

/**
 * Return a usable Reddit cookie + UA. Uses the fresh on-disk cache unless `force` is set
 * (callers pass force after a request is blocked, to re-harvest).
 * @returns {Promise<{cookie: string, ua: string}>}
 */
export async function getCookie({ force = false } = {}) {
  if (!force) {
    const cached = readCache();
    if (cached) return cached;
  }
  return harvest();
}

export const __test = { cacheDir, cachePath };
