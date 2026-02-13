# 03 - Système de Skills Dynamiques

## Concept Central

Les skills sont les **outils** que le LLM peut appeler pendant une conversation (via le mécanisme `tool_use` / `function calling`).
Ils sont stockés en BDD et chargés dynamiquement → l'admin peut les créer/modifier/supprimer sans toucher au code.

> **Note** : Les skills sont convertis au format OpenAI tools (`type: "function"`) qui est supporté par tous les modèles via OpenRouter.

## Types de Skills

### Type 1 : Skills Builtin (codés dans le projet)
```
handler_key = "builtin.analyze_document"
handler_code = NULL
```
- Fonction Python dans le code source du backend
- Fiable, testé, performant
- L'admin peut activer/désactiver mais pas modifier le code
- Utilisé pour les skills complexes (RAG, PDF, calculs)

### Type 2 : Skills Custom (créés par l'admin)
```
handler_key = "custom.verifier_conformite_bceao"
handler_code = "def execute(params, context): ..."
```
- Code Python écrit par l'admin dans l'interface
- Exécuté dans un environnement contrôlé (fonctions autorisées limitées)
- Idéal pour ajouter des logiques métier spécifiques
- Peut appeler les services internes (BDD, RAG)

---

## Architecture du Skill Registry

```python
# === backend/app/skills/registry.py ===

class SkillRegistry:
    """
    Registre central des skills.
    Charge les skills depuis la BDD et les convertit en outils (format OpenAI tools).
    """

    def __init__(self, db_session):
        self.db = db_session
        self.builtin_handlers: dict[str, Callable] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Enregistre tous les skills builtin disponibles."""
        from app.skills.handlers import (
            analyze_document,
            calculate_esg_score,
            list_referentiels,
            search_green_funds,
            calculate_carbon_footprint,
            generate_report_section,
            assemble_pdf,
            search_knowledge_base,
            get_company_profile,
            update_company_profile,
        )
        self.builtin_handlers = {
            "builtin.analyze_document": analyze_document,
            "builtin.calculate_esg_score": calculate_esg_score,
            "builtin.list_referentiels": list_referentiels,
            "builtin.search_green_funds": search_green_funds,
            "builtin.calculate_carbon": calculate_carbon_footprint,
            "builtin.generate_reduction_plan": generate_reduction_plan,
            "builtin.simulate_funding": simulate_funding,
            "builtin.calculate_credit_score": calculate_credit_score,
            "builtin.get_sector_benchmark": get_sector_benchmark,
            "builtin.manage_action_plan": manage_action_plan,
            "builtin.generate_report_section": generate_report_section,
            "builtin.assemble_pdf": assemble_pdf,
            "builtin.search_knowledge_base": search_knowledge_base,
            "builtin.get_company_profile": get_company_profile,
            "builtin.update_company_profile": update_company_profile,
        }

    async def get_active_tools(self) -> list[dict]:
        """
        Charge les skills actifs depuis la BDD.
        Retourne une liste de dicts intermédiaires {name, description, input_schema}.
        La conversion finale au format OpenAI tools se fait dans engine.py.
        """
        skills = await self.db.fetch_all(
            "SELECT * FROM skills WHERE is_active = true ORDER BY category, nom"
        )

        tools = []
        for skill in skills:
            tools.append({
                "name": skill["nom"],
                "description": skill["description"],
                "input_schema": skill["input_schema"],  # JSON Schema depuis la BDD
            })
        return tools

    async def execute_skill(self, skill_name: str, params: dict, context: dict) -> dict:
        """
        Exécute un skill par son nom.
        - Si builtin → appelle la fonction Python enregistrée
        - Si custom → exécute le handler_code depuis la BDD
        """
        skill = await self.db.fetch_one(
            "SELECT * FROM skills WHERE nom = $1 AND is_active = true",
            skill_name
        )

        if not skill:
            return {"error": f"Skill '{skill_name}' introuvable ou inactif"}

        handler_key = skill["handler_key"]

        # Skill Builtin
        if handler_key.startswith("builtin."):
            handler = self.builtin_handlers.get(handler_key)
            if not handler:
                return {"error": f"Handler builtin '{handler_key}' non enregistré"}
            return await handler(params, context)

        # Skill Custom (code de l'admin)
        if handler_key.startswith("custom."):
            return await self._execute_custom(skill["handler_code"], params, context)

        return {"error": f"Type de handler inconnu: {handler_key}"}

    async def _execute_custom(self, code: str, params: dict, context: dict) -> dict:
        """
        Exécute le code Python d'un skill custom dans un environnement restreint.
        """
        # Fonctions autorisées pour les skills custom
        allowed_globals = {
            "params": params,
            "context": context,
            # Services internes accessibles
            "db_query": context["db"].fetch_all,
            "rag_search": context["rag"].search,
            "json": __import__("json"),
            "datetime": __import__("datetime"),
            "math": __import__("math"),
        }

        local_vars = {}
        try:
            exec(code, allowed_globals, local_vars)
            # Le code doit définir une fonction execute()
            if "execute" in local_vars:
                result = await local_vars["execute"](params, context)
                return result
            else:
                return {"error": "Le skill doit définir une fonction execute(params, context)"}
        except Exception as e:
            return {"error": f"Erreur d'exécution du skill: {str(e)}"}
```

---

## Skills Builtin : Détail des Handlers

### Skill : analyze_document
```python
# === backend/app/skills/handlers/analyze_document.py ===

async def analyze_document(params: dict, context: dict) -> dict:
    """
    Analyse un document uploadé.
    1. Récupère le document depuis le stockage
    2. Extrait le texte (OCR si image/scan)
    3. Découpe en chunks + embedding
    4. Recherche les passages pertinents pour le type d'analyse
    5. Retourne les données extraites
    """
    document_id = params["document_id"]
    analysis_type = params.get("analysis_type", "esg_compliance")

    # 1. Récupérer le document
    doc = await context["db"].fetch_one(
        "SELECT * FROM documents WHERE id = $1", document_id
    )

    # 2. Si pas encore chunké → le faire
    chunk_count = await context["db"].fetch_val(
        "SELECT COUNT(*) FROM doc_chunks WHERE document_id = $1", document_id
    )

    if chunk_count == 0:
        text = doc["texte_extrait"]
        if not text:
            text = await extract_text(doc["chemin_stockage"], doc["type_mime"])
            await context["db"].execute(
                "UPDATE documents SET texte_extrait = $1 WHERE id = $2",
                text, document_id
            )
        chunks = chunk_text(text, chunk_size=800, overlap=200)
        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk.text)
            await context["db"].execute(
                """INSERT INTO doc_chunks (document_id, contenu, embedding, page_number, chunk_index)
                   VALUES ($1, $2, $3, $4, $5)""",
                document_id, chunk.text, embedding, chunk.page, i
            )

    # 3. Recherche sémantique selon le type d'analyse
    queries = {
        "esg_compliance": [
            "pratiques environnementales gestion déchets énergie",
            "conditions de travail employés formation",
            "gouvernance transparence éthique conformité",
        ],
        "financial": [
            "chiffre d'affaires revenus bénéfices",
            "dépenses investissements budget",
        ],
        "carbon": [
            "consommation énergie électricité carburant",
            "transport logistique véhicules",
            "déchets émissions pollution",
        ],
    }

    results = []
    for query in queries.get(analysis_type, queries["esg_compliance"]):
        query_embedding = await get_embedding(query)
        chunks = await context["db"].fetch_all(
            """SELECT contenu, page_number,
                      1 - (embedding <=> $1) AS similarity
               FROM doc_chunks
               WHERE document_id = $2
               ORDER BY embedding <=> $1
               LIMIT 5""",
            query_embedding, document_id
        )
        results.extend([dict(c) for c in chunks])

    # Déduplique et trie par pertinence
    seen = set()
    unique_results = []
    for r in sorted(results, key=lambda x: x["similarity"], reverse=True):
        if r["contenu"] not in seen:
            seen.add(r["contenu"])
            unique_results.append(r)

    return {
        "document": doc["nom_fichier"],
        "analysis_type": analysis_type,
        "extracted_passages": unique_results[:15],
        "total_pages": doc.get("metadata_json", {}).get("pages", "inconnu"),
    }
```

### Skill : list_referentiels
```python
# === backend/app/skills/handlers/list_referentiels.py ===

async def list_referentiels(params: dict, context: dict) -> dict:
    """
    Liste les référentiels ESG disponibles.
    Le LLM utilise ce skill pour savoir quels référentiels existent
    et recommander le bon selon le fonds visé.
    """
    region = params.get("region")         # Filtrer par région
    fonds_id = params.get("fonds_id")     # Trouver le référentiel d'un fonds

    if fonds_id:
        # Référentiel lié à un fonds spécifique
        ref = await context["db"].fetch_one(
            """SELECT r.* FROM referentiels_esg r
               JOIN fonds_verts f ON f.referentiel_id = r.id
               WHERE f.id = $1""",
            fonds_id
        )
        if ref:
            return {"referentiels": [_format_ref(ref)]}
        return {"referentiels": [], "note": "Ce fonds n'a pas de référentiel associé"}

    query = "SELECT * FROM referentiels_esg WHERE is_active = true"
    args = []
    if region:
        query += " AND region = $1"
        args.append(region)
    query += " ORDER BY nom"

    refs = await context["db"].fetch_all(query, *args)
    return {
        "nombre": len(refs),
        "referentiels": [_format_ref(r) for r in refs],
    }

def _format_ref(ref):
    grille = ref["grille_json"]
    return {
        "id": str(ref["id"]),
        "code": ref["code"],
        "nom": ref["nom"],
        "institution": ref["institution"],
        "region": ref["region"],
        "methode": grille.get("methode_aggregation"),
        "piliers": {
            pilier: {
                "poids": config["poids_global"],
                "nb_criteres": len(config["criteres"]),
            }
            for pilier, config in grille.get("piliers", {}).items()
        }
    }
```

### Skill : calculate_esg_score (v2 — multi-référentiel)
```python
# === backend/app/skills/handlers/calculate_esg_score.py ===

async def calculate_esg_score(params: dict, context: dict) -> dict:
    """
    Calcule le score ESG selon UN ou PLUSIEURS référentiels.
    La grille n'est plus codée en dur : elle vient de la BDD.

    params:
      - entreprise_id: str
      - data: dict (réponses aux critères, clé = critere_id)
      - referentiel_codes: list[str] | None
        Si None → score sur tous les référentiels actifs
        Si ["bceao_fd_2024"] → score sur ce référentiel uniquement
    """
    entreprise_id = params["entreprise_id"]
    data = params["data"]
    ref_codes = params.get("referentiel_codes")

    # 1. Charger les référentiels demandés depuis la BDD
    if ref_codes:
        referentiels = await context["db"].fetch_all(
            "SELECT * FROM referentiels_esg WHERE code = ANY($1) AND is_active = true",
            ref_codes
        )
    else:
        referentiels = await context["db"].fetch_all(
            "SELECT * FROM referentiels_esg WHERE is_active = true"
        )

    if not referentiels:
        return {"error": "Aucun référentiel trouvé", "scores": []}

    # 2. Calculer le score pour chaque référentiel
    resultats = []

    for ref in referentiels:
        grille = ref["grille_json"]
        methode = grille.get("methode_aggregation", "weighted_average")
        scores_piliers = {}

        for pilier_key, pilier_config in grille["piliers"].items():
            critere_scores = []

            for critere in pilier_config["criteres"]:
                critere_id = critere["id"]
                valeur = data.get(critere_id)

                if valeur is None:
                    score_critere = 0
                elif critere["type"] == "quantitatif":
                    score_critere = _score_quantitatif(valeur, critere.get("seuils", {}))
                elif critere["type"] == "qualitatif":
                    score_critere = _score_qualitatif(valeur, critere.get("options", []))
                else:
                    score_critere = min(max(valeur, 0), 100)

                critere_scores.append({
                    "id": critere_id,
                    "label": critere["label"],
                    "poids": critere["poids"],
                    "score": score_critere,
                    "statut": _statut(score_critere),
                    "valeur_brute": valeur,
                })

            pilier_score = sum(c["poids"] * c["score"] for c in critere_scores)
            scores_piliers[pilier_key] = {
                "score": round(pilier_score, 1),
                "poids_global": pilier_config["poids_global"],
                "criteres": critere_scores,
            }

        # Score global selon la méthode du référentiel
        if methode == "weighted_average":
            score_global = sum(
                p["score"] * p["poids_global"]
                for p in scores_piliers.values()
            )
        elif methode == "threshold":
            # Vérifier que tous les seuils minimum sont atteints
            all_above = True
            for pilier_config in grille["piliers"].values():
                for critere in pilier_config["criteres"]:
                    seuil_min = critere.get("seuil_minimum")
                    if seuil_min is not None:
                        score_c = next(
                            (c["score"] for p in scores_piliers.values()
                             for c in p["criteres"] if c["id"] == critere["id"]),
                            0
                        )
                        if score_c < seuil_min:
                            all_above = False
                            break

            score_global = sum(
                p["score"] * p["poids_global"]
                for p in scores_piliers.values()
            ) if all_above else 0
        else:
            score_global = sum(
                p["score"] * p["poids_global"]
                for p in scores_piliers.values()
            )

        score_global = round(score_global, 1)

        # Sauvegarder en BDD
        details = {
            "referentiel": ref["nom"],
            "methode": methode,
            **{k: v for k, v in scores_piliers.items()},
        }
        await context["db"].execute(
            """INSERT INTO esg_scores
               (entreprise_id, referentiel_id, score_e, score_s, score_g,
                score_global, details_json, source)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
            entreprise_id, ref["id"],
            scores_piliers.get("environnement", {}).get("score", 0),
            scores_piliers.get("social", {}).get("score", 0),
            scores_piliers.get("gouvernance", {}).get("score", 0),
            score_global, json.dumps(details), "conversation",
        )

        resultats.append({
            "referentiel": ref["nom"],
            "referentiel_code": ref["code"],
            "institution": ref["institution"],
            "score_global": score_global,
            "niveau": _niveau(score_global),
            "scores_piliers": {k: v["score"] for k, v in scores_piliers.items()},
            "details": scores_piliers,
        })

    # 3. Identifier les données manquantes
    all_critere_ids = set()
    for ref in referentiels:
        for p in ref["grille_json"]["piliers"].values():
            for c in p["criteres"]:
                all_critere_ids.add(c["id"])

    donnees_manquantes = [cid for cid in all_critere_ids if cid not in data]

    return {
        "nombre_referentiels": len(resultats),
        "scores": resultats,
        "donnees_manquantes": donnees_manquantes,
    }


def _score_quantitatif(valeur, seuils: dict) -> int:
    """Convertit une valeur numérique en score 0-100 selon les seuils."""
    for niveau in ["excellent", "bon", "moyen", "faible"]:
        seuil = seuils.get(niveau)
        if not seuil:
            continue
        if "max" in seuil and valeur <= seuil["max"]:
            return seuil["score"]
        if "min" in seuil and valeur >= seuil["min"]:
            return seuil["score"]
    return 0

def _score_qualitatif(valeur, options: list) -> int:
    """Trouve le score correspondant à une réponse qualitative."""
    for option in options:
        if option["label"].lower() == str(valeur).lower():
            return option["score"]
    return 0

def _statut(score):
    if score >= 70: return "conforme"
    if score >= 40: return "partiel"
    return "non_conforme"

def _niveau(score):
    if score >= 80: return "Excellent"
    if score >= 60: return "Bon"
    if score >= 40: return "À améliorer"
    return "Insuffisant"
```

### Skill : search_green_funds
```python
# === backend/app/skills/handlers/search_green_funds.py ===

async def search_green_funds(params: dict, context: dict) -> dict:
    """
    Recherche les fonds verts compatibles.
    Étape 1 : Filtrage SQL (gratuit, rapide)
    Étape 2 : RAG sur les fonds filtrés (précision fine)
    """
    secteur = params.get("secteur")
    pays = params.get("pays", "CIV")
    montant = params.get("montant_recherche")
    score_esg = params.get("score_esg")

    # Étape 1 : Filtrage SQL
    fonds = await context["db"].fetch_all(
        """SELECT * FROM fonds_verts
           WHERE is_active = true
           AND (secteurs_json @> $1::jsonb OR secteurs_json IS NULL)
           AND (pays_eligibles @> $2::jsonb OR pays_eligibles IS NULL)
           AND (date_limite IS NULL OR date_limite > NOW())
           ORDER BY montant_max DESC""",
        json.dumps([secteur]), json.dumps([pays])
    )

    # Étape 2 : Pour chaque fonds, recherche RAG des critères détaillés
    resultats = []
    for fonds in fonds[:10]:  # Max 10 fonds
        # Recherche sémantique dans les chunks du fonds
        query = f"critères éligibilité {secteur} PME {pays}"
        query_embedding = await get_embedding(query)

        chunks = await context["db"].fetch_all(
            """SELECT contenu FROM fonds_chunks
               WHERE fonds_id = $1
               ORDER BY embedding <=> $2
               LIMIT 3""",
            fonds["id"], query_embedding
        )

        # Score de compatibilité simple
        compatibilite = 50  # base
        if score_esg and score_esg >= 60: compatibilite += 20
        if montant and fonds["montant_min"] and montant >= fonds["montant_min"]: compatibilite += 15
        if chunks: compatibilite += 15

        resultats.append({
            "fonds_id": str(fonds["id"]),
            "nom": fonds["nom"],
            "institution": fonds["institution"],
            "type": fonds["type"],
            "referentiel_id": str(fonds["referentiel_id"]) if fonds.get("referentiel_id") else None,
            "montant_range": f"{fonds['montant_min']}-{fonds['montant_max']} {fonds['devise']}",
            "compatibilite": min(compatibilite, 100),
            "criteres_extraits": [c["contenu"] for c in chunks],
            "date_limite": str(fonds["date_limite"]) if fonds["date_limite"] else None,
        })

    resultats.sort(key=lambda x: x["compatibilite"], reverse=True)

    return {
        "nombre_fonds": len(resultats),
        "fonds": resultats,
    }
```

---

## Skills Builtin Additionnels (description brève)

Les skills suivants complètent les modules 4, 5 et 6. Leur implémentation suit la même structure que les skills détaillés ci-dessus (fonction async dans `handlers/`).

### Skill : calculate_carbon_footprint
- **Catégorie** : carbon
- **Rôle** : Calcule l'empreinte carbone annuelle d'une entreprise à partir des données collectées par conversation ou documents.
- **Entrées** : `entreprise_id`, `data` (dict avec clés : `electricite_kwh`, `generateur_litres`, `vehicules_km`, `type_carburant`, `dechets_tonnes`, `achats_montant`)
- **Logique** : Charge les facteurs d'émission depuis `data/facteurs_emission.json` (contextualisés par pays — mix énergétique CI vs Sénégal vs Cameroun). Multiplie chaque donnée d'activité par son facteur. Stocke le résultat dans `carbon_footprints`.
- **Sortie** : total tCO2e, répartition par source (énergie, transport, déchets, achats), comparaison avec la moyenne sectorielle via `sector_benchmarks`.

### Skill : generate_reduction_plan
- **Catégorie** : carbon
- **Rôle** : Génère un plan de réduction carbone priorisé basé sur l'empreinte calculée.
- **Entrées** : `entreprise_id`
- **Logique** : Récupère la dernière `carbon_footprint`. Identifie les sources les plus émettrices. Interroge la knowledge base (RAG) pour des actions de réduction adaptées au secteur et au pays. Classe les actions en `quick_win` (< 3 mois, faible coût), `moyen_terme` (3-12 mois), `long_terme` (> 12 mois). Estime les économies financières et la réduction en tCO2e pour chaque action.
- **Sortie** : Liste d'actions priorisées avec impact estimé, coût, et délai. Crée automatiquement les `action_items` associés.

### Skill : simulate_funding
- **Catégorie** : finance
- **Rôle** : Simule l'éligibilité et le montant potentiel pour un fonds vert donné.
- **Entrées** : `entreprise_id`, `fonds_id`, `montant_demande` (optionnel)
- **Logique** : Charge le fonds et son référentiel associé. Récupère le score ESG de l'entreprise selon ce référentiel. Vérifie les critères d'éligibilité (secteur, pays, seuils). Calcule un montant estimé (basé sur les fourchettes du fonds et le profil entreprise). Estime une timeline du processus de candidature. Calcule un ROI vert simplifié (économies énergie + crédits carbone potentiels vs investissement).
- **Sortie** : `eligible` (bool), `montant_estime`, `criteres_manquants`, `timeline_estimee`, `roi_vert`, `recommandations`.

### Skill : calculate_credit_score
- **Catégorie** : finance
- **Rôle** : Calcule le score de crédit vert alternatif (Module 5 — Innovation 3). Combine données financières et engagement ESG pour produire un score inclusif.
- **Entrées** : `entreprise_id`, `donnees_financieres` (dict optionnel : régularité, volume, ancienneté), `donnees_declaratives` (dict optionnel : pratiques vertes, programmes)
- **Logique** :
  1. **Score solvabilité (0-100)** : basé sur régularité des transactions, volume d'activité, ancienneté, existence de documents financiers (via `documents` uploadés).
  2. **Score impact vert (0-100)** : basé sur le dernier score ESG, la tendance (amélioration vs stagnation), les certifications, la participation à des programmes verts, l'existence d'un plan d'action actif.
  3. **Score combiné** : moyenne pondérée configurable (ex: 50% solvabilité + 50% impact vert). Plus l'entreprise est verte, meilleur est son accès au crédit.
  4. **Transparence** : chaque facteur est listé avec son impact positif ou négatif dans `facteurs_json`.
- **Sortie** : `score_solvabilite`, `score_impact_vert`, `score_combine`, `facteurs` (explication), `recommandations_amelioration`. Stocke dans `credit_scores`.
- **Note MVP** : Pour le hackathon, les données financières sont déclaratives (questionnaire conversationnel). L'intégration Mobile Money (Orange Money, Wave) est prévue en V2 via API partenaire.

### Skill : get_sector_benchmark
- **Catégorie** : utils
- **Rôle** : Récupère les moyennes sectorielles pour comparer les performances de l'entreprise.
- **Entrées** : `secteur`, `pays` (optionnel), `referentiel_code` (optionnel)
- **Logique** : Requête sur `sector_benchmarks`. Si le benchmark n'existe pas encore, le calcule à partir des `esg_scores` et `carbon_footprints` des entreprises du même secteur en BDD.
- **Sortie** : Moyennes E/S/G, score global moyen, empreinte carbone moyenne, nombre d'entreprises dans l'échantillon.

### Skill : manage_action_plan
- **Catégorie** : utils
- **Rôle** : Crée ou met à jour un plan d'action structuré pour l'entreprise.
- **Entrées** : `entreprise_id`, `action` (`create` | `add_item` | `update_status`), paramètres selon l'action
- **Logique** :
  - `create` : Génère un plan basé sur les lacunes identifiées dans le dernier score ESG. Priorise les actions par rapport qualité/coût. Définit des échéances réalistes.
  - `add_item` : Ajoute une action au plan existant.
  - `update_status` : Met à jour le statut d'une action (a_faire → en_cours → fait). Déclenche une notification de progression si un palier est atteint.
- **Sortie** : Le plan avec ses items, barre de progression, prochaines échéances.

---

## Skill Custom : Exemple Admin

Un admin veut ajouter un skill pour vérifier la conformité BCEAO :

```
Nom:          verifier_conformite_bceao
Description:  Vérifie si l'entreprise respecte les directives BCEAO sur la finance durable
Category:     esg
handler_key:  custom.verifier_conformite_bceao
input_schema: {
    "type": "object",
    "properties": {
        "entreprise_id": {"type": "string"},
        "type_verification": {
            "type": "string",
            "enum": ["reporting", "taxonomie", "risques_climatiques"]
        }
    },
    "required": ["entreprise_id"]
}
```

```python
# handler_code (écrit par l'admin dans l'interface)

async def execute(params, context):
    entreprise_id = params["entreprise_id"]
    type_verif = params.get("type_verification", "reporting")

    # Accès à la BDD via context
    entreprise = await context["db"].fetch_one(
        "SELECT * FROM entreprises WHERE id = $1", entreprise_id
    )

    # Accès au RAG via context
    resultats_rag = await context["rag"].search(
        query=f"directive BCEAO {type_verif} finance durable",
        category="regulation",
        top_k=5
    )

    # Derniers scores ESG
    score = await context["db"].fetch_one(
        """SELECT * FROM esg_scores
           WHERE entreprise_id = $1
           ORDER BY created_at DESC LIMIT 1""",
        entreprise_id
    )

    conformite = {
        "entreprise": entreprise["nom"],
        "type_verification": type_verif,
        "references_bceao": [r["contenu"] for r in resultats_rag],
        "score_esg_actuel": score["score_global"] if score else None,
        "conforme": score and score["score_global"] >= 50,
    }

    return conformite
```

---

## Sécurité des Skills Custom

### Ce que le code custom PEUT faire
- Lire la BDD (`context["db"].fetch_one`, `fetch_all`)
- Chercher dans le RAG (`context["rag"].search`)
- Utiliser `json`, `datetime`, `math`, `re`
- Retourner un dictionnaire de résultats

### Ce que le code custom NE PEUT PAS faire
- Importer des modules système (`os`, `subprocess`, `sys`)
- Accéder au système de fichiers
- Faire des requêtes HTTP externes
- Modifier/supprimer des données (uniquement lecture)
- Exécuter du code arbitraire imbriqué (`exec`, `eval`)

### Validation avant sauvegarde
```python
FORBIDDEN_PATTERNS = [
    "import os", "import sys", "import subprocess",
    "__import__", "exec(", "eval(",
    "open(", "file(",
    "requests.", "urllib.",
    "DELETE", "DROP", "UPDATE", "INSERT",  # Pas d'écriture directe
]

def validate_skill_code(code: str) -> tuple[bool, str]:
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in code:
            return False, f"Pattern interdit détecté: '{pattern}'"
    # Vérifie que execute() est définie
    if "async def execute(params, context)" not in code:
        return False, "Le code doit définir : async def execute(params, context)"
    return True, "OK"
```
