# Prédiction de la progression de la maladie d'Alzheimer (ADNI)

Projet Big Data & Deep Learning — construction d'une cohorte multimodale
longitudinale (IRM + PET + données cliniques/cognitives + biomarqueurs) à
partir de la base **ADNI**, puis modélisation de la progression.

## ⚠️ Données non incluses

Ce dépôt **ne contient aucune donnée ADNI** (images, tables, manifestes,
identifiants de participants). L'accès à ADNI est soumis à un accord
d'utilisation qui **interdit la redistribution** des données. Seul le **code**
est versionné ; les sorties des notebooks sont retirées automatiquement
(voir `nbstripout` ci-dessous).

Pour exécuter le projet, il faut disposer de son propre accès ADNI et placer
les données dans un dossier `data/` local (ignoré par git).

## Pipeline (notebooks)

| Notebook | Rôle |
|----------|------|
| `00_configuration` | Mise en place de l'arborescence |
| `01_inventaire_donnees` | Inventaire des tables ADNI |
| `02_selection_cohorte` | Sélection de la cohorte (359 participants) |
| `03_collecte_cohorte_359` | Manifestes et listes de téléchargement IRM |
| `04_verification_telechargements` | Contrôle qualité des IRM téléchargées |
| `05_collecte_PET` | Collecte et contrôle des PET |
| `06_preparation_visites` | QC, harmonisation, conversion NIfTI (112) |
| `07_cibles_et_tabulaire` | Cibles de prédiction + variables tabulaires |
| `08_baseline_tabulaire` | Baseline (régression logistique, random forest) |
| `09_pretraitement_images` | Prétraitement des volumes IRM/PET (64³) |
| `10_fusion_RQ1_RQ3` | Fusion multimodale (RQ1) + robustesse (RQ3) |
| `11_comparaison_modeles` | Comparaison de modèles, choix final justifié |

## Questions de recherche

- **RQ1** : la fusion multimodale améliore-t-elle la prédiction vs unimodal ?
- **RQ2** : le longitudinal améliore-t-il vs une visite unique ?
- **RQ3** : le modèle résiste-t-il à une modalité manquante ?

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Confidentialité des sorties

Les notebooks affichent des identifiants et des valeurs ADNI. Pour éviter de
les versionner, ce dépôt utilise **nbstripout** (filtre git qui retire les
sorties au moment du commit, tout en les gardant en local) :

```bash
pip install nbstripout
nbstripout --install
```
