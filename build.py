#!/usr/bin/env python3
"""Fabrique le site let's bloom. (espaces de Meli et de Sophie) en français et en anglais.

Sources : src/index.html (Meli) et src/sophie.html (Sophie).
Les blocs communs sont dans src/partials/ et s'insèrent avec  <!-- @inclure fichier.html -->
Les textes à traduire sont écrits en français entre doubles crochets, avec un identifiant :
    [[accueil.titre|Prends soin de toi]]
Les traductions sont dans i18n/<langue>.json (en.json, es.json) :
    "accueil.titre": {"fr": "Prends soin de toi", "en": "Take care of yourself"}
Le champ "fr" sert à repérer une traduction devenue obsolète quand le français change.

Usage : python3 build.py          -> écrit toutes les pages
        python3 build.py --sync   -> ajoute dans chaque fichier de langue les clés manquantes (vides)
Le script s'arrête avec une erreur s'il manque une traduction, si une traduction
n'est plus à jour, ou s'il trouve un tiret cadratin ou demi-cadratin.

Pages produites :
    index.html          Meli, français     en/index.html          es/index.html
    sophie/index.html   Sophie, français   en/sophie/index.html   es/sophie/index.html
Un clic sur un prénom ouvre l'espace de la personne dans sa langue par défaut
(Meli en français, Sophie en anglais) : voir LANGUE_PAR_DEFAUT.
"""
import json, re, sys
from pathlib import Path

ICI = Path(__file__).parent
SRC = ICI / "src"
SEG = re.compile(r"\[\[([a-z0-9_.\-]+)\|(.*?)\]\]", re.S)
INCLURE = re.compile(r"<!-- @inclure ([\w.\-]+) -->")

# personne -> (gabarit, dossier, nom affiché, signature du pied de page)
PERSONNES = {
    "meli": ("index.html", "", "Meli", "@still.becoming.me24"),
    "sophie": ("sophie.html", "sophie/", "Sophie", "let's bloom."),
}
# langue dans laquelle s'ouvre l'espace d'une personne quand on clique sur son prénom
LANGUE_PAR_DEFAUT = {"meli": "fr", "sophie": "en"}
LANGUES = {"fr": "", "en": "en/", "es": "es/"}   # le français est la langue source


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
    trad = {}
    for lang in LANGUES:
        if lang == "fr":
            continue
        f = ICI / "i18n" / f"{lang}.json"
        trad[lang] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    if "--sync" in sys.argv:
        for lang, d in trad.items():
            for cle, texte in fr.items():
                if cle not in d:
                    d[cle] = {"fr": texte, lang: ""}
            f = ICI / "i18n" / f"{lang}.json"
            f.parent.mkdir(exist_ok=True)
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{lang}.json synchronisé ({len(d)} clés)")
        return

    problemes = []
    for lang, d in trad.items():
        for cle, texte in fr.items():
            t = d.get(cle)
            if not t or not t.get(lang):
                problemes.append(f"[{lang}] traduction manquante : {cle}")
            elif t.get("fr") != texte:
                problemes.append(f"[{lang}] traduction à revoir (le français a changé) : {cle}")
    if problemes:
        sys.exit("Erreur :\n  " + "\n  ".join(problemes))

    for lang in LANGUES:
        for personne, (_, _, nom, signature) in PERSONNES.items():
            sortie = chemin(lang, personne)
            root = "../" * sortie.count("/")
            liens = '<span aria-hidden="true">·</span>'.join(
                f'<a href="{root + chemin(l, personne)}" lang="{l}" hreflang="{l}" class="{"actif" if l == lang else ""}">{l.upper()}</a>'
                for l in LANGUES)
            alternates = "\n  ".join(
                [f'<link rel="alternate" hreflang="{l}" href="{root + chemin(l, personne)}">' for l in LANGUES]
                + [f'<link rel="alternate" hreflang="x-default" href="{root + chemin(LANGUE_PAR_DEFAUT[personne], personne)}">'])
            vars = {
                "lang": lang, "root": root, "nom": nom, "signature": signature,
                "liens_langues": liens, "alternates": alternates,
                "actif_meli": "actif" if personne == "meli" else "",
                "actif_sophie": "actif" if personne == "sophie" else "",
                "logo_meli": "#accueil" if personne == "meli" else root + chemin(LANGUE_PAR_DEFAUT["meli"], "meli"),
                "logo_sophie": "#accueil" if personne == "sophie" else root + chemin(LANGUE_PAR_DEFAUT["sophie"], "sophie"),
                "lien_legal": "#mentions-legales" if personne == "meli" else root + chemin(lang, "meli") + "#mentions-legales",
            }
            page = SEG.sub(lambda m: m.group(2) if lang == "fr" else trad[lang][m.group(1)][lang], gabarits[personne])
            for k, v in vars.items():
                page = page.replace("{{" + k + "}}", v)
            if re.search(r"\{\{\w+\}\}|\[\[|@inclure", page):
                sys.exit(f"Erreur : un marqueur n'a pas été remplacé dans {sortie}.")
            if re.search("[\u2013\u2014]", page):
                sys.exit(f"Erreur : tiret cadratin ou demi-cadratin dans {sortie}.")
            (ICI / sortie).parent.mkdir(parents=True, exist_ok=True)
            (ICI / sortie).write_text(page, encoding="utf-8")
            print(f"{lang} {personne} -> {sortie}")
    for lang, d in trad.items():
        inutiles = sorted(set(d) - set(fr))
        if inutiles:
            print(f"[{lang}] clés qui ne servent plus : " + ", ".join(inutiles))


if __name__ == "__main__":
    main()
