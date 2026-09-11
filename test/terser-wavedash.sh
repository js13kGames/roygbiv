#!/usr/bin/env bash
# Replays the Wavedash suite on the TERSER OUTPUT, not on the source.
#
# This is the only test that catches the boolean trap: the source works, the
# shipped build does not. The compression options are those of build.sh. The
# toplevel mangle is dropped for this test only -- it prevents calling the
# game functions by name, and does not change the semantics being checked.
set -euo pipefail
cd "$(dirname "$0")/.."
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
fail=0
for f in src/index-80.html; do
  python3 - "$f" "$W" <<'PY'
import re, sys
src, work = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
open(work+'/g.js','w',encoding='utf-8').write(re.search(r'<script>(.*)</script>', html, re.S).group(1))
PY
  TERSER="./node_modules/.bin/terser"
  [ -x "$TERSER" ] || TERSER="$(command -v terser || echo 'npx --yes terser')"
  $TERSER "$W/g.js" -c passes=3,unsafe=true -o "$W/g.min.js"
  printf '<script>' > "$W/t.html"; cat "$W/g.min.js" >> "$W/t.html"; printf '</script>' >> "$W/t.html"
  echo "-------- terser output of $f ($(wc -c < "$W/g.min.js") bytes)"
  node test/wavedash.js "$W/t.html" || fail=1
done
exit $fail
