// Reddit search over plain `fetch`, authenticated with a harvested guest cookie.
//
// Reddit blocks plain HTTP (403) for unauthenticated clients, but a guest cookie taken
// from a real browser session gets through on clean IPs. src/cookie.js harvests that
// cookie once (headless Chrome) and caches it; here we just replay it as a Cookie header
// with the matching UA — no browser per request, so searches are fast.
//
// If a request is blocked (HTML wall instead of JSON), we re-harvest the cookie once and
// retry. Anti-bot-flagged IPs (datacenter / VPN) may still get blocked — there is no
// interactive login fallback by design; use a clean network in that case.
import { getCookie, REAL_UA } from "./cookie.js";

const BASE_URL = "https://www.reddit.com";
// Hosts tried in order — if one serves a block page, fall through to the next.
const HOSTS = ["https://www.reddit.com", "https://old.reddit.com"];

/** Fetch one endpoint across hosts with the given cookie; first host returning JSON wins. */
async function fetchOne(path, params, cookie) {
  const qs = new URLSearchParams(params).toString();
  for (const host of HOSTS) {
    let text;
    try {
      const resp = await fetch(`${host}${path}.json?${qs}`, {
        headers: { Cookie: cookie, "User-Agent": REAL_UA, Accept: "application/json" },
      });
      text = await resp.text();
    } catch {
      continue; // network error on this host -> try the next
    }
    try {
      return JSON.parse(text);
    } catch {
      continue; // block page (HTML) -> next host
    }
  }
  return null; // all hosts blocked with this cookie
}

/**
 * Fetch multiple .json endpoints with one cookie. If any endpoint is blocked, re-harvest
 * the cookie once and retry the whole set before giving up.
 */
async function fetchEndpoints(pathsParams) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const { cookie } = await getCookie({ force: attempt > 0 });
    const results = [];
    let blocked = false;
    for (const [path, params] of pathsParams) {
      const r = await fetchOne(path, params, cookie);
      if (r === null) {
        blocked = true;
        break;
      }
      results.push(r);
    }
    if (!blocked) return results;
  }
  throw new Error(
    "All Reddit hosts returned a block page even after refreshing the guest cookie. " +
      "This IP looks anti-bot flagged by Reddit (common on datacenter / VPN IPs). " +
      "Try a different network."
  );
}

/**
 * Search subreddits and posts in one pass.
 * @returns {Promise<{subreddits: object[], posts: object[]}>}
 */
export async function search(query, limit = 10) {
  const [subRaw, postRaw] = await fetchEndpoints([
    ["/subreddits/search", { q: query, limit }],
    ["/search", { q: query, limit, sort: "relevance" }],
  ]);

  const subreddits = (subRaw?.data?.children || []).map((c) => ({
    name: c.data?.display_name,
    subscribers: c.data?.subscribers,
    description: (c.data?.public_description || "").trim(),
  }));
  const posts = (postRaw?.data?.children || []).map((c) => ({
    title: c.data?.title,
    subreddit: c.data?.subreddit,
    score: c.data?.score,
    url: `${BASE_URL}${c.data?.permalink || ""}`,
  }));
  return { subreddits, posts };
}
