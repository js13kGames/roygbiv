#!/usr/bin/env bash
# Chaine de build js13k : extraction -> terser -> roadroller -> zip -> mesure.
#
# Contrairement a un build "HTML minimal", celui-ci CONSERVE l'en-tete de la
# source. La balise viewport n'est pas optionnelle : sans elle, Safari mobile
# suppose une fenetre de 980 pixels et le jeu s'affiche dezoome.
#
# Trois livrables, depuis le meme etat de la source :
#   js13k-game.zip           l'archive du concours, contenant index.html A SA RACINE
#   dist/js13k/index.html    la meme page, telle qu'elle est dans le zip
#   dist/wavedash/index.html la page NON compressee, pour la plateforme Wavedash
#
# Le nom du fichier dans l'archive n'est pas cosmetique : le reglement exige un
# index.html dans le repertoire de premier niveau. Une version anterieure de ce
# script y mettait index-80.min.html, ce qui suffit a faire rejeter l'entree.
#
# Usage : bash build.sh              # l'entree du concours (voir ENTRY)
#         bash build.sh index.html   # une autre variante, ecrite dans dist/alt/
set -euo pipefail

ENTRY="index-80.html"             # la variante reellement soumise
SRC="${1:-$ENTRY}"
LIMIT=13312                       # 13 * 1024

[ -f "$SRC" ] || { echo "Source introuvable: $SRC"; exit 1; }
BASE="$(basename "$SRC" .html)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

# Une variante qui n'est pas l'entree n'ecrase JAMAIS le livrable : elle part
# dans dist/alt/. Sans cette separation, un build de comparaison laisse derriere
# lui un js13k-game.zip qui n'est pas celui qu'on croit soumettre.
if [ "$SRC" = "$ENTRY" ]; then
  ZIP="js13k-game.zip"; OUT="dist/js13k"; WD="dist/wavedash"
else
  ZIP="dist/alt/$BASE.zip"; OUT="dist/alt/$BASE"; WD=""
  echo "Variante hors concours : sortie dans dist/alt/, js13k-game.zip intact."
fi
mkdir -p "$OUT" "$(dirname "$ZIP")"

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
  echo "Installation de terser + roadroller ..."
  npm install -g terser roadroller >/dev/null 2>&1 || npm install terser roadroller >/dev/null 2>&1 || true
  TERSER="$(find_tool terser || echo "npx --yes terser")"
  ROADROLLER="$(find_tool roadroller || echo "npx --yes roadroller")"
fi

# --- 1. decouper la source en tete / script -------------------------------
python3 - "$SRC" "$WORK" <<'PY'
import re, sys
src, work = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
m = re.search(r'<script>(.*)</script>', html, re.S)
if not m: sys.exit("Aucun bloc <script> trouve")
open(work+'/game.js','w',encoding='utf-8').write(m.group(1))
# L'en-tete est conservee, viewport comprise, mais degraissee : en HTML5 les
# balises html / head / body sont implicites, et les guillemets ne servent que
# si la valeur contient un espace ou une virgule.
head = html[:m.start()]
head = re.sub(r'\s*\n\s*', '', head)
head = re.sub(r'</?(html|head|body)[^>]*>', '', head)
head = re.sub(r'(\w+)="([^"\s,;/>]+)"', r'\1=\2', head)      # guillemets inutiles
css = re.search(r'<style>(.*?)</style>', head, re.S)
if css:
    c = css.group(1)
    c = re.sub(r'\s*([{}:;,])\s*', r'\1', c)                 # espaces autour des separateurs
    c = c.replace(';}', '}')
    head = head[:css.start()] + '<style>' + c + '</style>' + head[css.end():]
open(work+'/head.html','w',encoding='utf-8').write(head)
PY

# --- 2. verifier puis minifier --------------------------------------------
# booleans_as_integers est volontairement absent : il reecrit true en 1, ce qui
# fait lever la validation de type du SDK Wavedash. Le bug ne se voit que dans
# le build, jamais depuis la source.
node --check "$WORK/game.js" && echo "Syntaxe JS      : OK"
$TERSER "$WORK/game.js" -c passes=3,unsafe=true -m toplevel=true -o "$WORK/game.min.js" 2>/dev/null \
  || cp "$WORK/game.js" "$WORK/game.min.js"
echo "terser          : $(wc -c < "$WORK/game.min.js") octets"

# --- 3. roadroller ---------------------------------------------------------
# La recherche de roadroller est aleatoire : d'un build a l'autre la sortie
# varie d'une trentaine d'octets, assez pour passer ou non sous la limite.
# On lance donc plusieurs essais et on garde le plus petit.
TRIES="${TRIES:-4}"
BEST=""
if [ -n "$ROADROLLER" ]; then
  for i in $(seq 1 "$TRIES"); do
    if $ROADROLLER "$WORK/game.min.js" -O2 -o "$WORK/try.js" 2>/dev/null; then
      SZ=$(wc -c < "$WORK/try.js")
      if [ -z "$BEST" ] || [ "$SZ" -lt "$BEST" ]; then
        BEST="$SZ"; cp "$WORK/try.js" "$WORK/game.rr.js"
      fi
      printf "  essai %s : %s octets\n" "$i" "$SZ"
    fi
  done
fi
if [ -n "$BEST" ]; then
  echo "roadroller      : $BEST octets (meilleur de $TRIES essais)"
else
  echo "roadroller indisponible, on garde la sortie terser."
  cp "$WORK/game.min.js" "$WORK/game.rr.js"
fi

# --- 4. reassembler --------------------------------------------------------
# L'en-tete est decoupee AVANT la balise <script> : il faut donc la reecrire
# ici. Sans elle le code est colle nu derriere </canvas>, le navigateur le lit
# comme du texte, et la page reste noire SANS la moindre erreur console --
# un livrable mort que rien ne signale. D'ou les deux verifications ci-dessous.
cat "$WORK/head.html" > "$WORK/index.html"
printf '<script>' >> "$WORK/index.html"
printf '%s' "$(cat "$WORK/game.rr.js")" >> "$WORK/index.html"
printf '</script>' >> "$WORK/index.html"

grep -q '<script>' "$WORK/index.html" && grep -q '</script>' "$WORK/index.html" \
  && echo "balises script  : ouvrante et fermante presentes" \
  || { echo "ERREUR: le bloc <script> du build est incomplet, la page serait morte."; exit 1; }

grep -q viewport "$WORK/index.html" \
  && echo "viewport        : conservee" \
  || { echo "ERREUR: la balise viewport a disparu du build."; exit 1; }

cp "$WORK/index.html" "$OUT/index.html"

# La cible Wavedash est la source telle quelle : pas de minification, pas de
# roadroller. La plateforme n'a pas de limite de taille, et une page lisible
# rend un bug de la-bas diagnosticable.
if [ -n "$WD" ]; then
  mkdir -p "$WD"; cp "$SRC" "$WD/index.html"
  echo "wavedash        : $WD/index.html ($(wc -c < "$WD/index.html") octets, non compresse)"
fi

# --- 5. zipper et mesurer --------------------------------------------------
rm -f "$ZIP"
( cd "$WORK" && zip -9 -q "$OLDPWD/$ZIP" index.html )
command -v advzip >/dev/null 2>&1 && advzip -z -4 -q "$ZIP" && echo "advzip          : recompression zopfli appliquee"

# Le nom du fichier dans l'archive est une regle, pas un detail : on le verifie.
unzip -l "$ZIP" | grep -qE '^\s+[0-9]+ .* index\.html$' \
  || { echo "ERREUR: l'archive ne contient pas index.html a sa racine."; unzip -l "$ZIP"; exit 1; }

Z=$(wc -c < "$ZIP"); M=$((LIMIT - Z))
echo "----------------------------------------"
echo "archive         : $ZIP (index.html a la racine)"
echo "ZIP             : $Z / $LIMIT octets"
if [ "$Z" -le "$LIMIT" ]; then echo "DANS LE BUDGET. Marge: $M octets."
else echo "DEPASSEMENT de $((Z - LIMIT)) octets."; exit 1; fi
