"""Configuration centrale des chemins du projet Alzheimer.

A placer dans <racine du projet>\\configs\\config_projet.py
Utilisation dans un notebook (lance depuis le dossier notebooks/) :

    import sys
    sys.path.append(r"..\\configs")
    from config_projet import C

Avantage : plus aucun chemin horodate n'est recopie a la main dans les
notebooks. Si un dossier change, on ne corrige qu'ici.
"""

from pathlib import Path
import pandas as pd


class Config:
    def __init__(self):
        # Racine = dossier parent de configs/ : marche sur n'importe quel PC
        # (E:\Projet_Alzheimer, C:\Users\...\alzheimer, ...) sans rien modifier.
        self.ROOT = Path(__file__).resolve().parents[1]
        self.DATA = self.ROOT / "data"
        self.TABLES = self.DATA / "02_Tables_originales"
        self.MANIFESTES = self.DATA / "05_Manifestes"

        # Dossier de la cohorte 359 : on prend automatiquement le plus recent.
        self.COHORTE = self._dernier(self.MANIFESTES, "cohorte_359_*")

        # Dossier d'audit des visites IRM le plus recent (il contient les
        # manifestes du groupe de 112 produits par le notebook 06).
        self.AUDIT_VISITES = self._dernier(self.COHORTE, "audit_visites_IRM_*")

        # Fichiers cles deja produits par tes notebooks precedents.
        self.PARTICIPANTS_359 = self.COHORTE / "participants_candidats.csv"
        self.VISITES_359 = self.COHORTE / "visites_candidates.csv"
        self.MANIFESTE_112 = (
            self.AUDIT_VISITES / "manifeste_MMSE_1an_112_participants.csv"
        )
        self.BASE_112 = (
            self.AUDIT_VISITES / "base_MMSE_1an_112_avec_chemins.csv"
        )

    def _dernier(self, parent, motif):
        """Dernier dossier (par ordre de nom) correspondant au motif."""
        candidats = sorted(p for p in parent.glob(motif) if p.is_dir())
        if not candidats:
            raise FileNotFoundError(f"Aucun dossier {motif} dans {parent}")
        return candidats[-1]

    def table(self, prefixe):
        """Chemin unique d'une table originale a partir de son prefixe."""
        trouve = sorted(self.TABLES.rglob(prefixe + "*.csv"))
        if len(trouve) != 1:
            raise ValueError(
                f"{len(trouve)} fichier(s) pour {prefixe}, un seul attendu : "
                f"{[p.name for p in trouve]}"
            )
        return trouve[0]

    def sortie(self, nom):
        """Cree un nouveau dossier de sortie horodate (jamais ecrase)."""
        horodatage = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S_%f")
        dossier = self.COHORTE / f"{nom}_{horodatage}"
        dossier.mkdir(parents=True, exist_ok=False)
        return dossier


C = Config()
