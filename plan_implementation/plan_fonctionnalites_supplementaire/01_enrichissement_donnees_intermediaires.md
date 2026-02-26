# Phase 1 : Enrichissement des donnees intermediaires

## Dependances

**Prerequis :** Aucun (phase de base)
**Bloque :** Phase 2 (Skills LLM), Phase 3 (Generation dossiers), Phase 5 (Configs extension)

## Progression

- [x] 1.1 Creer le modele SQLAlchemy `Intermediaire` (`backend/app/models/intermediaire.py`)
- [x] 1.2 Creer les schemas Pydantic (`backend/app/schemas/intermediaire.py`)
- [x] 1.3 Creer la migration Alembic + executer `alembic upgrade head`
- [x] 1.4 Creer le fichier seed `data/intermediaires.json` (~46 intermediaires)
- [x] 1.5 Creer le script `backend/app/seed/seed_intermediaires.py` + integrer dans `__main__.py`
- [x] 1.6 Creer les API endpoints (`backend/app/api/intermediaires.py`) : GET publique + CRUD admin
- [x] 1.7 Creer la vue admin frontend (`frontend/src/views/admin/IntermediairesView.vue`)

## Objectif

Enrichir chaque fonds vert avec des donnees structurees sur les intermediaires, les liens de soumission, les contacts, et les processus detailles. Ces donnees alimenteront les skills LLM, l'extension Chrome, et l'interface de suivi.

## Etat actuel

### Ce qui existe deja
- 10 fonds avec `mode_acces` (banque_partenaire, entite_accreditee, etc.)
- `acces_details` dans `criteres_json` : intermediaire (texte), etapes[], delai_estime, periodicite, documents_requis[]
- RAG chunks (3 par fonds : eligibilite, criteres, processus)
- 1 seule FundSiteConfig (BOAD)

### Ce qui manque
- **Liste des intermediaires concrets** (noms, contacts, URLs) par pays
- **Liens de formulaires/soumission** pour chaque intermediaire
- **Types de formulaires** (en ligne vs dossier papier/email)
- **Contacts specifiques** (email, telephone, adresse)
- **Documents requis par intermediaire** (pas seulement par fonds)

## Nouveau modele de donnees

### Option retenue : Table `Intermediaire` + enrichissement JSONB

On cree une nouvelle table `intermediaires` pour stocker les intermediaires de facon normalisee, referencable et interrogeable par le LLM.

### Table `intermediaires`

```sql
CREATE TABLE intermediaires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fonds_id UUID NOT NULL REFERENCES fonds_verts(id) ON DELETE CASCADE,
    nom VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'banque_partenaire', 'entite_accreditee', 'agence_nationale', 'bmd'
    pays VARCHAR(100),          -- NULL = tous pays eligibles
    ville VARCHAR(100),

    -- Contact
    email VARCHAR(200),
    telephone VARCHAR(50),
    adresse TEXT,
    site_web VARCHAR(500),

    -- Soumission
    url_formulaire VARCHAR(500),        -- Lien direct vers le formulaire en ligne
    type_soumission VARCHAR(30),        -- 'formulaire_en_ligne', 'email', 'dossier_physique', 'portail_dedie'
    instructions_soumission TEXT,       -- Instructions specifiques a cet intermediaire

    -- Documents requis par cet intermediaire (peut differer du fonds)
    documents_requis JSONB,             -- [{"nom": "...", "format": "pdf", "obligatoire": true}]

    -- Processus specifique a cet intermediaire
    etapes_specifiques JSONB,           -- ["Etape 1", "Etape 2", ...]
    delai_traitement VARCHAR(50),       -- "2-4 semaines"

    -- Meta
    est_recommande BOOLEAN DEFAULT false,  -- Intermediaire prefere/recommande
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_intermediaires_fonds ON intermediaires(fonds_id);
CREATE INDEX idx_intermediaires_pays ON intermediaires(pays);
CREATE INDEX idx_intermediaires_type ON intermediaires(type);
```

### Migration Alembic

```
backend/migrations/versions/xxxx_create_intermediaires_table.py
```

## Fichiers a creer/modifier

### 1. Nouveau modele SQLAlchemy

**Fichier :** `backend/app/models/intermediaire.py`

```python
from uuid import uuid4
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Intermediaire(Base):
    __tablename__ = "intermediaires"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    fonds_id: Mapped[str] = mapped_column(ForeignKey("fonds_verts.id", ondelete="CASCADE"))
    nom: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))
    pays: Mapped[str | None] = mapped_column(String(100))
    ville: Mapped[str | None] = mapped_column(String(100))

    email: Mapped[str | None] = mapped_column(String(200))
    telephone: Mapped[str | None] = mapped_column(String(50))
    adresse: Mapped[str | None] = mapped_column(Text)
    site_web: Mapped[str | None] = mapped_column(String(500))

    url_formulaire: Mapped[str | None] = mapped_column(String(500))
    type_soumission: Mapped[str | None] = mapped_column(String(30))
    instructions_soumission: Mapped[str | None] = mapped_column(Text)

    documents_requis: Mapped[dict | None] = mapped_column(JSONB)
    etapes_specifiques: Mapped[list | None] = mapped_column(JSONB)
    delai_traitement: Mapped[str | None] = mapped_column(String(50))

    est_recommande: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relation
    fonds = relationship("FondsVert", backref="intermediaires")
```

### 2. Schemas Pydantic

**Fichier :** `backend/app/schemas/intermediaire.py`

```python
# IntermediaireResponse, IntermediaireCreateRequest, IntermediaireUpdateRequest
# Expose tous les champs pertinents pour l'API
```

### 3. Donnees seed

**Fichier :** `data/intermediaires.json`

Structure pour les 10 fonds avec intermediaires reels :

#### BOAD-PME (mode: banque_partenaire)
```json
[
  {
    "fonds_code": "BOAD-PME",
    "intermediaires": [
      {
        "nom": "Societe Generale Cote d'Ivoire (SGCI)",
        "type": "banque_partenaire",
        "pays": "Cote d'Ivoire",
        "ville": "Abidjan",
        "email": "entreprises@sgci.ci",
        "telephone": "+225 27 20 20 12 34",
        "site_web": "https://www.societegenerale.ci",
        "url_formulaire": "https://www.societegenerale.ci/fr/entreprises/financement",
        "type_soumission": "formulaire_en_ligne",
        "documents_requis": [
          {"nom": "Etats financiers 3 derniers exercices", "format": "pdf", "obligatoire": true},
          {"nom": "Plan d'affaires vert", "format": "pdf/docx", "obligatoire": true},
          {"nom": "Registre de commerce (RCCM)", "format": "pdf", "obligatoire": true},
          {"nom": "Etude d'impact environnemental", "format": "pdf", "obligatoire": false}
        ],
        "delai_traitement": "4-6 semaines",
        "est_recommande": true
      },
      {
        "nom": "Ecobank Cote d'Ivoire",
        "type": "banque_partenaire",
        "pays": "Cote d'Ivoire",
        "ville": "Abidjan",
        "site_web": "https://www.ecobank.com/ci",
        "type_soumission": "email",
        "delai_traitement": "6-8 semaines"
      },
      {
        "nom": "Banque Atlantique Senegal",
        "type": "banque_partenaire",
        "pays": "Senegal",
        "ville": "Dakar",
        "site_web": "https://www.banqueatlantique.net",
        "type_soumission": "formulaire_en_ligne",
        "delai_traitement": "4-6 semaines"
      }
    ]
  }
]
```

#### GCF (mode: entite_accreditee)
```json
{
  "fonds_code": "GCF",
  "intermediaires": [
    {
      "nom": "BOAD (Entite Accreditee regionale)",
      "type": "entite_accreditee",
      "pays": null,
      "site_web": "https://www.boad.org",
      "url_formulaire": "https://www.boad.org/fr/gcf",
      "type_soumission": "portail_dedie",
      "notes": "Couvre les 8 pays UEMOA"
    },
    {
      "nom": "Autorite Nationale Designee - Cote d'Ivoire",
      "type": "agence_nationale",
      "pays": "Cote d'Ivoire",
      "ville": "Abidjan",
      "email": "nda@environnement.gouv.ci",
      "type_soumission": "dossier_physique",
      "notes": "Lettre de non-objection obligatoire avant soumission GCF"
    },
    {
      "nom": "CSE - Centre de Suivi Ecologique",
      "type": "entite_accreditee",
      "pays": "Senegal",
      "ville": "Dakar",
      "site_web": "https://www.cse.sn",
      "url_formulaire": null,
      "type_soumission": "email",
      "notes": "Accredite GCF pour le Senegal"
    }
  ]
}
```

*(idem pour les 8 autres fonds - voir details complets dans le fichier seed)*

### 4. Script de seed

**Fichier :** `backend/app/seed/seed_intermediaires.py`

```python
async def seed_intermediaires(db: AsyncSession) -> int:
    """Charge les intermediaires depuis le JSON et les insere/met a jour."""
    # Meme pattern upsert que seed_fonds.py
    # Correspondance fonds_code -> fonds_id via lookup
```

### 5. Mise a jour `backend/app/seed/__main__.py`

Ajouter l'appel a `seed_intermediaires()` apres `seed_fonds()`.

### 6. API endpoints

**Fichier :** `backend/app/api/intermediaires.py` (nouveau)

```python
# GET /api/intermediaires/fonds/{fonds_id}         -> Liste par fonds
# GET /api/intermediaires/fonds/{fonds_id}/pays/{pays}  -> Filtrer par pays
# GET /api/intermediaires/{id}                      -> Detail

# Admin:
# POST /api/admin/intermediaires/                   -> Creer
# PUT /api/admin/intermediaires/{id}                -> Modifier
# DELETE /api/admin/intermediaires/{id}             -> Supprimer
```

### 7. Frontend admin

**Fichier :** `frontend/src/views/admin/IntermediairesView.vue` (nouveau)

- Liste des intermediaires groupes par fonds
- CRUD complet
- Filtres par pays, type, fonds

### 8. Mise a jour FondsVert existant

Ajouter une relation dans le modele :

```python
# Dans fonds_vert.py
intermediaires = relationship("Intermediaire", back_populates="fonds", lazy="selectin")
```

## Donnees intermediaires par fonds (recherche)

| Fonds | Nb intermediaires | Types | Pays couverts |
|-------|-------------------|-------|---------------|
| BOAD-PME | ~8 | banque_partenaire | 8 pays UEMOA |
| BAD | ~3 | agence_nationale | Pan-africain |
| GCF | ~6 | entite_accreditee + agence_nationale | CI, SN, CM, ML, BF, GH |
| IFC | ~5 | banque_partenaire | CI, SN, CM, GH |
| FAGACE | ~6 | banque_partenaire (locale) | 8 pays UEMOA |
| BCEAO | ~6 | banque_partenaire | 8 pays UEMOA |
| SUNREF | ~4 | banque_partenaire | CI, SN, CM |
| FIDA | ~3 | agence_nationale | CI, SN, ML, BF |
| BEI-Proparco | ~2 | direct | CI, SN, CM |
| SREP/CIF | ~3 | bmd | Pan-africain |

**Total estime : ~46 intermediaires**

## Criteres de validation

- [ ] Table `intermediaires` creee avec migration Alembic
- [ ] Modele SQLAlchemy avec relations bidirectionnelles
- [ ] Seed data pour les 10 fonds (~46 intermediaires)
- [ ] API publique GET (par fonds, par pays)
- [ ] API admin CRUD
- [ ] Frontend admin pour gerer les intermediaires
- [ ] Seed script integre dans `python -m app.seed`
