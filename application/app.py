"""CogniSuivi — application d'aide au suivi du risque d'aggravation cognitive.

Lancement :
    python app.py
puis ouvrir http://127.0.0.1:5000 dans un navigateur.

Le modele est produit par le notebook 22 et lu dans modele/.
Aucune donnee saisie n'est enregistree : tout est calcule en memoire.
"""
from pathlib import Path
import json
import math

import numpy as np
from flask import Flask, jsonify, render_template, request

BASE = Path(__file__).resolve().parent
DOSSIER_MODELE = BASE / "modele"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


@app.template_filter("fr")
def format_fr(valeur):
    """Affiche un nombre avec la virgule decimale francaise."""
    return str(valeur).replace(".", ",")


# --------------------------------------------------------------------------- modele
def charger_modele():
    """Charge le modele et sa fiche. Renvoie (modele, fiche, message d'erreur)."""
    fichier = DOSSIER_MODELE / "modele_final.joblib"
    fiche_json = DOSSIER_MODELE / "modele_final.json"
    if not fichier.exists() or not fiche_json.exists():
        return None, None, (
            "Le modèle n'a pas encore été généré. Exécutez le notebook "
            "22_export_modele_application.ipynb, puis relancez l'application."
        )
    try:
        import joblib
        charge = joblib.load(fichier)
        fiche = json.loads(fiche_json.read_text(encoding="utf-8"))
        return charge, fiche, None
    except Exception as erreur:            # pragma: no cover
        return None, None, f"Le modèle n'a pas pu être chargé : {erreur}"


MODELE, FICHE, ERREUR_MODELE = charger_modele()


# --------------------------------------------------------------------------- champs
# Description de chaque variable : libelle, aide, bornes, et valeurs possibles
# pour les champs a choix. Sert a construire le formulaire automatiquement.
CHAMPS = {
    "code_dx": {
        "libelle": "Un trouble de la mémoire a-t-il été constaté ?",
        "aide": "Tel qu'indiqué lors de la dernière consultation.",
        "choix": [(1, "Non, bilan normal"), (2, "Oui, un trouble léger")],
    },
    "MMSE": {
        "libelle": "Test de mémoire",
        "aide": "Score sur 30. Noté « MMSE » sur le compte rendu.",
        "min": 0, "max": 30, "pas": 1, "unite": "sur 30",
    },
    "CDR_global": {
        "libelle": "Retentissement sur la vie courante",
        "aide": "Noté « CDR » sur le compte rendu.",
        "choix": [(0, "Aucun"), (0.5, "Très léger"), (1, "Léger"),
                  (2, "Modéré"), (3, "Important")],
    },
    "CDR_SB": {
        "libelle": "Retentissement, score détaillé",
        "aide": "De 0 à 18. Noté « CDR-SB » sur le compte rendu.",
        "min": 0, "max": 18, "pas": 0.5, "unite": "sur 18",
    },
    "ADAS13": {
        "libelle": "Bilan cognitif approfondi",
        "aide": "De 0 à 85. Noté « ADAS » sur le compte rendu. Plus le score monte, "
                "plus les difficultés sont marquées.",
        "min": 0, "max": 85, "pas": 1, "unite": "sur 85",
    },
    "FAQ": {
        "libelle": "Autonomie au quotidien",
        "aide": "De 0 à 30. Noté « FAQ » sur le compte rendu.",
        "min": 0, "max": 30, "pas": 1, "unite": "sur 30",
    },
    "sexe": {
        "libelle": "Sexe",
        "aide": "",
        "choix": [(1, "Homme"), (2, "Femme")],
    },
    "education": {
        "libelle": "Années d'études",
        "aide": "Nombre total d'années de scolarité.",
        "min": 0, "max": 30, "pas": 1, "unite": "ans",
    },
    "APOE_e4": {
        "libelle": "Recherche génétique APOE",
        "aide": "À renseigner seulement si une analyse génétique a été réalisée.",
        "choix": [(0, "Aucune copie"), (1, "Une copie"), (2, "Deux copies")],
    },
    "age": {
        "libelle": "Âge",
        "aide": "",
        "min": 40, "max": 120, "pas": 1, "unite": "ans",
    },
}

ORDRE_VISITE = ["code_dx", "MMSE", "CDR_global", "CDR_SB", "ADAS13", "FAQ"]
ORDRE_PROFIL = ["sexe", "age", "education", "APOE_e4"]


def decomposer(variable):
    """'MMSE_visite2' -> ('MMSE', 2) ; 'pente_MMSE' -> ('MMSE', 'pente') ; sinon (nom, None)."""
    if variable.startswith("pente_"):
        return variable[len("pente_"):], "pente"
    if "_visite" in variable:
        base, numero = variable.rsplit("_visite", 1)
        return base, int(numero)
    return variable, None


def groupes_formulaire(variables):
    """Construit les groupes de champs a afficher, a partir des variables du modele."""
    visites, profil = {}, []
    for v in variables:
        base, marque = decomposer(v)
        if marque == "pente":
            continue                       # calculee, jamais saisie
        if base not in CHAMPS:
            continue
        if marque is None:
            (profil if base in ORDRE_PROFIL else visites.setdefault(1, [])).append((v, base))
        else:
            visites.setdefault(marque, []).append((v, base))

    def trier(paires, ordre):
        rang = {n: i for i, n in enumerate(ordre)}
        return sorted(paires, key=lambda p: rang.get(p[1], 99))

    groupes = []
    if profil:
        groupes.append({"titre": "Informations générales", "champs": [
            dict(CHAMPS[base], nom=v) for v, base in trier(profil, ORDRE_PROFIL)]})
    for numero in sorted(visites):
        titre = ("Résultats des tests" if len(visites) == 1
                 else f"Tests — consultation {numero}"
                      + (" (la plus récente)" if numero == max(visites) else ""))
        groupes.append({"titre": titre, "champs": [
            dict(CHAMPS[base], nom=v) for v, base in trier(visites[numero], ORDRE_VISITE)]})
    return groupes


GROUPES = groupes_formulaire(FICHE["variables"]) if FICHE else []
SEUIL = float(FICHE["seuil_alerte"]) if FICHE else 0.5


# --------------------------------------------------------------------------- calcul
def vecteur(donnees, variables):
    """Transforme la saisie en une ligne de variables, dans l'ordre du modele.

    Les champs laisses vides restent absents : la chaine du modele les remplit
    avec la mediane apprise a l'entrainement.
    """
    ligne = []
    for v in variables:
        base, marque = decomposer(v)
        if marque == "pente":
            derniere = max((n for _, n in map(decomposer, variables)
                            if isinstance(n, int)), default=None)
            debut = donnees.get(f"{base}_visite1")
            fin = donnees.get(f"{base}_visite{derniere}") if derniere else None
            ligne.append(fin - debut if (debut is not None and fin is not None) else math.nan)
        else:
            valeur = donnees.get(v)
            ligne.append(math.nan if valeur is None else float(valeur))
    return np.array([ligne], dtype=float)


def probabilite(ligne):
    modele = MODELE["modele"]
    if MODELE["type"] == "Ensemble":
        return float((modele["logreg"].predict_proba(ligne)[0, 1]
                      + modele["foret"].predict_proba(ligne)[0, 1]) / 2)
    return float(modele.predict_proba(ligne)[0, 1])


def niveau(p):
    """Trois paliers de lecture, construits autour du seuil retenu."""
    if p < SEUIL * 0.6:
        return ("faible", "Risque faible",
                "Les éléments indiqués ne font pas ressortir de risque particulier. "
                "Il n'y a pas lieu de modifier le suivi habituel.")
    if p < SEUIL:
        return ("modere", "Risque intermédiaire",
                "Les éléments indiqués méritent d'être revus avec un médecin lors "
                "d'une prochaine consultation.")
    return ("eleve", "Risque élevé",
            "Il est conseillé d'en parler à un médecin. Ce résultat ne signifie pas "
            "qu'une aggravation surviendra : il invite simplement à être suivi de près.")


# --------------------------------------------------------------------------- pages
def contexte_commun():
    perf = (FICHE or {}).get("performance_test_independant", {})
    return {
        "erreur_modele": ERREUR_MODELE,
        "fiche": FICHE,
        "perf": perf,
        "seuil": SEUIL,
        "seuil_pct": round(SEUIL * 100),
    }


@app.route("/")
def accueil():
    return render_template("index.html", groupes=GROUPES, **contexte_commun())


@app.route("/api/prediction", methods=["POST"])
def api_prediction():
    if MODELE is None:
        return jsonify({"erreur": ERREUR_MODELE}), 503

    recu = request.get_json(silent=True) or {}
    donnees, invalides = {}, []
    for v in FICHE["variables"]:
        base, marque = decomposer(v)
        if marque == "pente" or base not in CHAMPS:
            continue
        brut = recu.get(v)
        if brut is None or str(brut).strip() == "":
            continue
        try:
            valeur = float(str(brut).replace(",", "."))
        except ValueError:
            invalides.append(CHAMPS[base]["libelle"])
            continue
        borne_bas, borne_haut = CHAMPS[base].get("min"), CHAMPS[base].get("max")
        if borne_bas is not None and not (borne_bas <= valeur <= borne_haut):
            invalides.append(f"{CHAMPS[base]['libelle']} (attendu entre "
                             f"{borne_bas} et {borne_haut})")
            continue
        donnees[v] = valeur

    if invalides:
        return jsonify({"erreur": "Valeurs hors limites : " + ", ".join(invalides)}), 400
    if not donnees:
        return jsonify({"erreur": "Renseignez au moins une information pour lancer le calcul."}), 400

    p = probabilite(vecteur(donnees, FICHE["variables"]))
    classe, titre, phrase = niveau(p)
    total = len([v for v in FICHE["variables"] if decomposer(v)[1] != "pente"])
    return jsonify({
        "probabilite": round(p, 4),
        "pourcentage": round(p * 100, 1),
        "seuil": SEUIL,
        "alerte": bool(p >= SEUIL),
        "classe": classe,
        "titre": titre,
        "phrase": phrase,
        "renseignes": len(donnees),
        "total": total,
    })


if __name__ == "__main__":
    if ERREUR_MODELE:
        print("Attention :", ERREUR_MODELE)
    app.run(debug=False, port=5000)
