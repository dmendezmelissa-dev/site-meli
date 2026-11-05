#!/usr/bin/env python3
"""Fabrique le site let's bloom. (espaces de Meli et de Sophie) en français et en anglais.

Sources : src/index.html (Meli) et src/sophie.html (Sophie).
Les blocs communs sont dans src/partials/ et s'insèrent avec  <!-- @inclure fichier.html -->
Les textes à traduire sont écrits en français entre doubles crochets, avec un identifiant :
    [[accueil.titre|Prends soin de toi]]
Les traductions anglaises sont dans i18n/en.json :
    "accueil.titre": {"fr": "Prends soin de toi", "en": "Take care of yourself"}
Le champ "fr" sert à repérer une traduction devenue obsolète quand le français change.

Usage : python3 build.py          -> écrit toutes les pages
        python3 build.py --sync   -> ajoute dans en.json les clés manquantes (en vide)
Le script s'arrête avec une erreur s'il manque une traduction, si une traduction
n'est plus à jour, ou s'il trouve un tiret cadratin ou demi-cadratin.

Pages produites :
    index.html            Meli, français        en/index.html         Meli, anglais
    sophie/index.html     Sophie, français      en/sophie/index.html  Sophie, anglais
"""
import json, re, sys
from pathlib import Path

ICI = Path(__file__).parent
SRC = ICI / "src"
EN_JSON = ICI / "i18n" / "en.json"
SEG = re.compile(r"\[\[([a-z0-9_.\-]+)\|(.*?)\]\]", re.S)
INCLURE = re.compile(r"<!-- @inclure ([\w.\-]+) -->")

# personne -> (gabarit, dossier, nom affiché, signature du pied de page)
PERSONNES = {
    "meli": ("index.html", "", "Meli", "@still.becoming.me24"),
    "sophie": ("sophie.html", "sophie/", "Sophie", "let's bloom."),
}
LANGUES = {"fr": "", "en": "en/"}


def assembler(nom):
    texte = (SRC / nom).read_text(encoding="utf-8")
    return INCLURE.sub(lambda m: (SRC / "partials" / m.group(1)).read_text(encoding="utf-8").rstrip("\n"), texte)


def segments(gabarits):
    vus = {}
    for texte in gabarits:
        for cle, fr in SEG.findall(texte):
            if cle in vus and vus[cle] != fr:
                sys.exit(f"Erreur : la clé {cle} a deux textes français différents.")
            vus[cle] = fr
    return vus


def chemin(lang, personne):
    return LANGUES[lang] + PERSONNES[personne][1] + "index.html"


def main():
    gabarits = {p: assembler(conf[0]) for p, conf in PERSONNES.items()}
    fr = segments(gabarits.values())
    en = json.loads(EN_JSON.read_text(encoding="utf-8")) if EN_JSON.exists() else {}

    if "--sync" in sys.argv:
        for cle, texte in fr.items():
            if cle not in en:
                en[cle] = {"fr": texte, "en": ""}
        EN_JSON.parent.mkdir(exist_ok=True)
        EN_JSON.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"en.json synchronisé ({len(en)} clés)")
        return

    problemes = []
    for cle, texte in fr.items():
        t = en.get(cle)
        if not t or not t.get("en"):
            problemes.append(f"traduction manquante : {cle}")
        elif t.get("fr") != texte:
            problemes.append(f"traduction à revoir (le français a changé) : {cle}")
    if problemes:
        sys.exit("Erreur :\n  " + "\n  ".join(problemes))

    for lang in LANGUES:
        for personne, (_, _, nom, signature) in PERSONNES.items():
            sortie = chemin(lang, personne)
            root = "../" * sortie.count("/")
            vars = {
                "lang": lang, "root": root, "nom": nom, "signature": signature,
                "href_fr": root + chemin("fr", personne), "href_en": root + chemin("en", personne),
                "actif_fr": "actif" if lang == "fr" else "", "actif_en": "actif" if lang == "en" else "",
                "actif_meli": "actif" if personne == "meli" else "",
                "actif_sophie": "actif" if personne == "sophie" else "",
                "logo_meli": "#accueil" if personne == "meli" else root + chemin(lang, "meli"),
                "logo_sophie": "#accueil" if personne == "sophie" else root + chemin(lang, "sophie"),
                "lien_legal": "#mentions-legales" if personne == "meli" else root + chemin(lang, "meli") + "#mentions-legales",
            }
            page = SEG.sub(lambda m: m.group(2) if lang == "fr" else en[m.group(1)]["en"], gabarits[personne])
            for k, v in vars.items():
                page = page.replace("{{" + k + "}}", v)
            if re.search(r"\{\{\w+\}\}|\[\[|@inclure", page):
                sys.exit(f"Erreur : un marqueur n'a pas été remplacé dans {sortie}.")
            if re.search("[–—]", page):
                sys.exit(f"Erreur : tiret cadratin ou demi-cadratin dans {sortie}.")
            (ICI / sortie).parent.mkdir(parents=True, exist_ok=True)
            (ICI / sortie).write_text(page, encoding="utf-8")
            print(f"{lang} {personne} -> {sortie}")
    inutiles = sorted(set(en) - set(fr))
    if inutiles:
        print("Clés anglaises qui ne servent plus : " + ", ".join(inutiles))


if __name__ == "__main__":
    main()
