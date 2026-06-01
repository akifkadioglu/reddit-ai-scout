#!/usr/bin/env node
// CLI: reddit-scout "<query>" [--limit N]
// Output is byte-compatible with the old Python CLI.
import { existsSync } from "node:fs";
import { search } from "../src/reddit.js";
import { buildRawMarkdown, saveMarkdown } from "../src/markdown.js";

// Load .env if present (Node >=20.6 has process.loadEnvFile; no dep needed).
if (existsSync(".env") && typeof process.loadEnvFile === "function") {
  try {
    process.loadEnvFile(".env");
  } catch {
    /* ignore malformed .env */
  }
}

function parseArgs(argv) {
  const out = { _: [], limit: 10 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--limit") {
      out.limit = parseInt(argv[++i], 10) || 10;
    } else if (a.startsWith("--limit=")) {
      out.limit = parseInt(a.split("=")[1], 10) || 10;
    } else {
      out._.push(a);
    }
  }
  return out;
}

async function main() {
  const argv = process.argv.slice(2);

  const args = parseArgs(argv);
  const keyword = args._[0];
  if (!keyword) {
    console.error('usage: reddit-scout "<query>" [--limit N]');
    process.exit(1);
  }

  // --raw semantics: the keyword is used directly as the query (no AI expansion).
  const query = keyword;
  let result;
  try {
    result = await search(query, args.limit);
  } catch (e) {
    console.error(`\n[error] Reddit fetch failed: ${e.message}`);
    process.exit(1);
  }

  const { subreddits, posts } = result;
  if (!posts.length) {
    console.error("[error] No Reddit posts found.");
    process.exit(1);
  }

  const md = buildRawMarkdown(keyword, query, subreddits, posts);
  const path = saveMarkdown(keyword, md);
  console.log(`[reddit] ${posts.length} posts across ${subreddits.length} subreddits`);
  console.log(`[saved] ${path}`);
}

main().catch((e) => {
  console.error(`\n[error] ${e?.stack || e}`);
  process.exit(1);
});
