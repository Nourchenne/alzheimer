# CogniSuivi — application web

Estimation du risque d'aggravation cognitive à deux ans à partir d'une évaluation
clinique standard.

## Installation

Depuis la racine du projet, avec l'environnement virtuel activé :

```
pip install -r application/requirements.txt
```

## Préparer le modèle

L'application a besoin du modèle entraîné. Exécuter le notebook
`22_export_modele_application.ipynb`, qui écrit deux fichiers dans `application/modele/` :

- `modele_final.joblib` — la chaîne complète (imputation, mise à l'échelle, classifieur) ;
- `modele_final.json` — la liste des variables, le seuil d'alerte et les performances.

Tant que ces fichiers sont absents, le site reste consultable mais le formulaire
affiche un message d'indisponibilité.

## Lancer

```
cd application
python app.py
```

Puis ouvrir http://127.0.0.1:5000

## Structure

```
application/
  app.py                  serveur et calcul de la prédiction
  requirements.txt
  modele/                 produit par le notebook 22
  templates/
    base.html             en-tête, pied de page, structure commune
    index.html            page unique : présentation et formulaire d'estimation
  static/
    css/style.css
    js/outil.js
    img/                  visuels vectoriels
```

## Probabilité et explication

**Probabilité calibrée.** Le modèle est entraîné avec `class_weight="balanced"`, qui gonfle ses
probabilités brutes. Le notebook 22 apprend une calibration (méthode de Platt, sur des
prédictions hors échantillon) enregistrée dans le modèle ; `app.py` l'applique avant l'affichage.

**Facteurs du résultat.** Pour une régression logistique, le score est une somme : la contribution
d'une variable vaut `coefficient × valeur centrée-réduite du patient`. `app.py` (fonction
`explication`) liste les plus fortes, parmi les champs renseignés, dans « Ce qui augmente le risque »
et « Ce qui le diminue ». C'est une lecture exacte du calcul, par rapport à un participant moyen.
Le point de départ (`code_dx`) est listé avec un libellé explicite (`LIBELLES_DEPART`) : à scores
égaux, le modèle juge un patient au bilan normal plus à risque, car un faible déclin suffit pour
passer de « normal » à « trouble léger ». Vérifié sur les 771 patients (prédictions hors
échantillon) : avec ADAS 9-15 et CDR-SB 0,5-1, 11 % des patients au bilan normal s'aggravent,
contre 3 % des troubles légers. La calibration est juste dans chaque groupe (normaux : 9,1 %
prédits / 8,3 % observés ; troubles légers : 19,4 % / 20,2 %). Le CDR global n'est pas listé
(`NON_LISTES`) : son effet propre est très faible. Si le modèle exporté n'est plus une régression
logistique, l'explication est simplement masquée.

## Personnalisation

**Le nom.** Remplacer « CogniSuivi » dans `templates/base.html` (en-tête et pied de page)
et dans la balise `<title>` de `index.html`.

**Les couleurs.** Toutes les teintes sont regroupées au début de `static/css/style.css`,
dans le bloc `:root`. Changer `--teal` et `--marine` suffit à modifier l'ensemble du site.

**Les photographies.** Le site fonctionne avec des visuels vectoriels, sans dépendance
externe. Pour utiliser des photographies :

1. déposer les images dans `static/img/` ;
2. dans `templates/index.html`, remplacer le `<img>` de la bannière par la photographie
   souhaitée (format conseillé : 960 × 780 px) ;
3. pour les trois cartes de la section « L'outil », remplacer le bloc
   `<div class="carte__media">…</div>` par
   `<img class="carte__media" src="…" alt="…">` (format conseillé : 680 × 400 px).

N'utiliser que des images dont les droits permettent la diffusion.

## Données et confidentialité

Les valeurs saisies dans le formulaire servent au seul calcul de l'estimation. Elles ne
sont ni journalisées, ni écrites sur disque, ni transmises à un tiers. Aucune donnée
individuelle issue de la cohorte d'origine n'est incluse dans l'application : seul le
modèle entraîné y figure.

## Mention affichée aux utilisateurs

Le site ne publie ni la méthode, ni les données d'origine, ni les limites du modèle :
ces éléments restent dans les notebooks. Seule subsiste une mention courte en pied de
page — « aide à la décision, n'établit pas de diagnostic et ne remplace pas un avis
médical ». Elle est volontairement conservée : un outil qui affiche un risque patient
sans cette précision engage la responsabilité de celui qui le diffuse, et son absence
serait remarquée avant tout par un lecteur averti.
