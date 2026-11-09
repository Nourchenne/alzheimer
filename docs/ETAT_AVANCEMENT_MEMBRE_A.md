# État d'avancement — Membre A (imagerie et deep learning)

Dernière mise à jour : 9 novembre 2026. Ce fichier ne contient aucune donnée ADNI (chiffres agrégés seulement).

## Résultats obtenus (112 patients, cible `progression` du notebook 07, 5 plis, `random_state=0`)

| Modèle | ROC-AUC |
|---|---|
| Tableau seul (notebook 10) | 0,741 |
| Fusion tableau + 5 statistiques d'image (notebook 10) | 0,717 |
| CNN 3D IRM + PET + tableau (notebook 14) | 0,635 ± 0,093 |
| CNN 3D PET seule / IRM seule / IRM + PET | 0,544 / 0,541 / 0,508 |

RQ3 (notebook 10) : sans l'imagerie 0,731 ; sans le tableau 0,485.
Conclusion provisoire : les images n'apportent rien, **mais** elles sont mal préparées (voir problèmes).

## Problèmes trouvés (détail dans le document partagé avec Nourchene)

1. Cible décalée dans le temps par rapport à l'image (12 étiquettes sur 112 changent une fois corrigée).
2. IRM non alignées entre patients (6 tailles différentes, étirées en 64³ sans recalage).
3. Retournement des IRM sur le mauvais axe dans le notebook 14 (corrigé).
4. 5 statistiques d'image quasi constantes d'un patient à l'autre.
5. Âge vide dans `jeu_modelisation_359.csv` (corrigé dans 07b).
6. Très petit effectif.

## Fait aujourd'hui

- Chemins rendus portables : `configs/config_projet.py` (racine = dossier parent de `configs/`) et
  `sys.path.append(r"..\configs")` dans les notebooks 07 à 14.
- Notebooks 10 et 14 ajoutés (fournis par Nourchene).
- **Notebook 14 corrigé** : retournement gauche-droite sur le bon axe de chaque modalité (`AXE_GD`).
- **Notebook 07b créé et exécuté** : cible `progression_image` ancrée sur la date de l'image, variables du tableau
  mesurées à cette date, âge rempli (100 %). 85 patients « à risque » (35 qui progressent), 27 déjà déments.
  Sortie : `data/05_Manifestes/cohorte_359_*/cible_ancree_image_*/jeu_modelisation_112_ancre.csv`.
- **Module `src/alignement_mni.py` écrit et testé sur 5 patients** : recalage IRM (rigide puis affine) sur le modèle MNI
  avec crâne, retrait du crâne, correction N4, PET recalé via l'IRM du même patient, cubes 64³, mesures par région
  (hippocampe, amygdale, ventricules, temporal, pariétal postérieur, cingulaire postérieur, frontal).
- Modèles MNI et atlas téléchargés dans `data/08_Modele_MNI` (ignoré par git).
- Environnement : `.venv` avec PyTorch 2.7.1 + CUDA 11.8, pandas 2.2.3 (pandas 3.x est bloqué par Windows Smart App
  Control), antspyx, nilearn. Noyau Jupyter « Python (alzheimer GPU) ». `jupyter.exe` est bloqué par Windows : exécuter
  un notebook avec `python run_nb.py` (nbclient) ou depuis JupyterLab lancé par `python -m jupyterlab`.

## Ce qui reste à faire (dans l'ordre)

1. **Notebook 09b** : boucle sur les 112 patients avec `alignement_mni.traiter_patient` (≈ 25 à 50 s par patient,
   environ 1 h en tout), reprise possible, tableau de qualité, montage visuel des 112 cerveaux.
   Contrôle : `IRM_info_mutuelle` doit être proche de −0,70 (alerte si > −0,60) ; `PET_corr_matiere_grise` > 0,2.
   Le patient `128_S_0135` a eu un PET à 0,173 après 3 essais : à regarder à l'œil.
2. Brancher les notebooks **10 et 14** sur les données corrigées (nouvelle cible + volumes MNI), avec un interrupteur
   « ancien / corrigé » pour garder le tableau avant / après. Décider : exclure ou non les 27 patients déjà déments.
3. **Notebook 15** : PCA (20 à 50 composantes par modalité, calculée dans chaque pli d'apprentissage seulement)
   + mesures par région ; comparer 5 statistiques / PCA / CNN / régions.
4. Envoyer à Nourchene les fichiers de résultats (RQ1_comparaison, RQ3_robustesse, importance_fusion, resultats_CNN)
   et le document de plan ; décider avec elle : plan complet, cible des 359, qui pousse les chemins sur git.

## À savoir

- Le recalage ANTs utilise un échantillonnage aléatoire : un recalage peut rarement échouer. Le module mesure la
  qualité et réessaie automatiquement. Une initialisation aléatoire testée au départ ratait 1 fois sur 3 (abandonnée).
