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
| CNN 3D IRM seule, moyenne de 5 graines, 40 époques (notebook 14) | 0,541 (1 essai) | 0,630 ± 0,050 (0,58 à 0,70) |
| CNN 3D IRM seule, 5 graines, arrêt anticipé | — | 0,536 ± 0,020 |
| CNN 3D IRM + PET + tableau, 5 graines, 40 époques | 0,635 (1 essai) | 0,649 ± 0,041 |
| CNN 3D IRM + PET + tableau, 5 graines, arrêt anticipé | 0,644 (1 essai) | 0,627 ± 0,047 |
| CNN 3D PET seule, arrêt anticipé (1 essai) | 0,569 ± 0,056 | 0,414 ± 0,231 |
| CNN 3D IRM + PET, arrêt anticipé (1 essai) | 0,487 ± 0,066 | 0,503 ± 0,179 |

Le premier score du CNN sur l'IRM (0,714, publié le 9 nov. au soir) était un coup de chance : relancé avec 5 graines,
le même modèle donne 0,58 à 0,70. Le même code a aussi donné deux scores différents sur deux exécutions (calcul GPU non
reproductible). L'arrêt anticipé de la fiche dégrade l'IRM seule (validation sur 14 patients, trop peu).

Notebook 15 (images alignées, 85 patients, PCA à 10, 20, 30 et 50 composantes) : la PCA varie sans logique avec k
(IRM + régression logistique : 0,600 / 0,671 / 0,694 / 0,609) ; PCA IRM+PET 50 composantes + RF 0,630 ; anciennes
5 statistiques 0,47 (RF) et 0,44 (LR). Tabulaire + régions IRM/PET (RF) 0,711 ; tabulaire + PCA IRM+PET 50 composantes
(RF) 0,709 ; tabulaire seul 0,709 / 0,700.

### Lecture honnête
- L'alignement a rendu les images **informatives** : avant on était au hasard, maintenant 0,6 à 0,7.
- La fusion **n'améliore pas** le tableau (+0,002) : RQ1 = pas de gain mesurable.
- Le tableau baisse de 0,741 à 0,709 : c'est la vraie performance, la cible d'avant contenait des patients déjà aggravés.
- Avec 85 patients, l'écart-type entre plis est de 0,05 à 0,15 : un écart inférieur à ~0,05 n'est pas distinguable du bruit.
- Le CNN 3D est instable (voir plus haut) : sur 85 patients il n'est pas meilleur que les mesures par région (0,62) et reste
  sous le tableau (0,71). Aucun score de CNN isolé n'est fiable ; rapporter la moyenne sur plusieurs graines.
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

1. Envoyer à Nourchene : `docs/Document_pour_Nourchene.docx` et `outputs/livrables_membre_A.zip` (dossier
   `outputs/livrables_membre_A/`, avec LISEZMOI ; ignoré par git, aucun identifiant de patient).
2. Décisions communes : garder ou non les 27 patients déjà déments ; appliquer la nouvelle cible aux 359 (relancer ses
   notebooks 08, 11, 12 pour rester comparables) ; qui relance le notebook 07 pour l'âge ; qui pousse les chemins sur git.
3. Phase 4 : tableau comparatif unique, choix du modèle final (critères : AUC, stabilité, réponse aux RQ, simplicité),
   présentation avec une conclusion par RQ et la partie pipeline Big Data (Nourchene : notebook 13).
4. Pistes si le temps le permet : répéter la validation croisée pour tous les modèles, mesurer des régions plus fines,
   élargir au-delà de 112 patients (le même alignement marcherait pour d'autres).
5. Mise en conformité avec la fiche faite le 9 nov. au soir : écart-type et 4 métriques (notebooks 10 et 14), arrêt anticipé
   du CNN, PCA jusqu'à 50 composantes. L'étude de stabilité du CNN (5 graines) a été faite par un script non versionné ;
   ses résultats sont dans `livrables_membre_A/3_stabilite_CNN/`.

## Attention : fichiers de résultats

Les notebooks enregistrent dans `data/05_Manifestes/cohorte_359_*/` (dossiers datés, ignorés par git) :
`fusion_RQ1_RQ3_corrigee_*`, `representations_image_*`, `cnn_3d_corrigee_*`, `features_image_mni_*`.
