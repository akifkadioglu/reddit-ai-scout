// Markdown rendering + file output. Port of main.py:_slugify / build_raw_markdown / save_markdown.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const RESULT_DIR = ".previous";

/** Build a filesystem-safe slug from text (mirror of main.py:_slugify). */
export function slugify(text) {
  let slug = text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "") // drop non-word chars (\w keeps a-z0-9_)
    .trim();
  slug = slug.replace(/\s+/g, "_");
  return slug || "query";
}

/**
 * Render raw Reddit research (no AI) as Markdown for a downstream LLM.
 * Byte-for-byte compatible with main.py:build_raw_markdown so /generate-blog keeps reading it.
 */
export function buildRawMarkdown(keyword, query, subreddits, posts) {
  const lines = [
    `# Reddit Research: ${keyword}`,
    "",
    `_Query: \`${query}\` — ${posts.length} posts across ${subreddits.length} subreddits. ` +
      "No AI applied; topic ideas are generated downstream._",
    "",
    "## Posts",
    "",
  ];
  for (const p of posts) {
    lines.push(`- [${p.title}](${p.url}) — r/${p.subreddit} (${p.score} pts)`);
  }
  lines.push("");
  lines.push("## Subreddits");
  lines.push("");
  for (const s of subreddits) {
    const subs = s.subscribers;
    const desc = s.description || "";
    lines.push(`- r/${s.name} (${subs} subs) — ${desc}`);
  }
  lines.push("");
  return lines.join("\n");
}

/** Write the result to .previous/<keyword>.md and return the path. */
export function saveMarkdown(keyword, content) {
  mkdirSync(RESULT_DIR, { recursive: true });
  const path = join(RESULT_DIR, `${slugify(keyword)}.md`);
  writeFileSync(path, content, "utf-8");
  return path;
}
