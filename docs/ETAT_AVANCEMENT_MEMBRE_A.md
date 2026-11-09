# État d'avancement — Membre A (imagerie et deep learning)

Dernière mise à jour : 9 novembre 2026 (soir). Ce fichier ne contient aucune donnée ADNI (chiffres agrégés seulement).

## Où on en est

Les phases 1, 2 et 3 de Membre A sont faites **sur des données corrigées** : nouvelle cible ancrée sur l'image, âge rempli,
images alignées sur le cerveau de référence MNI. Il reste la synthèse commune avec Nourchene et la présentation.

## Résultats avant / après corrections (ROC-AUC, validation croisée 5 plis, `random_state=0`)

Attention : ce n'est pas exactement le même échantillon. Avant : 112 patients, cible `progression` du notebook 07.
Après : 85 patients « à risque » (pas encore déments à la date de l'image, 35 qui s'aggravent), cible `progression_image`.

| Modèle | Avant | Après |
|---|---|---|
| Tableau seul (random forest, notebook 10) | 0,741 | 0,709 |
| Imagerie IRM seule (statistiques → mesures par région) | 0,546 | 0,621 |
| Imagerie PET seule | 0,475 | 0,590 |
| Imagerie IRM + PET | 0,441 | 0,590 |
| Fusion tableau + imagerie | 0,717 | 0,711 |
| RQ3 : sans l'imagerie au test | 0,731 | 0,736 |
| RQ3 : sans le tableau au test | 0,485 | 0,624 |
| CNN 3D IRM seule (notebook 14) | 0,541 | **0,714 ± 0,103** |
| CNN 3D IRM + PET | 0,508 | 0,637 ± 0,084 |
| CNN 3D IRM + PET + tableau | 0,635 | 0,669 ± 0,119 |
| CNN 3D PET seule | 0,544 | 0,491 ± 0,086 |

Notebook 15 (images alignées, 85 patients) : meilleure représentation d'image seule = PCA IRM 20 composantes + régression
logistique (0,671) ; PCA PET 10 composantes 0,629 ; anciennes 5 statistiques 0,47 (RF) et 0,44 (LR).
Tabulaire + régions IRM/PET (RF) 0,711 ; tabulaire + PCA IRM+PET 10 composantes (LR) 0,697 ; tabulaire seul 0,709 / 0,700.

### Lecture honnête
- L'alignement a rendu les images **informatives** : avant on était au hasard, maintenant 0,6 à 0,7.
- La fusion **n'améliore pas** le tableau (+0,002) : RQ1 = pas de gain mesurable.
- Le tableau baisse de 0,741 à 0,709 : c'est la vraie performance, la cible d'avant contenait des patients déjà aggravés.
- Avec 85 patients, l'écart-type entre plis est de 0,05 à 0,15 : un écart inférieur à ~0,05 n'est pas distinguable du bruit.
  Le CNN IRM seule (0,714) est le meilleur de 4 configurations testées : score optimiste, à ne pas surinterpréter.
- RQ3 : le modèle résiste à l'absence d'imagerie, et l'imagerie seule garde un signal (0,62) alors qu'avant elle n'en avait aucun.

## Ce qui a été fait

- Chemins portables : `configs/config_projet.py` (racine automatique) et `sys.path.append(r"..\configs")` dans les notebooks 07 à 15.
- Notebook 14 : retournement gauche-droite corrigé (axe propre à chaque modalité).
- **07b** : cible `progression_image` ancrée sur la date de l'image, variables du tableau à cette date, âge rempli.
  Sortie : `cible_ancree_image_*/jeu_modelisation_112_ancre.csv`. 12 étiquettes sur 112 changent ; 27 patients déjà déments.
- **`src/alignement_mni.py` + 09b** : 112 patients alignés (rigide puis affine sur ICBM152 2009a, crâne retiré, correction N4,
  PET recalé via l'IRM du même patient, cubes 64³, mesures par région). 0 erreur, ≈ 55 min.
  Contrôle visuel : cerveaux moyens nets, montage des 112 cohérent. Le seuil PET (corrélation > 0,2) était trop sévère
  (35 PET sous le seuil, pires cas regardés : corrects).
- **10 et 14** : interrupteur `DONNEES = "initiales" / "corrigees"` et `EXCLURE_DEJA_DEMENTS`, pour garder l'avant / après.
- **15** : comparaison des représentations (5 statistiques, régions, PCA k = 10 et 20, avec ou sans tableau ; PCA calculée
  dans chaque pli d'apprentissage seulement).
- Environnement : `.venv` avec PyTorch 2.7.1 + CUDA 11.8, pandas 2.2.3 (pandas 3.x bloqué par Windows Smart App
  Control), antspyx, nilearn. `jupyter.exe` est bloqué par Windows : exécuter un notebook avec nbclient (script `run_nb.py`
  non versionné) ou depuis JupyterLab lancé par `python -m jupyterlab`.

## Ce qui reste à faire

1. Envoyer à Nourchene : `docs/Document_pour_Nourchene.docx` et les fichiers de résultats (RQ1_comparaison, RQ3_robustesse,
   importance_fusion, resultats_CNN, RQ1_representations).
2. Décisions communes : garder ou non les 27 patients déjà déments ; appliquer la nouvelle cible aux 359 (relancer ses
   notebooks 08, 11, 12 pour rester comparables) ; qui relance le notebook 07 pour l'âge ; qui pousse les chemins sur git.
3. Phase 4 : tableau comparatif unique, choix du modèle final (critères : AUC, stabilité, réponse aux RQ, simplicité),
   présentation avec une conclusion par RQ et la partie pipeline Big Data (Nourchene : notebook 13).
4. Pistes si le temps le permet : plusieurs graines pour le CNN (stabilité), répéter la validation croisée,
   mesurer des régions plus fines, élargir au-delà de 112 patients (le même alignement marcherait pour d'autres).

## Attention : fichiers de résultats

Les notebooks enregistrent dans `data/05_Manifestes/cohorte_359_*/` (dossiers datés, ignorés par git) :
`fusion_RQ1_RQ3_corrigee_*`, `representations_image_*`, `cnn_3d_corrigee_*`, `features_image_mni_*`.
