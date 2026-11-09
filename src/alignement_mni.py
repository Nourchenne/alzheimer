"""Alignement des IRM et des PET sur un cerveau de reference (MNI), pour les 112 patients.

Pourquoi : dans le notebook 09, chaque image etait simplement etiree en 64x64x64, sans etre
alignee. Un meme point du cube ne correspondait donc pas a la meme zone du cerveau d'un patient a
l'autre. Ici, chaque cerveau est ramene dans le meme espace (ICBM152 2009a, 2 mm), le crane est
retire, puis l'image est mise a une taille fixe commune.

Chaine de traitement :
    IRM : recalage affine (12 parametres) sur le modele MNI avec crane
          -> masque cerveau MNI (retire le crane) -> correction du biais d'intensite (N4)
          -> normalisation (z-score dans le cerveau)
    PET : recalage rigide sur l'IRM du MEME patient, puis meme transformation que l'IRM vers le MNI
          -> masque cerveau -> division par la moyenne du cerveau (pseudo-SUVR)
    Les deux : recadrage sur la boite du cerveau MNI puis reechantillonnage en 64x64x64.

Axes des tableaux produits (identiques pour l'IRM et le PET) :
    axe 0 = gauche -> droite,  axe 1 = arriere -> avant,  axe 2 = bas -> haut.
"""
import tempfile
from pathlib import Path

import numpy as np
import nibabel as nib
import ants
from nilearn import datasets
from nilearn.image import resample_to_img
from scipy.ndimage import zoom

TAILLE = 64
# Regions regroupees (atlas Harvard-Oxford). Le texte est cherche dans le nom de la region.
GROUPES_SOUS_CORTICAL = {
    "hippocampe": ["Hippocampus"],
    "amygdale": ["Amygdala"],
    "ventricules": ["Lateral Ventricle"],
}
GROUPES_CORTICAL = {
    "temporal": ["Temporal", "Parahippocampal"],
    "parietal_post": ["Precuneous", "Angular", "Supramarginal"],
    "cingulaire_post": ["Cingulate Gyrus, posterior"],
    "frontal": ["Frontal"],  # region de controle : peu touchee au debut de la maladie
}


class ModeleMNI:
    """Cerveau de reference + masque + atlas, tous sur la meme grille de 2 mm."""

    def __init__(self, dossier):
        dossier = str(dossier)
        d = datasets.fetch_icbm152_2009(data_dir=dossier, verbose=0)
        t1 = ants.image_read(d["t1"])
        self.t1 = ants.resample_image(t1, (2, 2, 2), use_voxels=False, interp_type=4)
        masque = ants.resample_image(ants.image_read(d["mask"]), (2, 2, 2), use_voxels=False, interp_type=1)
        self.masque_img = ants.threshold_image(masque, 0.5, 1e9, 1, 0)
        self.masque = self.masque_img.numpy() > 0
        gm = ants.resample_image(ants.image_read(d["gm"]), (2, 2, 2), use_voxels=False, interp_type=4)
        self.matiere_grise = gm.numpy()
        self.t1_np = self.t1.numpy()

        # Boite qui entoure le cerveau (recadrage commun a tous les patients).
        axes = [np.where(self.masque.any(axis=tuple(j for j in range(3) if j != i)))[0] for i in range(3)]
        self.boite = tuple(slice(max(a.min() - 1, 0), a.max() + 2) for a in axes)

        # Regions de l'atlas, reechantillonnees sur la grille de 2 mm.
        with tempfile.TemporaryDirectory() as tmp:
            fichier = str(Path(tmp) / "t1_2mm.nii.gz")
            ants.image_write(self.t1, fichier)
            ref = nib.load(fichier)
            ref = nib.Nifti1Image(np.zeros(ref.shape, dtype=np.float32), ref.affine)  # grille seule
        self.regions = {}
        for nom_atlas, groupes in [("sub-maxprob-thr25-2mm", GROUPES_SOUS_CORTICAL),
                                   ("cort-maxprob-thr25-2mm", GROUPES_CORTICAL)]:
            atlas = datasets.fetch_atlas_harvard_oxford(nom_atlas, data_dir=dossier, verbose=0)
            lab = np.rint(resample_to_img(atlas.maps, ref, interpolation="nearest", copy_header=True,
                                          force_resample=True).get_fdata()).astype(int)
            noms = list(atlas.labels)
            for groupe, motifs in groupes.items():
                valeurs = [i for i, n in enumerate(noms) if i > 0 and any(m in n for m in motifs)]
                self.regions[groupe] = np.isin(lab, valeurs) & self.masque


def _vers_cube(modele, tableau_2mm):
    """Recadre sur le cerveau MNI puis met a 64x64x64."""
    rec = tableau_2mm[modele.boite]
    facteurs = [TAILLE / s for s in rec.shape]
    return zoom(rec, facteurs, order=1).astype(np.float32)


SEUIL_MI = -0.60     # au-dessus de cette valeur, le recalage de l'IRM est juge rate
SEUIL_PET = 0.20     # en dessous, le recalage du PET est juge rate


def _info_mutuelle(modele, image_alignee):
    return ants.image_similarity(modele.t1, image_alignee, metric_type="MattesMutualInformation")


def _recaler_irm(modele, irm):
    """IRM -> MNI : etape rigide puis affine (initialisation par centre de masse).

    Le recalage utilise un echantillonnage aleatoire : il peut rarement rater. On mesure donc
    l'information mutuelle ; si elle est mauvaise, on reessaie avec un echantillonnage dense.
    (Une initialisation aleatoire testee au depart ratait environ 1 fois sur 3.)
    """
    meilleur, essais = None, 0
    for dense in (False, True):
        essais += 1
        rigide = ants.registration(fixed=modele.t1, moving=irm, type_of_transform="Rigid",
                                   aff_metric="mattes", aff_sampling=32)
        if dense:
            reg = ants.registration(fixed=modele.t1, moving=irm, type_of_transform="Affine",
                                    initial_transform=rigide["fwdtransforms"][0],
                                    aff_metric="mattes", aff_sampling=32, aff_random_sampling_rate=1.0,
                                    aff_iterations=(1000, 500, 250, 50), aff_shrink_factors=(8, 4, 2, 1),
                                    aff_smoothing_sigmas=(4, 2, 1, 0))
        else:
            reg = ants.registration(fixed=modele.t1, moving=irm, type_of_transform="Affine",
                                    initial_transform=rigide["fwdtransforms"][0],
                                    aff_metric="mattes", aff_sampling=32)
        mi = _info_mutuelle(modele, reg["warpedmovout"])
        if meilleur is None or mi < meilleur[1]:
            meilleur = (reg, mi)
        if mi < SEUIL_MI:
            break
    return meilleur[0], meilleur[1], essais


def _recaler_pet(modele, irm, pet, reg_irm):
    """PET -> IRM du meme patient (rigide), puis vers le MNI avec la transformation de l'IRM.

    Controle : une fois aligne, le PET doit etre plus actif dans la matiere grise du modele
    (correlation > 0,2) ; un PET mal aligne donne une correlation proche de 0. Jusqu'a 3 essais.
    """
    m = modele.masque
    meilleur, essais = None, 0
    for _ in range(3):
        essais += 1
        rig = ants.registration(fixed=irm, moving=pet, type_of_transform="Rigid",
                                aff_metric="mattes", aff_sampling=32)
        pet_mni = ants.apply_transforms(fixed=modele.t1, moving=pet, interpolator="linear",
                                        transformlist=reg_irm["fwdtransforms"] + rig["fwdtransforms"])
        c = float(np.corrcoef(pet_mni.numpy()[m], modele.matiere_grise[m])[0, 1])
        if meilleur is None or c > meilleur[1]:
            meilleur = (pet_mni, c)
        if c > SEUIL_PET:
            break
    return meilleur[0], meilleur[1], essais


def traiter_patient(modele, chemin_irm, chemin_pet):
    """Aligne et normalise l'IRM et le PET d'un patient.

    Renvoie (cube_irm, cube_pet, mesures, qc) :
    - cubes de 64x64x64, normalises ;
    - mesures par region du cerveau (matiere grise / liquide pour l'IRM, activite pour le PET) ;
    - qc : indicateurs de qualite de l'alignement.
    """
    irm = ants.image_read(str(chemin_irm))
    pet = ants.image_read(str(chemin_pet))
    m = modele.masque

    # --- IRM -> MNI (rigide puis affine) ---
    reg, mi_irm, essais_irm = _recaler_irm(modele, irm)
    irm_mni = reg["warpedmovout"]
    irm_mni = irm_mni * modele.masque_img  # retire le crane
    try:  # correction du biais d'intensite
        irm_mni = ants.n4_bias_field_correction(irm_mni, mask=modele.masque_img, shrink_factor=2)
    except Exception:
        pass
    irm_np = irm_mni.numpy()
    irm_np[~m] = 0
    mu, sd = irm_np[m].mean(), irm_np[m].std() + 1e-6
    irm_z = np.where(m, (irm_np - mu) / sd, 0).astype(np.float32)

    # --- PET -> IRM du meme patient (rigide), puis -> MNI avec la transformation de l'IRM ---
    pet_mni, corr_pet, essais_pet = _recaler_pet(modele, irm, pet, reg)
    pet_np = pet_mni.numpy()
    pet_np[~m] = 0
    pet_np = np.clip(pet_np, 0, None)
    pet_suvr = np.where(m, pet_np / (pet_np[m].mean() + 1e-6), 0).astype(np.float32)

    # --- Segmentation des tissus de l'IRM (3 classes) : liquide, matiere grise, matiere blanche ---
    mesures = {}
    try:
        seg = ants.atropos(a=irm_mni, x=modele.masque_img, i="kmeans[3]", m="[0.1,1x1x1]", c="[5,0]")
        s = seg["segmentation"].numpy()
        ordre = sorted([1, 2, 3], key=lambda k: irm_np[(s == k) & m].mean())  # sombre -> clair
        lcr, mg = (s == ordre[0]) & m, (s == ordre[1]) & m
    except Exception:
        lcr = mg = None

    for nom, zone in modele.regions.items():
        n = zone.sum()
        if lcr is not None:
            mesures[f"IRM_{nom}_LCR"] = float(lcr[zone].sum() / n)
            mesures[f"IRM_{nom}_MG"] = float(mg[zone].sum() / n)
        mesures[f"PET_{nom}"] = float(pet_suvr[zone].mean())

    qc = {
        "IRM_info_mutuelle": float(mi_irm),   # plus negatif = mieux aligne (bon : environ -0,70)
        "IRM_essais": essais_irm,
        "PET_corr_matiere_grise": float(corr_pet),  # bon : > 0,2 ; PET decale : environ 0
        "PET_essais": essais_pet,
    }
    return _vers_cube(modele, irm_z), _vers_cube(modele, pet_suvr), mesures, qc
