#!/usr/bin/env node
// Generate one blog image via Gemini (Nano Banana). Node port of the /generate-blog
// inline python heredoc. Reads PROMPT + OUT from env; idempotent (skips if OUT exists).
//
//   PROMPT='<image prompt>' OUT='public/images/blogs/<...>.jpg' npx blog-image
//
// Config from .env (with defaults): GEMINI_API_KEY, IMG_ASPECT, IMG_WIDTH, IMG_HEIGHT.
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { spawnSync } from "node:child_process";

if (existsSync(".env") && typeof process.loadEnvFile === "function") {
  try {
    process.loadEnvFile(".env");
  } catch {
    /* ignore */
  }
}

const env = (k, d) => process.env[k] || d;

const key = env("GEMINI_API_KEY");
if (!key) {
  console.error("ERROR: GEMINI_API_KEY not found. Add it to .env or export it.");
  process.exit(1);
}

const aspect = env("IMG_ASPECT", "16:9");
const w = env("IMG_WIDTH", "1200");
const h = env("IMG_HEIGHT", "630");
const prompt = process.env.PROMPT;
const out = process.env.OUT;

if (!prompt || !out) {
  console.error("ERROR: set PROMPT and OUT env vars.");
  process.exit(1);
}

if (existsSync(out)) {
  console.log(`skip ${out} (exists)`);
  process.exit(0);
}
mkdirSync(dirname(out), { recursive: true });

const body = JSON.stringify({
  contents: [{ parts: [{ text: prompt }] }],
  generationConfig: { responseModalities: ["IMAGE"], imageConfig: { aspectRatio: aspect } },
});

const resp = await fetch(
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent",
  { method: "POST", headers: { "x-goog-api-key": key, "Content-Type": "application/json" }, body }
);
const data = await resp.json();

const parts = data?.candidates?.[0]?.content?.parts || [];
let wrote = false;
for (const p of parts) {
  const inl = p.inlineData || p.inline_data;
  if (inl?.data) {
    writeFileSync(out, Buffer.from(inl.data, "base64"));
    // Force exact px on macOS (sips); elsewhere leave at the API aspect ratio.
    if (spawnSync("which", ["sips"]).status === 0) {
      spawnSync("sips", ["--resampleWidth", w, out], { stdio: "ignore" });
      spawnSync("sips", ["-c", h, w, out], { stdio: "ignore" });
    }
    console.log(`ok ${out} (${w}x${h})`);
    wrote = true;
    break;
  }
}
if (!wrote) {
  console.error(data?.error?.message || "no image part in response");
  process.exit(1);
}
