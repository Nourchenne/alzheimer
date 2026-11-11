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
    vide.hidden = false;
  });
})();
