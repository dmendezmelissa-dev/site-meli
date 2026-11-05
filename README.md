# Site let's bloom. : espaces de Meli (@still.becoming.me24) et de Sophie

Site statique, en français et en anglais, publié avec GitHub Pages.
En haut de chaque page, « Meli. » et « Sophie. » permettent de choisir la personne.

## Comment c'est rangé
- `src/index.html` (Meli) et `src/sophie.html` (Sophie) : **les pages à modifier**. Les textes y sont
  écrits en français, entre doubles crochets avec un identifiant : `[[accueil.titre|Prends soin de toi]]`.
- `src/partials/` : blocs communs (en-tête avec le choix de la personne, langues, présentation
  let's bloom., pied de page et script), insérés avec `<!-- @inclure fichier.html -->`.
- `i18n/en.json` : les traductions anglaises, une par identifiant.
- `build.py` : fabrique `index.html`, `en/index.html`, `sophie/index.html`, `en/sophie/index.html`.
  Ces fichiers sont générés : ne pas les modifier à la main.
- `css/style.css`, `fonts/`, `images/` : communs aux deux langues.

## Modifier un texte
1. Changer le français dans `src/index.html`, `src/sophie.html` ou `src/partials/` (ou ajouter un nouveau `[[cle|texte]]`).
2. `python3 build.py --sync` ajoute les nouvelles clés dans `i18n/en.json`.
3. Écrire l'anglais dans `i18n/en.json` (et recopier le nouveau français dans `"fr"` si le texte a changé).
4. `python3 build.py` : refuse de construire s'il manque une traduction, si une traduction
   n'est plus à jour, ou s'il y a un tiret cadratin ou demi-cadratin.

## Fonctionnement de la page
- Une page HTML par langue, découpée en « pages » (`section.page[data-page]`) affichées
  une à une selon l'adresse : `#histoire`, `#packs`, `#packs-nutrition`, `#pack-routine`...
- Le bouton FR · EN garde la page en cours.
- Bouton « Réserver » fixe en bas sur téléphone (après le haut de page).
- Animations douces (`.reveal`), désactivées si le téléphone demande moins d'animations.
