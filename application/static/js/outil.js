/* Formulaire d'estimation : envoi au serveur et affichage du resultat. */
(function () {
  "use strict";

  var formulaire = document.getElementById("formulaire");
  if (!formulaire) { return; }

  var vide       = document.getElementById("resultat-vide");
  var contenu    = document.getElementById("resultat-contenu");
  var boiteErreur= document.getElementById("resultat-erreur");
  var pourcent   = document.getElementById("resultat-pct");
  var remplissage= document.getElementById("jauge-remplissage");
  var niveau     = document.getElementById("resultat-niveau");
  var phrase     = document.getElementById("resultat-phrase");
  var bouton     = formulaire.querySelector('button[type="submit"]');

  function afficherErreur(message) {
    vide.hidden = true;
    contenu.hidden = true;
    boiteErreur.hidden = false;
    boiteErreur.textContent = message;
  }

  var blocFacteurs = document.getElementById("facteurs");
  var listeFacteurs= document.getElementById("facteurs-liste");

  /* Construit un groupe ("augmente" / "diminue") avec une barre proportionnelle au poids. */
  function groupe(titre, classe, facteurs, poidsMax) {
    var fragment = document.createDocumentFragment();
    var t = document.createElement("p");
    t.className = "facteurs__groupe facteurs__groupe--" + classe;
    t.textContent = titre;
    fragment.appendChild(t);
    var ul = document.createElement("ul");
    facteurs.forEach(function (f) {
      var li = document.createElement("li");
      li.className = "facteur";
      var nom = document.createElement("span");
      nom.className = "facteur__nom";
      nom.textContent = f.libelle;
      var valeur = document.createElement("span");
      valeur.className = "facteur__valeur";
      valeur.textContent = f.valeur;
      var barre = document.createElement("span");
      barre.className = "facteur__barre";
      var plein = document.createElement("span");
      plein.style.width = Math.max(8, Math.round(100 * f.poids / poidsMax)) + "%";
      barre.appendChild(plein);
      li.appendChild(nom); li.appendChild(valeur); li.appendChild(barre);
      ul.appendChild(li);
    });
    fragment.appendChild(ul);
    return fragment;
  }

  function afficherFacteurs(e) {
    listeFacteurs.textContent = "";
    if (!e) { blocFacteurs.hidden = true; return; }
    if (e.hausse.length) {
      listeFacteurs.appendChild(groupe("Ce qui augmente le risque", "hausse", e.hausse, e.poids_max));
    }
    if (e.baisse.length) {
      listeFacteurs.appendChild(groupe("Ce qui le diminue", "baisse", e.baisse, e.poids_max));
    }
    if (!e.hausse.length && !e.baisse.length) {
      var p = document.createElement("p");
      p.className = "facteurs__aucun";
      p.textContent = "Aucun des éléments renseignés ne s'écarte nettement de la moyenne.";
      listeFacteurs.appendChild(p);
    }
    blocFacteurs.hidden = false;
  }

  function afficherResultat(d) {
    vide.hidden = true;
    boiteErreur.hidden = true;
    contenu.hidden = false;

    var valeur = d.pourcentage;
    pourcent.textContent = String(valeur).replace(".", ",");
    remplissage.style.width = Math.min(valeur, 100) + "%";

    niveau.textContent = d.titre;
    niveau.className = "etiquette-niveau " + d.classe;
    phrase.textContent = d.phrase;
    afficherFacteurs(d.explication);

    contenu.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  formulaire.addEventListener("submit", function (evenement) {
    evenement.preventDefault();

    var donnees = {};
    new FormData(formulaire).forEach(function (valeur, cle) {
      if (String(valeur).trim() !== "") { donnees[cle] = valeur; }
    });

    bouton.disabled = true;
    var libelleInitial = bouton.textContent;
    bouton.textContent = "Calcul en cours…";

    fetch("/api/prediction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(donnees)
    })
      .then(function (reponse) {
        return reponse.json().then(function (corps) {
          return { ok: reponse.ok, corps: corps };
        });
      })
      .then(function (r) {
        if (!r.ok) { afficherErreur(r.corps.erreur || "Le calcul n'a pas abouti."); }
        else { afficherResultat(r.corps); }
      })
      .catch(function () {
        afficherErreur("Le serveur n'a pas répondu. Vérifiez que l'application est bien lancée.");
      })
      .finally(function () {
        bouton.disabled = false;
        bouton.textContent = libelleInitial;
      });
  });

  formulaire.addEventListener("reset", function () {
    contenu.hidden = true;
    boiteErreur.hidden = true;
    blocFacteurs.hidden = true;
    vide.hidden = false;
  });
})();
