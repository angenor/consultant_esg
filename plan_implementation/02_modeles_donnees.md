# 02 - Modèles de Données

## Diagramme Relationnel

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users      │     │   entreprises     │     │  conversations   │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK)      │◄──┐ │ id (PK)          │◄──┐ │ id (PK)          │
│ email        │   │ │ user_id (FK)     │   │ │ entreprise_id(FK)│
│ password_hash│   │ │ nom              │   │ │ titre            │
│ nom_complet  │   │ │ secteur          │   │ │ created_at       │
│ role         │   │ │ pays             │   │ │ updated_at       │
│ is_active    │   │ │ ville            │   │ └────────┬─────────┘
│ created_at   │   │ │ effectifs        │   │          │
└──────────────┘   │ │ chiffre_affaires │   │          │
                   │ │ description      │   │ ┌────────▼─────────┐
                   │ │ profil_json      │   │ │    messages       │
                   │ │ created_at       │   │ ├──────────────────┤
                   │ └──────────────────┘   │ │ id (PK)          │
                   │          │              │ │ conversation_id  │
                   │          │              │ │ role (user/asst)  │
                   │          ▼              │ │ content          │
                   │ ┌──────────────────┐   │ │ tool_calls_json  │
                   │ │    documents      │   │ │ created_at       │
                   │ ├──────────────────┤   │ └──────────────────┘
                   │ │ id (PK)          │   │
                   │ │ entreprise_id(FK)│   │
                   │ │ nom_fichier      │   │
                   │ │ type_mime        │   │
                   │ │ chemin_stockage  │   │
                   │ │ taille           │   │
                   │ │ texte_extrait    │   │
                   │ │ created_at       │   │
                   │ └────────┬─────────┘   │
                   │          │              │
                   │          ▼              │
                   │ ┌──────────────────┐   │
                   │ │  doc_chunks       │   │
                   │ ├──────────────────┤   │
                   │ │ id (PK)          │   │
                   │ │ document_id (FK) │   │
                   │ │ contenu          │   │
                   │ │ embedding(vector)│   │
                   │ │ page_number      │   │
                   │ │ chunk_index      │   │
                   │ └──────────────────┘   │
                   │                         │
┌──────────────┐   │ ┌──────────────────┐   │
│    skills     │   │ │   esg_scores     │   │
├──────────────┤   │ ├──────────────────┤   │
│ id (PK)      │   │ │ id (PK)          │   │
│ nom          │   │ │ entreprise_id(FK)├───┘
│ description  │   │ │ referentiel_id(FK)──┐
│ input_schema │   │ │ score_e          │  │
│ handler_key  │   │ │ score_s          │  │
│ handler_code │   │ │ score_g          │  │
│ is_active    │   │ │ score_global     │  │
│ category     │   │ │ details_json     │  │
│ version      │   │ │ source (auto/doc)│  │
│ created_by   ├───┘ │ created_at       │  │
│ created_at   │     └──────────────────┘  │
│ updated_at   │                            │
└──────────────┘  ┌─────────────────────┐  │
                  │ referentiels_esg     │  │
                  ├─────────────────────┤  │
                  │ id (PK)             │◄─┘
                  │ nom                 │
                  │ code (UNIQUE)       │
                  │ institution         │
                  │ description         │
                  │ region              │
                  │ grille_json         │◄── piliers, critères, poids
                  │ is_active           │
                  │ created_at          │
                  │ updated_at          │
                  └─────────────────────┘

                     ┌──────────────────┐
                     │   fonds_verts     │
                     ├──────────────────┤
                     │ id (PK)          │
                     │ nom              │
                     │ institution      │
                     │ type             │
                     │ referentiel_id(FK)──► referentiels_esg
                     │ montant_min      │
                     │ montant_max      │
                     │ secteurs_json    │
                     │ pays_eligibles   │
                     │ criteres_json    │
                     │ date_limite      │
                     │ url_source       │
                     │ is_active        │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │ fonds_chunks      │
                     ├──────────────────┤
                     │ id (PK)          │
                     │ fonds_id (FK)    │
                     │ contenu          │
                     │ embedding(vector)│
                     │ type_info        │
                     └──────────────────┘
```

## Détail des Tables

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom_complet VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- 'user', 'admin'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### entreprises
```sql
CREATE TABLE entreprises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    secteur VARCHAR(100),         -- agriculture, energie, recyclage, etc.
    sous_secteur VARCHAR(100),
    pays VARCHAR(100) DEFAULT 'Côte d''Ivoire',
    ville VARCHAR(100),
    effectifs INTEGER,
    chiffre_affaires DECIMAL,
    devise VARCHAR(10) DEFAULT 'XOF',
    description TEXT,
    -- Profil enrichi par l'agent au fil des conversations
    profil_json JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Exemple de profil_json enrichi par l'agent :
-- {
--   "pratiques_environnementales": ["tri des déchets", "panneaux solaires"],
--   "certifications": [],
--   "fournisseurs_principaux": ["..."],
--   "risques_identifies": ["..."],
--   "objectifs_declares": ["réduire consommation eau"]
-- }
```

### conversations & messages
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    titre VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    -- Stocke les appels de skills faits par le LLM dans ce tour
    tool_calls_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
```

### skills (table centrale pour l'admin)
```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(100) UNIQUE NOT NULL,         -- ex: "analyze_document"
    description TEXT NOT NULL,                 -- description pour Claude
    category VARCHAR(50),                      -- "esg", "finance", "carbon", "report", "utils"
    input_schema JSONB NOT NULL,               -- JSON Schema des paramètres
    -- Référence à la fonction Python enregistrée
    handler_key VARCHAR(100) NOT NULL,         -- ex: "builtin.analyze_document"
    -- OU code Python personnalisé (pour skills créés par l'admin)
    handler_code TEXT,                         -- code Python du skill
    -- Métadonnées
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Exemples de handler_key :
-- "builtin.analyze_document"  → fonction Python dans le code source
-- "builtin.search_green_funds" → fonction Python dans le code source
-- "custom.mon_skill"          → exécute handler_code (Python sandboxé)
```

### documents & doc_chunks (RAG)
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    nom_fichier VARCHAR(255) NOT NULL,
    type_mime VARCHAR(100),
    chemin_stockage VARCHAR(500) NOT NULL,
    taille INTEGER,
    texte_extrait TEXT,          -- texte brut extrait (OCR ou parsing)
    metadata_json JSONB,         -- pages, langue détectée, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE doc_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    embedding vector(1024),      -- pgvector, dimension selon le modèle d'embedding
    page_number INTEGER,
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_doc_chunks_embedding ON doc_chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### referentiels_esg (NOUVEAU)
```sql
CREATE TABLE referentiels_esg (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(255) NOT NULL,              -- "BCEAO Finance Durable 2024"
    code VARCHAR(50) UNIQUE NOT NULL,       -- "bceao_fd_2024"
    institution VARCHAR(255),               -- "BCEAO"
    description TEXT,
    region VARCHAR(100),                    -- "UEMOA", "International", "Europe"
    -- Grille complète : piliers, critères, poids, seuils
    grille_json JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Exemple grille_json :
-- {
--   "methode_aggregation": "weighted_average",  -- ou "threshold"
--   "piliers": {
--     "environnement": {
--       "poids_global": 0.40,
--       "criteres": [
--         {
--           "id": "emissions_carbone",
--           "label": "Émissions de gaz à effet de serre",
--           "poids": 0.30,
--           "type": "quantitatif",
--           "unite": "tCO2e/an",
--           "seuils": {
--             "excellent": {"max": 50, "score": 100},
--             "bon": {"max": 200, "score": 70},
--             "moyen": {"max": 500, "score": 40},
--             "faible": {"min": 500, "score": 10}
--           },
--           "question_collecte": "Estimez vos émissions annuelles de CO2"
--         },
--         {
--           "id": "gestion_dechets",
--           "label": "Gestion et valorisation des déchets",
--           "poids": 0.25,
--           "type": "qualitatif",
--           "options": [
--             {"label": "Politique formelle + recyclage actif", "score": 100},
--             {"label": "Tri sélectif en place", "score": 70},
--             {"label": "Collecte basique", "score": 40},
--             {"label": "Aucune gestion structurée", "score": 10}
--           ],
--           "question_collecte": "Comment gérez-vous vos déchets ?"
--         }
--       ]
--     },
--     "social": { "poids_global": 0.30, "criteres": [...] },
--     "gouvernance": { "poids_global": 0.30, "criteres": [...] }
--   }
-- }
--
-- Chaque fonds/institution peut avoir son propre référentiel :
-- BCEAO → pondère fortement la gouvernance
-- Fonds Vert pour le Climat → pondère fortement l'environnement (60%)
-- IFC → critères spécifiques par secteur
-- Même entreprise, mêmes données, scores différents selon le référentiel
```

### esg_scores
```sql
CREATE TABLE esg_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    referentiel_id UUID REFERENCES referentiels_esg(id),  -- Lien vers le référentiel utilisé
    score_e DECIMAL(5,2),        -- 0-100
    score_s DECIMAL(5,2),
    score_g DECIMAL(5,2),
    score_global DECIMAL(5,2),
    -- Détail par critère selon le référentiel
    details_json JSONB NOT NULL,
    -- Source : questionnaire conversationnel ou analyse de documents
    source VARCHAR(20) DEFAULT 'conversation',  -- 'conversation', 'document', 'hybrid'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Une entreprise a PLUSIEURS scores (un par référentiel)
CREATE UNIQUE INDEX idx_score_per_referentiel
    ON esg_scores(entreprise_id, referentiel_id, created_at);

-- Exemple details_json :
-- {
--   "referentiel": "BCEAO Finance Durable 2024",
--   "methode": "weighted_average",
--   "environnement": {
--     "score": 58.5,
--     "poids_global": 0.40,
--     "criteres": [
--       {"id": "emissions_carbone", "label": "Émissions GES", "score": 40,
--        "statut": "partiel", "valeur_brute": 350, "unite": "tCO2e/an"},
--       {"id": "gestion_dechets", "label": "Gestion déchets", "score": 70,
--        "statut": "conforme", "valeur_brute": "Tri sélectif en place"}
--     ]
--   },
--   "social": { ... },
--   "gouvernance": { ... }
-- }
```

### fonds_verts & fonds_chunks (RAG)
```sql
CREATE TABLE fonds_verts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(255) NOT NULL,
    institution VARCHAR(255),
    type VARCHAR(50),            -- 'subvention', 'pret', 'credit_carbone', 'garantie'
    -- Lien vers le référentiel ESG utilisé par ce fonds
    referentiel_id UUID REFERENCES referentiels_esg(id),
    montant_min DECIMAL,
    montant_max DECIMAL,
    devise VARCHAR(10) DEFAULT 'USD',
    secteurs_json JSONB,         -- ["agriculture", "energie", "recyclage"]
    pays_eligibles JSONB,        -- ["CIV", "SEN", "CMR"]
    criteres_json JSONB,         -- critères d'éligibilité structurés
    date_limite DATE,
    url_source VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fonds_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fonds_id UUID REFERENCES fonds_verts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    embedding vector(1024),
    type_info VARCHAR(50),       -- 'procedure', 'criteres', 'faq', 'formulaire'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fonds_chunks_embedding ON fonds_chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### report_templates (templates de rapports gérés par l'admin)
```sql
CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(100) UNIQUE NOT NULL,   -- 'esg_full', 'carbon', 'funding_application'
    description TEXT,
    -- Structure des sections du rapport
    sections_json JSONB NOT NULL,
    -- Template HTML/CSS (Jinja2)
    template_html TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Exemple sections_json :
-- [
--   {"id": "page_garde", "titre": "Page de garde", "source": "db"},
--   {"id": "resume", "titre": "Résumé Exécutif", "source": "llm", "prompt": "..."},
--   {"id": "score_e", "titre": "Environnement", "source": "llm", "prompt": "..."},
--   {"id": "charts", "titre": "Graphiques", "source": "code"},
--   {"id": "plan", "titre": "Plan d'action", "source": "llm", "prompt": "..."}
-- ]
```

### carbon_footprints (historique empreinte carbone)
```sql
CREATE TABLE carbon_footprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    annee INTEGER NOT NULL,
    mois INTEGER,                    -- NULL = bilan annuel
    -- Émissions par source (tCO2e)
    energie DECIMAL(10,2) DEFAULT 0,       -- électricité, générateurs, gaz
    transport DECIMAL(10,2) DEFAULT 0,     -- véhicules, livraisons
    dechets DECIMAL(10,2) DEFAULT 0,       -- volumes, traitement
    achats DECIMAL(10,2) DEFAULT 0,        -- matières premières, fournitures
    total_tco2e DECIMAL(10,2) NOT NULL,
    details_json JSONB,
    -- Exemple details_json :
    -- {
    --   "energie": {
    --     "electricite_kwh": 15000, "generateur_litres": 500,
    --     "facteur_emission_pays": 0.45
    --   },
    --   "transport": {
    --     "vehicules_km": 30000, "type_carburant": "diesel"
    --   }
    -- }
    source VARCHAR(20) DEFAULT 'conversation',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_carbon_entreprise ON carbon_footprints(entreprise_id, annee, mois);
```

### credit_scores (scoring crédit vert alternatif — Module 5)
```sql
CREATE TABLE credit_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    score_solvabilite DECIMAL(5,2),    -- 0-100 (capacité financière)
    score_impact_vert DECIMAL(5,2),    -- 0-100 (engagement ESG)
    score_combine DECIMAL(5,2),        -- 0-100 (pondéré)
    -- Données sources utilisées pour le calcul
    donnees_financieres_json JSONB,
    -- {
    --   "regularite_transactions": 85,
    --   "volume_mensuel_moyen": 2500000,
    --   "anciennete_mois": 36,
    --   "source": "declaratif"  -- ou "mobile_money" si intégration
    -- }
    donnees_esg_json JSONB,
    -- {
    --   "dernier_score_esg": 62.5,
    --   "referentiel": "BCEAO",
    --   "tendance": "hausse",
    --   "certifications": []
    -- }
    donnees_declaratives_json JSONB,
    -- {
    --   "pratiques_vertes": ["tri_dechets", "solaire"],
    --   "projets_verts_en_cours": true,
    --   "participation_programmes": ["REDD+"]
    -- }
    facteurs_json JSONB NOT NULL,       -- explication transparente de chaque facteur
    -- {
    --   "facteurs_positifs": [
    --     {"facteur": "Score ESG > 60", "impact": "+15"},
    --     {"facteur": "Transactions régulières", "impact": "+10"}
    --   ],
    --   "facteurs_negatifs": [
    --     {"facteur": "Pas de certification", "impact": "-5"}
    --   ]
    -- }
    created_at TIMESTAMP DEFAULT NOW()
);
```

### action_plans & action_items (plans d'action et suivi — Module 6)
```sql
CREATE TABLE action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entreprise_id UUID REFERENCES entreprises(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    horizon VARCHAR(20),              -- '6_mois', '12_mois', '24_mois'
    referentiel_id UUID REFERENCES referentiels_esg(id),
    score_initial DECIMAL(5,2),       -- score ESG au moment de la création
    score_cible DECIMAL(5,2),         -- score ESG visé
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES action_plans(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    priorite VARCHAR(20),             -- 'quick_win', 'moyen_terme', 'long_terme'
    pilier VARCHAR(20),               -- 'environnement', 'social', 'gouvernance'
    critere_id VARCHAR(100),          -- lien vers le critère du référentiel visé
    statut VARCHAR(20) DEFAULT 'a_faire',  -- 'a_faire', 'en_cours', 'fait'
    echeance DATE,
    impact_score_estime DECIMAL(5,2), -- gain estimé sur le score
    cout_estime DECIMAL,              -- en devise locale
    benefice_estime DECIMAL,          -- économies / revenus estimés
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_action_items_plan ON action_items(plan_id, statut);
```

### notifications (rappels et alertes)
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    -- Types : 'rappel_action', 'echeance_fonds', 'nouveau_fonds',
    --         'progres_score', 'action_completee'
    titre VARCHAR(255) NOT NULL,
    contenu TEXT,
    lien VARCHAR(500),               -- route frontend vers l'élément concerné
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
```

### sector_benchmarks (moyennes sectorielles pour comparaison)
```sql
CREATE TABLE sector_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    secteur VARCHAR(100) NOT NULL,
    pays VARCHAR(100),                -- NULL = tous pays
    referentiel_id UUID REFERENCES referentiels_esg(id),
    score_e_moyen DECIMAL(5,2),
    score_s_moyen DECIMAL(5,2),
    score_g_moyen DECIMAL(5,2),
    score_global_moyen DECIMAL(5,2),
    carbone_moyen_tco2e DECIMAL(10,2),
    nombre_entreprises INTEGER,       -- taille de l'échantillon
    periode VARCHAR(20),              -- '2024_Q4', '2025_Q1'
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_benchmark_unique
    ON sector_benchmarks(secteur, COALESCE(pays, ''), referentiel_id, periode);
```
