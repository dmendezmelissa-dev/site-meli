#!/usr/bin/env python3
"""Fabrique le site de Meli en français et en anglais.

Source unique : src/index.html. Les textes à traduire y sont écrits en français
entre doubles crochets, avec un identifiant :  [[accueil.titre|Prends soin de toi]]
Les traductions anglaises sont dans i18n/en.json :
    "accueil.titre": {"fr": "Prends soin de toi", "en": "Take care of yourself"}
Le champ "fr" sert à repérer une traduction devenue obsolète quand le français change.

Usage : python3 build.py          -> écrit index.html (fr) et en/index.html (en)
        python3 build.py --sync   -> ajoute dans en.json les clés manquantes (en vide)
Le script s'arrête avec une erreur s'il manque une traduction, si une traduction
n'est plus à jour, ou s'il trouve un tiret cadratin ou demi-cadratin.
"""
import json, re, sys
from pathlib import Path

ICI = Path(__file__).parent
SRC = ICI / "src" / "index.html"
EN_JSON = ICI / "i18n" / "en.json"
SEG = re.compile(r"\[\[([a-z0-9_.\-]+)\|(.*?)\]\]", re.S)

LANGUES = {
    "fr": dict(sortie=ICI / "index.html", root="", href_fr="index.html", href_en="en/index.html", actif_fr="actif", actif_en=""),
    "en": dict(sortie=ICI / "en" / "index.html", root="../", href_fr="../index.html", href_en="index.html", actif_fr="", actif_en="actif"),
}


def segments(texte):
    vus = {}
    for cle, fr in SEG.findall(texte):
        if cle in vus and vus[cle] != fr:
            sys.exit(f"Erreur : la clé {cle} a deux textes français différents.")
        vus[cle] = fr
    return vus


def main():
    gabarit = SRC.read_text(encoding="utf-8")
    fr = segments(gabarit)
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
    inutiles = sorted(set(en) - set(fr))
    if problemes:
        sys.exit("Erreur :\n  " + "\n  ".join(problemes))

    for lang, conf in LANGUES.items():
        page = SEG.sub(lambda m: m.group(2) if lang == "fr" else en[m.group(1)]["en"], gabarit)
        for var in ("root", "href_fr", "href_en", "actif_fr", "actif_en"):
            page = page.replace("{{" + var + "}}", conf[var])
        page = page.replace("{{lang}}", lang)
        if re.search(r"\{\{\w+\}\}|\[\[", page):
            sys.exit(f"Erreur : un marqueur n'a pas été remplacé dans la version {lang}.")
        if re.search("[–—]", page):
            sys.exit(f"Erreur : tiret cadratin ou demi-cadratin dans la version {lang}.")
        conf["sortie"].parent.mkdir(exist_ok=True)
        conf["sortie"].write_text(page, encoding="utf-8")
        print(f"{lang} -> {conf['sortie'].relative_to(ICI)}")
    if inutiles:
        print("Clés anglaises qui ne servent plus : " + ", ".join(inutiles))


if __name__ == "__main__":
    main()
