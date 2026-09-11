#!/usr/bin/env bash
# Runs the whole suite on the arcade source.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
for f in src/index-80.html; do
  echo "════════ $f"
  for t in test/smoke.js test/title.js test/wavedash.js; do
    node "$t" "$f" || fail=1
  done
done
# The same game, seen through terser: the only pass that catches an API broken
# by minification while the source still works.
echo "════════ terser output"
bash test/terser-wavedash.sh || fail=1
[ $fail -eq 0 ] && echo "ALL PASS" || echo "SOME TESTS FAILED"
exit $fail
