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
 * Deep pass: pull each post's body (selftext) + top comments from its `<permalink>.json`.
 * Reuses the same cookie/host-fallback path as search. Best-effort: if the batch is blocked,
 * every post degrades to an empty thread instead of failing the whole run.
 * @returns {Promise<object[]>} one thread per input post (same order)
 */
async function fetchThreads(posts, commentLimit = 8) {
  const empty = posts.map((p) => ({
    title: p.title,
    subreddit: p.subreddit,
    score: p.score,
    url: p.url,
    selftext: "",
    comments: [],
  }));
  if (!posts.length) return empty;

  let raws;
  try {
    raws = await fetchEndpoints(
      posts.map((p) => [
        // `/r/x/comments/abc/title/` -> `/r/x/comments/abc/title` (fetchOne appends `.json`).
        p.permalink.replace(/\/$/, ""),
        { limit: commentLimit, sort: "top", raw_json: 1 },
      ])
    );
  } catch {
    return empty; // blocked on the deep pass — keep the surface results we already have
  }

  return posts.map((p, i) => {
    const raw = raws[i];
    const selftext = (raw?.[0]?.data?.children?.[0]?.data?.selftext || "").trim();
    const comments = (raw?.[1]?.data?.children || [])
      .filter((c) => c.kind === "t1" && c.data?.body)
      .slice(0, commentLimit)
      .map((c) => ({ body: c.data.body.trim(), score: c.data.score ?? 0 }));
    return { title: p.title, subreddit: p.subreddit, score: p.score, url: p.url, selftext, comments };
  });
}

/**
 * Search subreddits and posts in one pass. When `deep > 0`, also fetch the body + top
 * comments of the `deep` highest-scoring posts (returned as `threads`).
 * @param {string} query
 * @param {number} limit
 * @param {number} deep number of top posts to deep-fetch (0 = surface only, back-compat)
 * @returns {Promise<{subreddits: object[], posts: object[], threads: object[]}>}
 */
export async function search(query, limit = 10, deep = 0) {
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
    numComments: c.data?.num_comments,
    upvoteRatio: c.data?.upvote_ratio,
    permalink: c.data?.permalink || "",
  }));

  let threads = [];
  if (deep > 0) {
    const top = [...posts].sort((a, b) => (b.score ?? 0) - (a.score ?? 0)).slice(0, deep);
    threads = await fetchThreads(top);
  }

  return { subreddits, posts, threads };
}
