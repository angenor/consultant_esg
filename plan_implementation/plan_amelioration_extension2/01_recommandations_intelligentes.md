# Phase 1 : Recommandations intelligentes

## Dependances

**Prerequis :** Aucune
**Bloque :** Phase 2 (le scoring doit etre fiable avant d'y brancher le flux candidature)

## Progression

- [x] 1.1 Affiner l'algorithme de scoring avec ponderation configurable
- [x] 1.2 Ajouter le cache Redis/memoire pour eviter le recalcul a chaque appel
- [x] 1.3 Ajouter les filtres utilisateur (type de financement, montant, secteur)
- [x] 1.4 Creer un endpoint `/api/candidatures/fonds-eligibles` dedie (distinct de l'extension)
- [x] 1.5 Ajouter le tri cote extension (par compatibilite, par montant, par date limite)
- [x] 1.6 Afficher un message explicatif du score de compatibilite
- [x] 1.7 Tests unitaires de l'algorithme de scoring

## Objectif

Transformer les recommandations de fonds d'un simple listing en un systeme de matching intelligent qui prend en compte le profil complet de l'entreprise.

## Etat actuel (correctif rapide applique)

### Ce qui existe
- Endpoint `/api/extension/fund-recommendations` avec scoring 0-100
- Criteres : pays (+30), secteur (+25), score ESG (+30), montant (+15)
- Mapping pays nom → code ISO (Cote d'Ivoire → CIV, etc.)
- Tri decroissant par score de compatibilite
- Champs enrichis : `mode_acces`, `criteres_json`, `acces_details`, `compatibility_score`

### Ce qui manque
- **Ponderation configurable** : les poids (30/25/30/15) sont codes en dur
- **Cache** : chaque appel recalcule tout (N+1 queries pour ESG score)
- **Filtres utilisateur** : pas de filtre par type (pret/subvention/garantie) ni montant
- **Explicabilite** : l'utilisateur voit "70% compatible" mais ne sait pas pourquoi
- **Tests** : aucun test unitaire sur la logique de scoring

## Implementation detaillee

### 1.1 Affiner l'algorithme de scoring

**Fichier :** `backend/app/api/extension.py` → extraire dans `backend/app/services/fund_matching.py`

```python
# Ponderation configurable
SCORING_WEIGHTS = {
    "pays_eligible": 30,
    "secteur_match": 25,
    "score_esg_ok": 30,
    "montant_accessible": 15,
}

# Criteres supplementaires a ajouter :
# - Bonus si date_limite proche (urgence) : +5
# - Bonus si mode_acces == "direct" (plus simple) : +5
# - Malus si score_esg_minimum > score_entreprise + 20 : -10
# - Bonus si deja une candidature en cours sur un fonds similaire : +5
# - Prise en compte du sous-secteur pour un matching plus fin
```

**Principe :** Extraire la logique de scoring dans un service reutilisable, avec des poids configurables via `.env` ou une table de config.

### 1.2 Cache des recommandations

**Strategie :** Cache en memoire avec TTL 5 minutes, invalide quand :
- Le profil entreprise change
- Un nouveau score ESG est calcule
- Un fonds est ajoute/modifie

```python
# backend/app/services/fund_matching.py
from functools import lru_cache
from datetime import datetime

# Cache par (entreprise_id, timestamp_arrondi_5min)
# Ou utiliser redis si disponible
```

### 1.3 Filtres utilisateur

**Endpoint modifie :** `GET /api/extension/fund-recommendations?type=pret&montant_max=500000000&secteur=energie`

```python
@router.get("/fund-recommendations")
async def get_fund_recommendations(
    type: str | None = Query(None),           # pret, subvention, garantie
    montant_max: float | None = Query(None),  # montant max en devise originale
    secteur: str | None = Query(None),        # filtre par secteur
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
```

### 1.4 Endpoint plateforme web dedie

**Fichier :** `backend/app/api/candidatures.py`

Ajouter `GET /api/candidatures/fonds-eligibles` qui reutilise le service de matching mais avec une reponse adaptee au frontend web (inclut les intermediaires disponibles).

### 1.5 Tri cote extension

**Fichier :** `chrome-extension/src/popup/components/DashboardPanel.vue`

Ajouter un selecteur de tri :
```
[Compatibilite v] [Montant v] [Date limite v]
```

### 1.6 Message explicatif

**Fichier :** `chrome-extension/src/popup/components/FundRecommendation.vue`

Au survol du score de compatibilite, afficher un tooltip :
```
70% compatible :
✓ Pays eligible (+30)
✓ Secteur correspondant (+25)
✓ Score ESG suffisant (+30)
✗ Montant non verifie
```

Cela necessite que le backend renvoie un champ `compatibility_details` :
```json
{
  "compatibility_score": 85,
  "compatibility_details": {
    "pays_eligible": true,
    "secteur_match": true,
    "score_esg_ok": true,
    "montant_accessible": false
  }
}
```

### 1.7 Tests unitaires

**Fichier :** `backend/tests/test_fund_matching.py`

```python
# Cas a tester :
# - Entreprise CIV + secteur agriculture → BOAD, FIDA, FAGACE en premier
# - Entreprise sans score ESG → recommandations avec score_esg_minimum faible
# - Entreprise hors zone UEMOA → fonds GCF, BAD, BEI en priorite
# - Filtre par type=subvention → seulement BAD, GCF, FIDA, SREP
# - Score compatibilite max = 100 (pas de depassement)
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `backend/app/services/fund_matching.py` | Service de scoring reutilisable |
| `backend/tests/test_fund_matching.py` | Tests unitaires scoring |

## Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `backend/app/api/extension.py` | Deleguer au service, ajouter filtres |
| `backend/app/api/candidatures.py` | Ajouter endpoint fonds-eligibles |
| `chrome-extension/src/popup/components/DashboardPanel.vue` | Selecteur de tri |
| `chrome-extension/src/popup/components/FundRecommendation.vue` | Tooltip explicatif |

## Criteres de validation

- [ ] Le scoring donne des resultats coherents (fonds UEMOA en premier pour entreprise CIV)
- [ ] Les filtres fonctionnent (type, montant, secteur)
- [ ] Le cache evite les recalculs inutiles
- [ ] L'explicabilite du score est visible dans l'extension
- [ ] Les tests unitaires passent
