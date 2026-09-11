# ROYGBIV

Entrée js13kGames 2026, thème *Unicorns and Rainbows*.

Tout le monde parle des licornes. Les arcs-en-ciel n'ont jamais une belle place
dans les histoires. Ça va changer.

Un top-down shooter roguelite où vous jouez l'arc-en-ciel, armé d'un fusil à
pompe, contre une horde de licornes écœurantes de mignonnerie.

## La mécanique centrale

Le corps du héros est fait de **sept bandes de couleur, et ces sept bandes sont
à la fois sa barre de vie et ses sept emplacements de pouvoir**.

- Il commence entièrement gris, une seule bande peinte, tirée au hasard.
- Chaque montée de niveau peint une bande et lui attache un pouvoir, choisi
  parmi trois tirés au sort dans les quatre de cette couleur.
- Encaisser un coup éteint la bande la plus interne : **vous perdez le pouvoir
  avec elle**, et c'est toujours votre meilleure carte qui part la première.
- Quatre secondes sans dégât et la bande se repeint, avec son pouvoir.

Il y a **28 pouvoirs**, quatre par bande, et **sept paliers de licornes** dont
la mère qui se scinde en deux à sa mort. Au bout, une hydre à quatre têtes dont
la crinière est faite de sept mèches arc-en-ciel volées : chaque mèche arrachée
tue une tête, qui prend les yeux en croix et dont le cou retombe.

## Deux versions

| Fichier | Rendu |
|---|---|
| `index.html` | vectoriel, halos et dégradés, champ vert |
| `index-80.html` | borne d'arcade : 147x320 pixels internes agrandis au plus proche voisin, scanlines, police bitmap 3x5, fond noir |

**C'est `index-80.html` qui part au concours.** `index.html` reste la source de
référence et sert de variante de comparaison.

**`index-80.html` est généré, ne l'éditez pas à la main.** Toute modification se
fait dans `index.html`, puis :

```sh
python3 mk80.py        # régénère index-80.html
```

`mk80.py` applique des substitutions textuelles sur la source : résolution
interne, scanlines, remplacement de `fillText` par une police bitmap, retrait
des halos et dégradés qui n'ont pas leur place sur une borne. Il **échoue
bruyamment** si un de ses motifs a bougé, ce qui en fait un filet utile : toute
modification de `index.html` qui casse une de ses ancres est signalée tout de
suite, pas au moment du build.

## Construire

```sh
bash build.sh                 # l'entrée du concours
bash build.sh index.html      # la variante vectorielle, hors concours
```

Le build de l'entrée produit trois livrables depuis le même état de la source :

| Fichier | Rôle |
|---|---|
| `js13k-game.zip` | l'archive soumise, contenant **`index.html` à sa racine** |
| `dist/js13k/index.html` | la même page, telle qu'elle est dans l'archive |
| `dist/wavedash/index.html` | la page **non compressée**, déployée sur Wavedash |

La chaîne est : extraction du `<script>`, `terser`, `roadroller`, `zip -9`,
`advzip`, mesure. Les deux outils JS sont installés automatiquement s'ils
manquent ; `advzip` est facultatif et rend 2 à 3 % de l'archive quand il est là.

Un build de la variante vectorielle écrit dans `dist/alt/` et **ne touche pas**
à `js13k-game.zip` : un livrable ne doit pas pouvoir être écrasé par un build de
comparaison.

### Ce que le build vérifie, et pourquoi

**Le nom du fichier dans l'archive.** Le règlement exige un `index.html` dans le
répertoire de premier niveau. Une version antérieure y mettait
`index-80.min.html` : recevable à l'œil, rejeté par le concours.

**Les deux balises `<script>`.** L'en-tête est découpée *avant* la balise
ouvrante, il faut donc la réécrire au réassemblage. Quand elle manquait, le
code se retrouvait collé nu derrière `</canvas>`, le navigateur le lisait comme
du texte, et la page restait noire **sans la moindre erreur console** : un
livrable mort que rien ne signalait. Le build refuse maintenant de produire une
archive dont le bloc `<script>` est incomplet.

**La balise `viewport`.** Sans elle, Safari mobile suppose une fenêtre de 980
pixels et le jeu s'affiche dézoomé.

**La taille du zip n'est pas stable d'un build à l'autre.** `roadroller -O2`
fait une recherche aléatoire de paramètres : dix tirages successifs se sont
étalés sur 47 octets de sortie. Le script en lance quatre et garde le plus
petit ; `TRIES=12 bash build.sh` en fait davantage quand la marge est mince.
**Lire le chiffre que le build vient d'imprimer, jamais un chiffre noté ici.**

## Tester

```sh
bash test/run.sh
```

Les tests montent un faux DOM sous node et **jouent réellement** le jeu : écran
titre, six montées de niveau, deux mille images, dégâts, mort, victoire. Ils
vérifient aussi la mise en page du titre sur quatre formats d'écran, portrait
comme paysage.

Le faux contexte de `test/harness.js` **imite Safari**, qui renvoie la police
normalisée avec le poids en chiffres (`700 30px monospace`) là où Chrome renvoie
`bold 30px monospace`. Ce détail avait cassé la police bitmap de la version
arcade, qui lisait 700 comme taille de caractère.

`test/wavedash.js` rejoue l'intégration Wavedash contre un faux SDK qui **valide
les types comme le vrai** : un stub permissif ne teste rien. `test/terser-wavedash.sh`
rejoue la même batterie sur la **sortie terser**, avec les options de
compression de production — c'est la seule passe qui attrape une API cassée par
la minification alors que la source fonctionne.

## Wavedash

Le jeu coche le challenge Wavedash de l'édition 2026. C'est une case sur la même
entrée js13k, pas une seconde soumission.

L'intégration tient dans un bloc unique en fin de `index.html`. **Rien n'est
téléchargé** : la plateforme injecte un global `Wavedash` avant le code du jeu,
et chaque appel est gardé, donc le bloc est inerte partout ailleurs. La règle
« aucune ressource externe » est respectée, et le jeu se comporte à l'identique
sur js13kgames.com.

Elle apporte dix trophées, deux classements, et un **bandeau de trophée maison**
qui ne dépend pas de la plateforme : il s'affiche aussi sur js13kgames.com, là
où sont les votants. Les libellés se dérivent des identifiants, ce qui évite
d'embarquer une table de titres dans les 13 ko.

| Fichier | Rôle |
|---|---|
| `wavedash-achievements.json` | les définitions à importer dans le Developer Portal |
| `wavedash.toml` | `upload_dir` pointe sur `dist/wavedash/`, jamais sur `dist/` entier |

**Les définitions doivent exister côté portail avant que le jeu ne les
déclenche** : le SDK ignore `setAchievement()` pour tout identifiant inconnu et
retourne `false` sans un mot. L'import du JSON se fait à la main, depuis le
portail — le CLI ne sait créer les trophées qu'un par un et n'avale pas de
fichier.

## Les labos

`tools/` contient des pages autonomes qui ont servi à trancher la direction
artistique. Elles ne partent pas dans le zip.

| Fichier | Sert à |
|---|---|
| `title-four.html` | quatre écrans titre à comparer, avec simulation portrait |
| `hero-shapes.html` | quatre silhouettes de héros, curseurs de bandes peintes et débloquées |
| `boss-six.html` | six boss, curseur de mèches restantes pour voir l'agonie |
| `music-six.html` | six pistes procédurales, même moteur que le jeu |
| `face-editor.html` | 63 curseurs sur la géométrie des têtes de licorne, avec génération du code |

## Contraintes

- **13 312 octets** zippés, sans aucun fichier externe.
- Aucun asset : tout est dessiné en primitives canvas et cuit une fois dans des
  canvas hors écran. La musique et les bruitages sont synthétisés en Web Audio.
- Le monde fait 3000x3000 unités et s'agrandit si la vue est plus large. Les
  licornes ne naissent **jamais** dans le champ visible : la position de sortie
  de cadre est calculée exactement le long du rayon, et si aucune place valable
  n'existe, la licorne ne naît pas.

## Commandes

| | |
|---|---|
| flèches ou WASD / ZQSD | se déplacer |
| doigt, n'importe où | joystick virtuel |
| 1 2 3 | choisir un pouvoir |
| M | couper le son |

La visée et le tir sont automatiques, et le fusil n'ouvre le feu que si une
licorne est à portée de plomb.

## Licence

MIT.
