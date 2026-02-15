# Plan d'implementation : Candidature guidee aux fonds verts

## Vision

Transformer la plateforme ESG Advisor en un assistant complet de candidature aux fonds verts :
- Le LLM guide l'utilisateur de bout en bout, de la recherche du fonds a la soumission
- Si la candidature directe est possible : redirection vers le site + extension Chrome prend le relais
- Si un intermediaire est necessaire : le LLM identifie les intermediaires, explique le processus, et aide a preparer le dossier
- Generation automatique de dossiers complets (Word/PDF) adaptes a chaque fonds et intermediaire
- Synchronisation temps reel entre la plateforme web et l'extension Chrome

## Architecture cible

```
Utilisateur
    |
    v
[Chat LLM] -----> skill: guide_candidature
    |                  |
    |                  |--> Analyse mode_acces du fonds
    |                  |--> Si direct: propose URL + declenche extension
    |                  |--> Si intermediaire: liste les intermediaires
    |                  |        |--> Propose formulaire en ligne si dispo
    |                  |        |--> Propose generation de dossier
    |                  |
    |                  |--> skill: generate_dossier_candidature
    |                  |        |--> Lettre de motivation adaptee
    |                  |        |--> Fiche projet
    |                  |        |--> Dossier technique complet
    |                  |        |--> Templates pre-remplis
    |                  |
    v                  v
[Plateforme Web] <--sync--> [Extension Chrome]
    |                            |
    |-- Suivi candidatures       |-- Detection site fonds
    |-- Historique dossiers      |-- Auto-remplissage formulaires
    |-- Notifications            |-- Guide etape par etape
    |-- Timeline processus       |-- Sauvegarde progression
```

## Phases d'implementation

| Phase | Nom | Duree estimee | Dependances |
|-------|-----|---------------|-------------|
| 1 | [Enrichissement donnees intermediaires](01_enrichissement_donnees_intermediaires.md) | 1 semaine | Aucune |
| 2 | [Skills LLM pour candidature guidee](02_skills_llm_candidature.md) | 1.5 semaines | Phase 1 |
| 3 | [Generation de dossiers avancee](03_generation_dossiers.md) | 1.5 semaines | Phase 1 |
| 4 | [Synchronisation plateforme-extension](04_sync_plateforme_extension.md) | 1 semaine | Phases 2-3 |
| 5 | [Configurations extension pour tous les fonds](05_configs_extension_fonds.md) | 1 semaine | Phase 1 |
| 6 | [Interface de suivi des candidatures](06_interface_suivi_candidature.md) | 1 semaine | Phases 4-5 |

**Duree totale estimee : 7 semaines** (avec parallelisation phases 2-3 et phases 5-6)

## Diagramme de dependances

```
Phase 1 (Donnees)
    |
    +------+-------+
    |      |       |
    v      v       v
Phase 2  Phase 3  Phase 5
(Skills) (Docs)   (Extension configs)
    |      |       |
    +------+       |
    |              |
    v              v
Phase 4          Phase 6
(Sync)           (UI suivi)
```

## Stack technique additionnelle

### Backend
- **python-docx** (deja present) : generation Word avancee
- **weasyprint** (deja present) : generation PDF
- **websockets** ou **sse-starlette** (deja planifie) : sync temps reel
- Pas de nouvelle dependance majeure

### Frontend
- Nouveaux composants Vue 3 pour le suivi de candidature
- Integration WebSocket/SSE pour notifications temps reel
- Timeline interactive (CSS/Tailwind, pas de lib externe)

### Extension Chrome
- 9 nouvelles configurations `FundSiteConfig` (1 seule existe actuellement : BOAD)
- Nouveau message type `PLATFORM_ACTION` pour recevoir des commandes de la plateforme
- `chrome.runtime.sendMessage` pour communication extension -> plateforme

## Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Sites de fonds changent leurs formulaires | Elevee | Versionner les FundSiteConfig, monitoring periodique |
| URLs des intermediaires deviennent invalides | Moyen | Verifier les URLs au seed, fallback vers recherche |
| Generation LLM de dossiers imprecise | Moyen | Templates structurees + revision humaine recommandee |
| Sync temps reel complexe a debugger | Moyen | Fallback polling 30s si WebSocket echoue |
| Formulaires SPA difficiles a detecter | Moyen | Detection hybride URL + DOM + titre page |

## Metriques de succes

1. **Taux de completion** : % de candidatures demarrees vs soumises
2. **Temps moyen** : temps entre premiere interaction et soumission
3. **Qualite dossiers** : % de dossiers generes sans modification manuelle
4. **Couverture** : nombre de fonds avec config extension fonctionnelle
5. **Sync fiabilite** : % de syncs reussies entre plateforme et extension
