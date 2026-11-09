# Changements en cours côté Membre A, et pourquoi

Salut Nourchene. Voici ce qu'on modifie de mon côté et les raisons. Aucun de tes notebooks (00 à 13) n'est
changé dans sa logique, et tes données ne sont pas touchées. Tout est sur la branche `membre-a-corrections`.

## 1. Chemins rendus portables (touche tes fichiers)

- `configs/config_projet.py` : la racine du projet est maintenant trouvée automatiquement (dossier parent de `configs/`).
- Notebooks 07 à 14 : `sys.path.append(r"E:\Projet_Alzheimer\configs")` devient `sys.path.append(r"..\configs")`.

**Pourquoi :** le projet doit tourner sur mon PC comme sur ton disque `E:`, sans modifier les chemins à chaque fois.
**À faire :** une seule de nous deux pousse ce changement, sinon on aura des conflits. Lance les notebooks depuis le
dossier `notebooks/`.

## 2. Problèmes trouvés dans les données

| Problème | Chiffre |
|---|---|
| La cible `progression` compare le **premier** diagnostic au dernier, mais l'image est prise en moyenne **2 ans plus tard** (jusqu'à 11 ans) | 14 des 45 « progresseurs » étaient déjà aggravés au moment de l'image ; 12 étiquettes sur 112 changent une fois corrigée |
| `age_reference` est vide dans `jeu_modelisation_359.csv` | 0 % rempli, donc l'âge est absent de tous les modèles |
| Les IRM ne sont pas alignées entre patients (6 tailles différentes, étirées en 64³ sans recalage ni retrait du crâne) | un même point du cube ne correspond pas à la même zone du cerveau |
| Notebook 14 : l'augmentation retournait le dernier axe, qui est avant-arrière pour l'IRM | corrigé |

**Conséquence :** nos résultats actuels (tableau 0,74, fusion 0,72, CNN 0,64, images seules ≈ 0,5) ne prouvent pas que
les images n'aident pas. Elles sont mal préparées.

## 3. Ce que j'ai ajouté (nouveaux fichiers, rien d'écrasé)

- `notebooks/07b_cible_ancree_image.ipynb` : nouvelle cible `progression_image` calculée à partir de la **date de l'image**
  (diagnostic de départ = celui de l'image, arrivée = pire diagnostic après l'image), variables du tableau mesurées à
  cette date, âge calculé. Les 27 patients déjà déments à l'image sont marqués (`deja_dement`) : ils ne peuvent pas s'aggraver.
- `src/alignement_mni.py` : recalage des IRM et des PET sur un cerveau de référence (MNI), retrait du crâne, cubes 64³
  communs, et mesures par région (hippocampe, ventricules, temporal...). Notebook `09b` à venir pour le lancer.
- `notebooks/10_...` et `14_...` (ceux que tu m'as envoyés), le 14 avec le retournement corrigé.

## 4. Ce qu'il faut décider ensemble

- [ ] Garde-t-on les 27 patients déjà déments, ou travaille-t-on sur les 85 patients « à risque » ?
- [ ] Veux-tu appliquer la nouvelle définition de la cible aux 359 patients (donc relancer tes notebooks 08, 11, 12) ?
      Si oui, les chiffres de nos deux parties restent comparables ; sinon ils ne le sont plus.
- [ ] Qui relance le notebook 07 pour récupérer l'âge ? (cause probable : le CSV a été enregistré avant que le calcul
      de l'âge soit ajouté ; 07b le recalcule déjà pour les 112.)

Plus de détails : `docs/ETAT_AVANCEMENT_MEMBRE_A.md`.
