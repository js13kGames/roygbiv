#!/usr/bin/env bash
# js13k build chain: extract -> terser -> roadroller -> zip -> measure.
#
# Unlike a "minimal HTML" build, this one KEEPS the header from the
# source. The viewport tag is not optional: without it, mobile Safari
# assumes a 980-pixel window and the game renders zoomed out.
#
# Three deliverables, from the same state of the source:
#   js13k-game.zip           the contest archive, holding index.html AT ITS ROOT
#   dist/js13k/index.html    the same page, exactly as it sits in the zip
#   dist/wavedash/index.html the UNCOMPRESSED page, for the Wavedash platform
#
# The file name inside the archive is not cosmetic: the rules require an
# index.html in the top-level directory. An earlier version of this script
# put index-80.min.html there, which is enough to get the entry rejected.
#
# Usage: bash build.sh
set -euo pipefail
cd "$(dirname "$0")"

[ "$#" -eq 0 ] || { echo "Usage: bash build.sh (builds src/index-80.html)"; exit 1; }
SRC="src/index-80.html"
LIMIT=13312                       # 13 * 1024

[ -f "$SRC" ] || { echo "Source not found: $SRC"; exit 1; }
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
ZIP="js13k-game.zip"; OUT="dist/js13k"; WD="dist/wavedash"
mkdir -p "$OUT"

# --- outils ---------------------------------------------------------------
find_tool(){ local n="$1" p
  for p in "./node_modules/.bin/$n" "$HOME/node_modules/.bin/$n" \
           "$(npm root -g 2>/dev/null)/.bin/$n" "$(npm config get prefix 2>/dev/null)/bin/$n"; do
    [ -x "$p" ] && { echo "$p"; return 0; }
  done
  command -v "$n" >/dev/null 2>&1 && { echo "$n"; return 0; }
  return 1; }
TERSER="$(find_tool terser || true)"
ROADROLLER="$(find_tool roadroller || true)"
if [ -z "$TERSER" ] || [ -z "$ROADROLLER" ]; then
  echo "Installing terser + roadroller ..."
  npm install -g terser roadroller >/dev/null 2>&1 || npm install terser roadroller >/dev/null 2>&1 || true
  TERSER="$(find_tool terser || echo "npx --yes terser")"
  ROADROLLER="$(find_tool roadroller || echo "npx --yes roadroller")"
fi

# --- 1. split the source into head / script -------------------------------
python3 - "$SRC" "$WORK" <<'PY'
import re, sys
src, work = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
m = re.search(r'<script>(.*)</script>', html, re.S)
if not m: sys.exit("No <script> block found")
open(work+'/game.js','w',encoding='utf-8').write(m.group(1))
# The header is kept, viewport included, but trimmed down: in HTML5 the
# html / head / body tags are implicit, and quotes only matter when the
# value contains a space or a comma.
head = html[:m.start()]
head = re.sub(r'\s*\n\s*', '', head)
head = re.sub(r'</?(html|head|body)[^>]*>', '', head)
head = re.sub(r'(\w+)="([^"\s,;/>]+)"', r'\1=\2', head)      # guillemets inutiles
css = re.search(r'<style>(.*?)</style>', head, re.S)
if css:
    c = css.group(1)
    c = re.sub(r'\s*([{}:;,])\s*', r'\1', c)                 # whitespace around the separators
    c = c.replace(';}', '}')
    head = head[:css.start()] + '<style>' + c + '</style>' + head[css.end():]
open(work+'/head.html','w',encoding='utf-8').write(head)
PY

# --- 2. check, then minify ------------------------------------------------
# booleans_as_integers is deliberately absent: it rewrites true as 1, which
# trips the Wavedash SDK type validation. The bug shows up only in the
# build, never from the source.
node --check "$WORK/game.js" && echo "JS syntax       : OK"
$TERSER "$WORK/game.js" -c passes=3,unsafe=true -m toplevel=true -o "$WORK/game.min.js" 2>/dev/null \
  || cp "$WORK/game.js" "$WORK/game.min.js"
echo "terser          : $(wc -c < "$WORK/game.min.js") bytes"

# --- 3. roadroller ---------------------------------------------------------
# Roadroller's search is random: from one build to the next the output
# varies by some thirty bytes, enough to land under the limit or not.
# So we run several attempts and keep the smallest one.
TRIES="${TRIES:-4}"
BEST=""
if [ -n "$ROADROLLER" ]; then
  for i in $(seq 1 "$TRIES"); do
    if $ROADROLLER "$WORK/game.min.js" -O2 -o "$WORK/try.js" 2>/dev/null; then
      SZ=$(wc -c < "$WORK/try.js")
      if [ -z "$BEST" ] || [ "$SZ" -lt "$BEST" ]; then
        BEST="$SZ"; cp "$WORK/try.js" "$WORK/game.rr.js"
      fi
      printf "  run %s : %s bytes\n" "$i" "$SZ"
    fi
  done
fi
if [ -n "$BEST" ]; then
  echo "roadroller      : $BEST bytes (best of $TRIES runs)"
else
  echo "roadroller unavailable, keeping the terser output."
  cp "$WORK/game.min.js" "$WORK/game.rr.js"
fi

# --- 4. reassembler --------------------------------------------------------
# The header is cut off BEFORE the <script> tag, so it has to be written back
# here. Without it the code sits bare after </canvas>, the browser reads it
# as text, and the page stays black WITHOUT a single console error --
# a dead deliverable that nothing reports. Hence the two checks below.
cat "$WORK/head.html" > "$WORK/index.html"
printf '<script>' >> "$WORK/index.html"
printf '%s' "$(cat "$WORK/game.rr.js")" >> "$WORK/index.html"
printf '</script>' >> "$WORK/index.html"

grep -q '<script>' "$WORK/index.html" && grep -q '</script>' "$WORK/index.html" \
  && echo "script tags     : opening and closing present" \
  || { echo "ERROR: the build <script> block is incomplete, the page would be dead."; exit 1; }

grep -q viewport "$WORK/index.html" \
  && echo "viewport        : preserved" \
  || { echo "ERROR: the viewport tag vanished from the build."; exit 1; }

cp "$WORK/index.html" "$OUT/index.html"

# The Wavedash target is the source as it stands: no minification, no
# roadroller. The platform has no size limit, and a readable page makes
# a bug reported from there diagnosable.
if [ -n "$WD" ]; then
  mkdir -p "$WD"; cp "$SRC" "$WD/index.html"
  echo "wavedash        : $WD/index.html ($(wc -c < "$WD/index.html") bytes, uncompressed)"
fi

# --- 5. zip and measure ----------------------------------------------------
rm -f "$ZIP"
( cd "$WORK" && zip -9 -q "$OLDPWD/$ZIP" index.html )
command -v advzip >/dev/null 2>&1 && advzip -z -4 -q "$ZIP" && echo "advzip          : zopfli recompression applied"

# The file name inside the archive is a rule, not a detail: we check it.
unzip -l "$ZIP" | grep -qE '^\s+[0-9]+ .* index\.html$' \
  || { echo "ERROR: the archive does not hold index.html at its root."; unzip -l "$ZIP"; exit 1; }

Z=$(wc -c < "$ZIP"); M=$((LIMIT - Z))
echo "----------------------------------------"
echo "archive         : $ZIP (index.html at the root)"
echo "ZIP             : $Z / $LIMIT bytes"
if [ "$Z" -le "$LIMIT" ]; then echo "WITHIN BUDGET. Margin: $M bytes."
else echo "OVER BUDGET by $((Z - LIMIT)) bytes."; exit 1; fi
