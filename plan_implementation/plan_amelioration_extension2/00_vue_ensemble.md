# Plan d'amelioration : Extension Chrome - Recommandations & Candidatures

## Contexte

Lors de l'implementation de la Phase 6 (Interface suivi candidatures), une analyse d'alignement entre les donnees de fonds et l'extension Chrome a revele 4 problemes majeurs. Certains ont recu un correctif rapide ; ce plan definit les ameliorations completes pour un fonctionnement production-ready.

## Problemes identifies

| # | Probleme | Impact | Correctif rapide applique | Reste a faire |
|---|----------|--------|---------------------------|---------------|
| 1 | Recommandations non-intelligentes | Eleve | Scoring compatibilite 0-100 (pays, secteur, ESG, montant) | Tests, ponderation, cache, filtres utilisateur |
| 2 | Pas de lien recommandation → candidature | Eleve | Bouton "Postuler" cree une candidature + ouvre le site | Flux guidé selon mode_acces, deduplication, feedback UX |
| 3 | `mode_acces` absent de la reponse API | Moyen | Champ ajoute dans la reponse | Affichage conditionnel dans le popup, guide adapte |
| 4 | `criteres_json` / `acces_details` non transmis | Moyen | Champs ajoutes dans la reponse | Affichage etapes d'acces, checklist documents, guide interactif |

## Phases d'implementation

| Phase | Nom | Duree estimee | Dependances |Statut |
|-------|-----|---------------|-------------|-------|
| 1 | [Recommandations intelligentes](01_recommandations_intelligentes.md) | 3 jours | Aucune | [ ] Non demarre |
| 2 | [Flux candidature depuis recommandation](02_flux_candidature_recommandation.md) | 3 jours | Phase 1 | [ ] Non demarre |
| 3 | [Guide adaptatif par mode d'acces](03_guide_adaptatif_mode_acces.md) | 4 jours | Phases 1, 2 | [ ] Non demarre |
| 4 | [Checklist documents & etapes interactives](04_checklist_documents_etapes.md) | 3 jours | Phase 3 | [ ] Non demarre |

**Duree totale estimee : 2 semaines** (avec parallelisation phases 1-2)

## Diagramme de dependances

```
Phase 1 (Recommandations)
    |
    +------+
    |      |
    v      v
Phase 2  Phase 3
(Flux)   (Guide adaptatif)
    |      |
    +------+
    |
    v
Phase 4
(Checklist & etapes)
```

## Progression globale

- [ ] **Phase 1** : Recommandations intelligentes (0/7 taches)
- [ ] **Phase 2** : Flux candidature depuis recommandation (0/6 taches)
- [ ] **Phase 3** : Guide adaptatif par mode d'acces (0/8 taches)
- [ ] **Phase 4** : Checklist documents & etapes interactives (0/6 taches)
