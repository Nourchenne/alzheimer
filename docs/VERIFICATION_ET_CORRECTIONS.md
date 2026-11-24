# Vérification des notebooks 11, 12, 13, 18 à 22 et de l'application, et corrections

Date : 24 novembre 2026. Branche : `verification`. Aucune donnée ADNI ni identifiant de patient dans ce fichier.

## 1. Vérification : tout est reproductible

Les notebooks ont été exécutés sur un second ordinateur (Windows, Python 3.12, scikit-learn 1.9) : les chiffres sont retrouvés.

| Notebook | Résultat annoncé | Résultat obtenu |
|---|---|---|
| 18 cohorte élargie | 1 185 patients, 17,8 % d'aggravations | identique |
| 19 entraînement | AUC 0,825 | 0,825 ± 0,038 |
| 21 test indépendant | AUC 0,898 (0,838 à 0,944), 187 patients, 23 aggravations | identique (avant correction) |
| 11 modèles (cible initiale) | random forest 0,814 | 0,814 (autres modèles à ±0,02) |
| 12 longitudinal | statique 0,70, longitudinal 0,76 | identique à ±0,01 |
| 13 Spark | 5 comptages identiques à pandas | identiques ; temps plus courts (autre machine) |
| Application | fonctionne | page, formulaire, cas d'erreur : corrects |

## 2. Problèmes constatés, mesurés, puis corrigés

### A. Probabilités gonflées dans l'application (notebook 22, `application/app.py`)
`class_weight="balanced"` fait croire au modèle que la moitié des patients s'aggrave. Le classement des patients est bon
(AUC inchangée) mais le pourcentage affiché ne l'était pas : 35 % annoncés en moyenne pour 14 % de risque réel
(un patient normal aux scores parfaits : 24,8 %).

**Correction :** calibration de Platt apprise sur des prédictions hors échantillon (validation croisée), enregistrée dans
le modèle et appliquée par l'application. Le seuil d'alerte est converti en probabilité calibrée (même décision).

| | Avant | Après |
|---|---|---|
| Probabilité moyenne affichée (risque réel 14,4 %) | 34,7 % | 14,4 % |
| Profil normal, scores parfaits, 68 ans | 24,8 % (risque intermédiaire) | 6,7 % (risque faible) |
| Profil normal, 60 ans | 9,1 % | 2,6 % |
| Profil trouble léger, scores moyens | 43,4 % | 14,9 % |
| Profil trouble léger, scores dégradés | 99,3 % | 89,8 % |

Contrôle de calibration après correction (5 groupes de 155 patients, prédit → observé) :
2,2 → 0,6 % ; 4,5 → 3,2 % ; 7,2 → 7,1 % ; 12,7 → 15,5 % ; 45,3 → 45,8 %.

### B. Question 2 : le gain du suivi dans le temps n'est pas robuste (notebook 12)
Le notebook 12 gardait les patients **déjà déments à la 3e visite** (43 sur 352), qui ne peuvent pas s'aggraver, alors que le
reste du projet les exclut. **Correction :** exclusion (`EXCLURE_DEJA_DEMENTS = True`) et mesures prises avant la visite.

| Situation | Statique (meilleur) | Longitudinal (meilleur) | Gain | Plis gagnés |
|---|---|---|---|---|
| Avant correction (352 patients) | 0,703 | 0,765 | +0,061 | 5/5 |
| Sans les déjà déments (309) | 0,773 | 0,751 | −0,022 | 2/5 |
| Sans les déjà déments, mesures avant la visite (309) | 0,761 | 0,744 | −0,016 | 1/5 |

Le résultat est cohérent avec les notebooks 20 (+0,014 sur 631 patients) et 21 (modèle final statique). **Conclusion
honnête : sur nos données, suivre 3 visites au lieu d'une n'apporte pas de gain mesurable** (de −0,02 à +0,01 selon la
définition, toujours moins que l'écart-type entre plis). Perte quand la 2e visite manque (BiLSTM) : 0,744 → 0,719.

### C. Mesures prises avant la date de référence et codes « −1 » (notebooks 21 et 22)
- Les scores étaient rattachés à la mesure **la plus proche à ± 90 jours** : une mesure faite jusqu'à 90 jours **après** la
  visite pouvait entrer dans le modèle. Désormais : la mesure la plus récente **avant** la visite (`direction="backward"`).
- Dans les tables ADNI, **−1 signifie « valeur manquante »** (133 fois pour le CDR global, 14 pour le MMSE, 32 pour le FAQ).
  Ils sont maintenant remplacés par des valeurs manquantes. Impact mesuré : négligeable (1 patient sur 771 dans le modèle final).
- Conséquence : la sélection automatique du notebook 21 aurait basculé vers un modèle longitudinal (note 0,853 contre
  0,838) pour un gain inférieur au bruit. On a donc ajouté la **règle de parcimonie « d'une erreur-type »** : parmi les
  configurations à moins d'un écart-type de la meilleure, on retient la plus simple. Le modèle final reste la
  **régression logistique statique, 10 variables** (6 configurations à moins d'un écart-type).

| Notebook 21 | Avant | Après |
|---|---|---|
| Note de développement (optimiste, a servi au choix) | 0,864 ± 0,023 | 0,838 ± 0,035 |
| **AUC sur le test indépendant** (187 patients, 23 aggravations) | 0,898 (0,838 à 0,944) | **0,896** (0,832 à 0,945) |
| Sensibilité / spécificité au seuil choisi sur le développement | 0,870 / 0,774 | 0,826 / 0,811 |
| Aggravations détectées / fausses alertes | 20 sur 23 / 37 | 19 sur 23 / 31 |

Le résultat du test est stable ; l'estimation de développement, plus honnête, passe de 0,864 à 0,838. Une estimation
prudente de la performance est donc **environ 0,85 à 0,90**.

## 3. Ce qui a été mesuré et ne pose pas de problème
- L'AUC du test n'est pas « circulaire » : l'état de départ (normal / trouble léger) seul donne 0,635 ; le modèle 0,898.
  Dans les troubles légers seuls : 0,919 (18 aggravations) ; chez les normaux : 0,725 (**5 aggravations seulement** : non
  concluant).
- Les « indicateurs de présence », le gradient boosting et les modèles séparés (notebook 20) n'apportent aucun gain :
  le plafond ne vient pas du choix du modèle.

## 4. À savoir
- Le seuil d'alerte (environ 12 % de risque calibré) est un seuil de **dépistage** : il détecte 83 % des aggravations au
  prix de fausses alertes (valeur prédictive positive 0,38). Dans l'application, « Risque élevé » signifie « au-dessus du
  seuil d'alerte », pas « probable ».
- Le jeu de test ne contient que 23 aggravations : l'intervalle de confiance est large (0,83 à 0,95).
- Les temps de calcul de Spark dépendent de la machine ; les comptages, eux, sont identiques à pandas.

## 5. Fichiers modifiés
`notebooks/12_longitudinal_LSTM.ipynb`, `21_modele_final_longitudinal.ipynb`, `22_export_modele_application.ipynb`,
`application/app.py`, `application/modele/modele_final.json`, `requirements.txt`. Le fichier du modèle
(`modele_final.joblib`) n'est pas versionné : il se régénère avec le notebook 22.
