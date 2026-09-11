#!/usr/bin/env bash
# Rejoue la batterie Wavedash sur la SORTIE TERSER, pas sur la source.
#
# C'est le seul test qui attrape le piege des booleens : la source marche,
# le livrable non. Les options de compression sont celles de build.sh. Le
# mangle toplevel est retire pour ce test seulement -- il empeche d'appeler
# les fonctions du jeu par leur nom, et ne change pas la semantique verifiee.
set -euo pipefail
cd "$(dirname "$0")/.."
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
fail=0
for f in index.html index-80.html; do
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
  echo "-------- sortie terser de $f ($(wc -c < "$W/g.min.js") octets)"
  node test/wavedash.js "$W/t.html" || fail=1
done
exit $fail
