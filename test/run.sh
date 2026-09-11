#!/usr/bin/env bash
# Lance toute la batterie sur les deux versions.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
for f in index.html index-80.html; do
  echo "════════ $f"
  for t in test/smoke.js test/title.js test/wavedash.js; do
    node "$t" "$f" || fail=1
  done
done
# Le meme jeu, vu par terser : c'est la seule passe qui attrape une API cassee
# par la minification alors que la source fonctionne.
echo "════════ sortie terser"
bash test/terser-wavedash.sh || fail=1
[ $fail -eq 0 ] && echo "TOUT PASSE" || echo "DES TESTS ONT ECHOUE"
exit $fail
