#!/usr/bin/env bash
#
# generate-blog-images.sh
#
# Reads IMAGE_PROMPT blocks from blog markdown file(s) and generates the real
# images via the Gemini API (gemini-2.5-flash-image / Nano Banana), saving them
# under public/images/blogs/...
#
# Usage:
#   bash scripts/generate-blog-images.sh <blog.md> [<blog2.md> ...] [--force]
#
# Image targets are discovered from:
#   - in-content images:  ![alt](/images/blogs/<id>/<name>.jpg)  + following IMAGE_PROMPT comment
#   - cover image:         an HTML comment with  IMAGE_TARGET: /images/blogs/<id>/cover.jpg  + IMAGE_PROMPT
#
# API key: read from .env (GEMINI_API_KEY=...) or the environment.
# Existing images are skipped (idempotent) unless --force is passed.

set -uo pipefail

MODEL="gemini-2.5-flash-image"
API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent"

# --- image size config (override via env) ---
# Nano Banana only accepts ASPECT RATIO presets (1:1, 16:9, 4:3, 3:2, ...),
# NOT arbitrary pixel sizes. We request the closest ratio, then crop/resize to
# the exact target px with sips (macOS built-in).
#   IMG_ASPECT  = ratio preset sent to the API (closest to 1200x630 is 16:9)
#   IMG_WIDTH   = exact final width  in px
#   IMG_HEIGHT  = exact final height in px
IMG_ASPECT="${IMG_ASPECT:-16:9}"
IMG_WIDTH="${IMG_WIDTH:-1200}"
IMG_HEIGHT="${IMG_HEIGHT:-630}"

# --- resolve repo root (script lives in <root>/scripts) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PUBLIC_DIR="$ROOT_DIR/public"

FORCE=0
FILES=()

for arg in "$@"; do
  if [ "$arg" = "--force" ]; then
    FORCE=1
  else
    FILES+=("$arg")
  fi
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "Usage: bash scripts/generate-blog-images.sh <blog.md> [<blog2.md> ...] [--force]" >&2
  exit 1
fi

# --- load GEMINI_API_KEY ---
if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "$ROOT_DIR/.env" ]; then
  GEMINI_API_KEY="$(grep -E '^GEMINI_API_KEY=' "$ROOT_DIR/.env" | tail -n1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: GEMINI_API_KEY not found. Add GEMINI_API_KEY=... to .env or export it." >&2
  exit 1
fi

# --- python helper for JSON build + response decode ---
PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "ERROR: python3 is required (used for JSON encode/decode)." >&2
  exit 1
fi

GENERATED=0
SKIPPED=0
FAILED=0

# Parse a markdown file into "target<TAB>prompt" records (one per line).
# awk state machine. Prompt newlines are flattened to single spaces.
parse_md() {
  awk '
    function flush() {
      if (target != "" && prompt != "") {
        gsub(/\t/, " ", prompt)
        print target "\t" prompt
      }
      target = ""; prompt = ""; collecting = 0
    }
    # explicit cover target inside a comment
    /IMAGE_TARGET:/ {
      line = $0
      sub(/.*IMAGE_TARGET:[ \t]*/, "", line)
      gsub(/[ \t\r]+$/, "", line)
      target = line
      next
    }
    # in-content image markdown: ![...](/images/blogs/...)
    /^!\[.*\]\(\/images\/blogs\// {
      line = $0
      sub(/^!\[.*\]\(/, "", line)
      sub(/\).*$/, "", line)
      target = line
      next
    }
    /IMAGE_PROMPT:/ {
      collecting = 1
      rest = $0
      sub(/.*IMAGE_PROMPT:[ \t]*/, "", rest)
      if (rest != "") prompt = rest
      next
    }
    collecting == 1 {
      if ($0 ~ /-->/) { flush(); next }
      txt = $0
      gsub(/[\r]+$/, "", txt)
      if (txt != "") {
        if (prompt == "") prompt = txt
        else prompt = prompt " " txt
      }
      next
    }
    END { flush() }
  ' "$1"
}

generate_one() {
  local target="$1"
  local prompt="$2"

  # /images/blogs/... -> public/images/blogs/...
  local rel="${target#/}"
  local out="$PUBLIC_DIR/$rel"

  if [ -f "$out" ] && [ "$FORCE" -eq 0 ]; then
    echo "skip   $target (exists)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi

  mkdir -p "$(dirname "$out")"

  # build request body safely with python3 json.dumps
  local body
  body="$(PROMPT="$prompt" IMG_ASPECT="$IMG_ASPECT" "$PY" -c '
import json, os
print(json.dumps({
  "contents": [{"parts": [{"text": os.environ["PROMPT"]}]}],
  "generationConfig": {
    "responseModalities": ["IMAGE"],
    "imageConfig": {"aspectRatio": os.environ["IMG_ASPECT"]},
  },
}))')"

  local resp
  resp="$(curl -sS -X POST "$API_URL" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$body")"

  # decode: find first inlineData.data, base64-decode to file. Print error if none.
  if OUT="$out" "$PY" -c '
import json, sys, base64, os
data = json.load(sys.stdin)
parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
for p in parts:
    inline = p.get("inlineData") or p.get("inline_data")
    if inline and inline.get("data"):
        with open(os.environ["OUT"], "wb") as f:
            f.write(base64.b64decode(inline["data"]))
        sys.exit(0)
err = data.get("error", {}).get("message")
if err:
    sys.stderr.write(err + "\n")
else:
    sys.stderr.write("no image part in response\n")
sys.exit(1)
' <<< "$resp"; then
    # force exact pixel size: scale to target width, then center-crop to height
    if command -v sips >/dev/null 2>&1; then
      sips --resampleWidth "$IMG_WIDTH" "$out" >/dev/null 2>&1
      sips -c "$IMG_HEIGHT" "$IMG_WIDTH" "$out" >/dev/null 2>&1
    fi
    echo "ok     $target (${IMG_WIDTH}x${IMG_HEIGHT})"
    GENERATED=$((GENERATED + 1))
  else
    echo "FAIL   $target" >&2
    FAILED=$((FAILED + 1))
  fi
}

for md in "${FILES[@]}"; do
  if [ ! -f "$md" ]; then
    echo "WARN   file not found: $md" >&2
    continue
  fi
  echo "== $md =="
  while IFS=$'\t' read -r target prompt; do
    [ -z "$target" ] && continue
    generate_one "$target" "$prompt"
  done < <(parse_md "$md")
done

echo "----"
echo "done: generated=$GENERATED skipped=$SKIPPED failed=$FAILED"

if [ "$FAILED" -gt 0 ]; then
  exit 2
fi
exit 0
