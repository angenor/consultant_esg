# Semaine 3 — Modules Métier (ESG + Carbone + Financement)

> **Objectif** : Implémenter les fonctionnalités métier principales — RAG documentaire, scoring ESG multi-référentiel, empreinte carbone, recherche de fonds verts, benchmarking sectoriel.

> **Prérequis** : Semaine 2 terminée (agent conversationnel fonctionnel avec skills de base)

---

## Étape 11 — RAG : chunker, embeddings, search (HNSW)

**Fichiers concernés** : [08_arborescence_projet.md](../08_arborescence_projet.md) · [03_systeme_skills.md](../03_systeme_skills.md#skill--analyze_document) · [02_modeles_donnees.md](../02_modeles_donnees.md#documents--doc_chunks-rag)

### À faire

- [x] 11.1 Créer `backend/app/rag/__init__.py`

- [x] 11.2 Créer `backend/app/rag/text_extractor.py`
  - `extract_text_from_file(file_path, mime_type)` → str
  - Supporte : PDF (`PyPDF2` ou `pdfplumber`), Word (`python-docx`), Excel (`openpyxl`), images (`pytesseract` pour OCR)
  - Ajouter les dépendances au `requirements.txt`

- [x] 11.3 Créer `backend/app/rag/chunker.py`
  - `chunk_text(text, chunk_size=800, overlap=200)` → list de chunks
  - Chaque chunk a : `text`, `page` (si applicable), `index`
  - Découpage intelligent : respecter les paragraphes et phrases

- [x] 11.4 Créer `backend/app/rag/embeddings.py`
  - `get_embedding(text)` → vector (list[float])
  - Utiliser Voyage AI (`voyage-3-large`, dim 1024) ou un modèle d'embeddings via OpenRouter
  - Configurable via `.env` : `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`

- [x] 11.5 Créer `backend/app/rag/search.py`
  - `semantic_search(query, table, filters, top_k)` → list de résultats
  - Utilise pgvector : `ORDER BY embedding <=> query_embedding`
  - Supporte les tables `doc_chunks` et `fonds_chunks`
  - Index HNSW déjà créé dans la migration (Semaine 1)

- [x] 11.6 Ajouter les dépendances RAG au `requirements.txt`
  - `PyPDF2` ou `pdfplumber`, `python-docx`, `openpyxl`, `pytesseract`, `Pillow`

- [x] 11.7 Tester la pipeline RAG
  - Extraire le texte d'un PDF test → chunker → embeddings → insérer dans `doc_chunks` → recherche sémantique

### Comment

1. Le chunker doit produire des morceaux de ~800 tokens avec 200 tokens de recouvrement
2. Les embeddings transforment chaque chunk en vecteur 1024 dimensions
3. pgvector + index HNSW permettent une recherche sémantique rapide
4. Commencer par le PDF (cas le plus fréquent), ajouter OCR ensuite

---

## Étape 12 — Upload documents + analyse

**Fichiers concernés** : [05_api_endpoints.md](../05_api_endpoints.md#documents) · [03_systeme_skills.md](../03_systeme_skills.md#skill--analyze_document)

### À faire

- [x] 12.1 Créer `backend/app/api/documents.py` — router `/api/documents`

- [x] 12.2 Endpoint `POST /api/documents/upload`
  - Accepte `multipart/form-data` : fichier + `entreprise_id`
  - Validation : types autorisés (PDF, PNG, JPEG, DOCX, XLSX)
  - Sauvegarde le fichier dans `uploads/{entreprise_id}/`
  - Extrait le texte via `text_extractor`
  - Crée les chunks + embeddings via pipeline RAG
  - Insère dans tables `documents` + `doc_chunks`
  - Voir [05_api_endpoints.md](../05_api_endpoints.md#documents)

- [x] 12.3 Endpoint `GET /api/documents/entreprise/{id}`
  - Liste les documents d'une entreprise

- [x] 12.4 Endpoint `GET /api/documents/{id}`
  - Détail d'un document (métadonnées + nombre de chunks)

- [x] 12.5 Endpoint `DELETE /api/documents/{id}`
  - Supprime le document, ses chunks, et le fichier physique

- [x] 12.6 Implémenter le handler `analyze_document`
  - Récupère le document et ses chunks depuis la BDD
  - Si pas encore chunké → lance la pipeline RAG
  - Fait des recherches sémantiques par type d'analyse (`esg_compliance`, `financial`, `carbon`)
  - Retourne les passages pertinents extraits
  - Code de référence dans [03_systeme_skills.md](../03_systeme_skills.md#skill--analyze_document)

- [x] 12.7 Créer les schemas Pydantic `backend/app/schemas/document.py`

- [x] 12.8 Tester : uploader un PDF → vérifier les chunks en BDD → demander à l'agent "analyse ce document"

### Comment

1. L'upload est synchrone pour le MVP (chunking + embedding dans la même requête)
2. Le handler `analyze_document` est appelé par le LLM quand l'utilisateur parle d'un document
3. Les requêtes de recherche sémantique dépendent du type d'analyse demandé

---

## Étape 13 — Score ESG multi-référentiel

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--calculate_esg_score-v2--multi-référentiel) · [02_modeles_donnees.md](../02_modeles_donnees.md#referentiels_esg-nouveau)

### À faire

- [x] 13.1 Implémenter le handler `calculate_esg_score` (version multi-référentiel)
  - Entrées : `entreprise_id`, `data` (réponses aux critères), `referentiel_codes` (optionnel)
  - Charge la grille du/des référentiel(s) depuis la BDD
  - Pour chaque critère : calcule le score selon son type (quantitatif → seuils, qualitatif → options)
  - Agrège par pilier (poids des critères) puis en score global (poids des piliers)
  - Gère 2 méthodes : `weighted_average` et `threshold`
  - Sauvegarde dans `esg_scores`
  - Identifie les données manquantes + retourne les `questions_manquantes`
  - → `backend/app/skills/handlers/calculate_esg_score.py`

- [x] 13.2 Fonctions utilitaires de scoring
  - `_score_quantitatif(valeur, seuils)` → score 0-100 (avec conversion auto string→float)
  - `_score_qualitatif(valeur, options)` → score 0-100 (insensible à la casse + correspondance partielle)
  - `_statut(score)` → "conforme" / "partiel" / "non_conforme"
  - `_niveau(score)` → "Excellent" / "Bon" / "À améliorer" / "Insuffisant"

- [x] 13.3 Compléter le handler `list_referentiels`
  - Ajout paramètre `include_criteres` → retourne les questions_collecte, options, unités
  - Filtrage par région et par fonds (déjà en place)
  - Schema du skill mis à jour en BDD

- [x] 13.4 Ajouter endpoints scores dans `backend/app/api/entreprises.py`
  - `GET /api/entreprises/{id}/scores` — historique avec filtre par référentiel + pagination
  - `GET /api/entreprises/{id}/scores/{score_id}` — détail complet par critère
  - Schemas Pydantic dans `backend/app/schemas/esg.py`

- [x] 13.5 Tester le scoring via le chat
  - Via le chat : "Calcule mon score ESG selon le référentiel BCEAO" ✅
  - L'agent pose les 12 questions (3 piliers × 4 critères) ✅
  - Le skill `calculate_esg_score` est appelé et sauvegarde en BDD ✅
  - L'endpoint `GET /api/entreprises/{id}/scores` retourne l'historique ✅
  - Note : les réponses qualitatives en texte libre ont un matching partiel,
    les réponses doivent correspondre aux labels exacts des options pour un score optimal

### Comment

1. La grille vient de `referentiels_esg.grille_json` (pas codée en dur)
2. Le LLM collecte les données conversationnellement en posant les `question_collecte` de chaque critère
3. Quand il a assez de données, il appelle `calculate_esg_score` avec les réponses
4. Le résultat inclut le score par pilier, par critère, et les données manquantes

---

## Étape 14 — Recherche fonds verts (SQL + RAG)

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--search_green_funds) · [02_modeles_donnees.md](../02_modeles_donnees.md#fonds_verts--fonds_chunks-rag)

### À faire

- [x] 14.1 Implémenter le handler `search_green_funds`
  - Filtrage SQL sur `fonds_verts` (secteur, pays, date_limite, montant)
  - Recherche RAG dans `fonds_chunks` pour les critères détaillés
  - Score de compatibilité (secteur +15, pays +10, montant +10, ESG +15, RAG +5)
  - Tri par compatibilité décroissante
  - → `backend/app/skills/handlers/search_green_funds.py`

- [x] 14.2 Peupler `fonds_chunks` pour les fonds du seed
  - 5 fonds × 3 descriptions (éligibilité, critères, processus) = 16 chunks
  - Embeddings via Voyage AI + insertion dans `fonds_chunks`
  - → `backend/app/seed/seed_fonds_chunks.py`
  - Intégré dans `python -m app.seed` (étape 5/5)

- [x] 14.3 Tester via le chat
  - "Quels fonds verts sont disponibles pour une entreprise de recyclage en CI ?" ✅
  - FAGACE 100%, BOAD-PME 95%, GCF 75% (score ESG insuffisant) ✅
  - Détails RAG : documents requis, délais, conditions extraits des chunks ✅

### Comment

1. Le filtrage SQL élimine rapidement les fonds non pertinents (secteur, pays, date)
2. Le RAG affine en cherchant dans les détails des critères d'éligibilité
3. Le score de compatibilité est un calcul simple (bonus si score ESG > 60, si montant dans la fourchette, etc.)

---

## Étape 15 — Calculateur empreinte carbone

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--calculate_carbon_footprint) · [02_modeles_donnees.md](../02_modeles_donnees.md#carbon_footprints-historique-empreinte-carbone)

### À faire

- [ ] 15.1 Implémenter le handler `calculate_carbon_footprint`
  - Entrées : `entreprise_id`, `data` (electricite_kwh, generateur_litres, vehicules_km, type_carburant, dechets_tonnes, achats_montant)
  - Charge les facteurs d'émission depuis `data/facteurs_emission.json` (contextualisés par pays)
  - Calcule : chaque donnée d'activité × facteur d'émission
  - Répartition par source : énergie, transport, déchets, achats
  - Sauvegarde dans `carbon_footprints`
  - Compare avec la moyenne sectorielle via `sector_benchmarks`

- [ ] 15.2 Créer/compléter `data/facteurs_emission.json`
  - Facteurs par pays : CI (mix énergétique ~0.45 kgCO2/kWh), SEN, CMR
  - Facteurs par source : diesel (2.68 kgCO2/L), essence (2.31), etc.

- [ ] 15.3 Créer `backend/app/api/carbon.py`
  - `GET /api/carbon/entreprise/{id}` — historique empreinte carbone
  - `GET /api/carbon/entreprise/{id}/evolution` — évolution mensuelle/annuelle

- [ ] 15.4 Tester via le chat
  - "Calcule mon empreinte carbone, je consomme 15000 kWh d'électricité par an et j'ai 3 véhicules diesel"

### Comment

1. Les facteurs d'émission sont dans un fichier JSON statique (pas en BDD pour simplifier)
2. Le calcul est : `total_tco2e = Σ (activité × facteur_emission)`
3. Le handler stocke le résultat et retourne la répartition + comparaison sectorielle

---

## Étape 16 — Plan de réduction carbone

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--generate_reduction_plan)

### À faire

- [ ] 16.1 Implémenter le handler `generate_reduction_plan`
  - Récupère la dernière `carbon_footprint` de l'entreprise
  - Identifie les sources les plus émettrices
  - Propose des actions classées en `quick_win` (< 3 mois), `moyen_terme` (3-12 mois), `long_terme` (> 12 mois)
  - Estime la réduction en tCO2e et les économies financières pour chaque action
  - Crée automatiquement les `action_items` associés

- [ ] 16.2 Créer une base de connaissances des actions de réduction
  - Fichier JSON ou données dans `data/knowledge_base/` avec des actions types par secteur
  - Ex : remplacement éclairage LED, panneaux solaires, véhicules électriques, compostage, etc.

- [ ] 16.3 Tester : "Génère un plan de réduction carbone pour mon entreprise"

### Comment

1. Le plan est généré à partir des données carbone existantes
2. Les actions sont priorisées par rapport coût/impact
3. Chaque action a un impact estimé et un coût estimé en devise locale (XOF)

---

## Étape 17 — Simulateur de financement

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--simulate_funding)

### À faire

- [ ] 17.1 Implémenter le handler `simulate_funding`
  - Entrées : `entreprise_id`, `fonds_id`, `montant_demande` (optionnel)
  - Charge le fonds et son référentiel associé
  - Récupère le score ESG de l'entreprise selon ce référentiel
  - Vérifie les critères d'éligibilité
  - Calcule : `eligible` (bool), `montant_estime`, `criteres_manquants`, `timeline_estimee`, `roi_vert`

- [ ] 17.2 Tester : "Suis-je éligible au Fonds Vert pour le Climat ? Simule ma candidature"

### Comment

1. Le simulateur combine les données du fonds (critères, montants) avec le profil de l'entreprise (scores, secteur)
2. Si critères manquants → les lister pour que l'agent guide l'utilisateur

---

## Étape 18 — Benchmarking sectoriel

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--get_sector_benchmark)

### À faire

- [ ] 18.1 Implémenter le handler `get_sector_benchmark`
  - Entrées : `secteur`, `pays` (optionnel), `referentiel_code` (optionnel)
  - Requête sur `sector_benchmarks`
  - Si pas de benchmark existant → le calculer à partir des données en BDD
  - Retourne : moyennes E/S/G, score global, empreinte carbone, taille échantillon

- [ ] 18.2 Créer `backend/app/api/benchmark.py`
  - `GET /api/benchmark/secteur/{secteur}` — moyennes sectorielles

- [ ] 18.3 Tester : "Comment je me situe par rapport aux autres entreprises de recyclage en CI ?"

### Comment

1. Les benchmarks initiaux viennent du seed (Semaine 1)
2. À terme, ils se mettent à jour automatiquement à mesure que des entreprises s'inscrivent

---

## Récapitulatif Semaine 3

| # | Étape | Statut |
|---|-------|--------|
| 11 | RAG : chunker, embeddings, search | ✅ |
| 12 | Upload documents + analyse | ✅ |
| 13 | Score ESG multi-référentiel | ✅ |
| 14 | Recherche fonds verts (SQL + RAG) | ✅ |
| 15 | Calculateur empreinte carbone | ⬜ |
| 16 | Plan de réduction carbone | ⬜ |
| 17 | Simulateur de financement | ⬜ |
| 18 | Benchmarking sectoriel | ⬜ |

**Critère de fin de semaine** : L'agent peut analyser des documents uploadés, calculer un score ESG multi-référentiel, calculer l'empreinte carbone, proposer un plan de réduction, rechercher des fonds verts compatibles, simuler un financement, et comparer avec les moyennes sectorielles — le tout via la conversation.

---

## Fichiers du plan à consulter

| Fichier | Quand le consulter |
|---------|-------------------|
| [02_modeles_donnees.md](../02_modeles_donnees.md) | Tables documents, doc_chunks, referentiels_esg, fonds_verts, carbon_footprints, sector_benchmarks |
| [03_systeme_skills.md](../03_systeme_skills.md) | Code complet de tous les handlers (analyze_document, calculate_esg_score, search_green_funds, calculate_carbon, etc.) |
| [05_api_endpoints.md](../05_api_endpoints.md) | Endpoints documents, carbon, benchmark |
