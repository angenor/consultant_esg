# Phase 3 : Generation de dossiers avancee

## Dependances

**Prerequis :** Phase 1 (table `intermediaires` doit exister pour adapter les documents par intermediaire)
**Bloque :** Phase 4 (Sync plateforme-extension - le chat doit pouvoir generer des dossiers avant de proposer l'extension)

## Progression

- [x] 3.1 Creer le template `backend/app/documents/templates/fiche_projet.py`
- [x] 3.2 Creer le template `backend/app/documents/templates/note_impact_esg.py`
- [x] 3.3 Creer le template `backend/app/documents/templates/page_garde.py`
- [x] 3.4 Creer le template `backend/app/documents/templates/checklist_documents.py`
- [x] 3.5 Creer `backend/app/documents/dossier_assembler.py` (assemblage ZIP)
- [x] 3.6 Modifier `backend/app/documents/word_generator.py` : ajouter parametres fonds/intermediaire, mode template_vierge, prompts par fonds
- [x] 3.7 Creer le modele `backend/app/models/dossier_candidature.py` + migration Alembic
- [x] 3.8 Etendre `backend/app/api/reports.py` pour supporter le telechargement ZIP et les dossiers
- [x] 3.9 Creer le composant `frontend/src/components/chat/DossierGeneratedCard.vue`
- [x] 3.10 Modifier `SkillIndicator.vue` pour detecter et afficher `DossierGeneratedCard` sur les resultats du skill

## Objectif

Permettre au LLM de generer des dossiers complets de candidature aux fonds verts, adaptes a chaque fonds et intermediaire. Deux modes : **dossier pre-rempli** (avec donnees de l'entreprise) et **template vierge** (structure a remplir). Formats Word (.docx) et PDF.

## Etat actuel

### Ce qui existe deja
- `generate_document` skill : 5 types (lettre_motivation, note_presentation, plan_affaires, engagement_esg, budget_previsionnel)
- `assemble_pdf` skill : 3 templates (esg_full, carbon, funding_application)
- `word_generator.py` : generation DOCX avec python-docx, style emerald
- `generator.py` : generation PDF avec WeasyPrint + Jinja2 + matplotlib
- Toutes les dependances deja installees

### Ce qui manque
- **Adaptation par fonds/intermediaire** : les documents actuels sont generiques
- **Mode template vierge** : templates a remplir manuellement
- **Dossier complet** : generation de tous les documents en un seul appel + ZIP
- **Fiche projet** specifique (differente du plan d'affaires)
- **Note d'impact ESG** dediee a la candidature
- **Page de garde** avec logo entreprise
- **Checklist documents** avec statut (genere/disponible/manquant)

## Architecture de generation

```
generate_dossier_candidature (skill)
    |
    +-- Charge contexte (entreprise, fonds, intermediaire, scores)
    |
    +-- Determine documents requis (par fonds + par intermediaire)
    |
    +-- Pour chaque document requis :
    |       |
    |       +-- Si "generable" par la plateforme :
    |       |       |
    |       |       +-- Mode "complet" : genere avec donnees reelles
    |       |       +-- Mode "template" : genere structure vierge
    |       |       +-- Appel LLM pour contenu narratif
    |       |       +-- Produit DOCX + PDF
    |       |
    |       +-- Si "disponible" sur la plateforme :
    |       |       +-- Copie le fichier existant (rapport ESG, bilan carbone)
    |       |
    |       +-- Si "non generable" :
    |               +-- Ajoute a la liste "documents_manquants"
    |
    +-- Cree archive ZIP du dossier complet
    |
    +-- Retourne les URLs de telechargement
```

## Nouveaux templates de documents

### 1. Fiche Projet Vert

**Fichier :** `backend/app/documents/templates/fiche_projet.py`

**Contenu (2-3 pages) :**
- En-tete : nom entreprise + nom fonds + date
- Section 1 : Resume executif du projet (LLM)
- Section 2 : Contexte et problematique (LLM)
- Section 3 : Description du projet
  - Objectifs
  - Activites prevues
  - Zone geographique
  - Beneficiaires
- Section 4 : Impact environnemental et social attendu
  - Reduction CO2 estimee (si bilan carbone disponible)
  - Emplois crees/preserves
  - Contribution aux ODD
- Section 5 : Budget resume (tableau)
- Section 6 : Calendrier de mise en oeuvre (tableau)

### 2. Note d'Impact ESG Dediee

**Fichier :** `backend/app/documents/templates/note_impact_esg.py`

**Contenu (3-4 pages) :**
- Score ESG actuel avec graphique radar (E/S/G)
- Analyse par pilier avec points forts et axes d'amelioration
- Alignement avec le referentiel du fonds cible
- Plan d'amelioration ESG lie au projet finance
- Benchmarks sectoriels (comparaison)
- Indicateurs de suivi proposes

### 3. Page de Garde Dossier

**Fichier :** `backend/app/documents/templates/page_garde.py`

**Contenu (1 page) :**
- Titre : "Dossier de Candidature"
- Sous-titre : nom du fonds
- Nom de l'entreprise
- Nom de l'intermediaire
- Date de soumission
- Reference (auto-generee)
- Table des matieres du dossier
- Mention confidentialite

### 4. Checklist Documents

**Fichier :** `backend/app/documents/templates/checklist_documents.py`

**Contenu (1 page) :**
- Tableau avec tous les documents requis
- Colonne "Statut" : Inclus / A fournir / Non applicable
- Colonne "Page" : numero de page dans le dossier
- Notes par document

## Modifications du word_generator existant

### Fichier : `backend/app/documents/word_generator.py`

**Ajouts :**

1. **Parametre `fonds` et `intermediaire`** dans toutes les fonctions de generation
   - Adapte le contenu au fonds specifique
   - Mentionne l'intermediaire dans les en-tetes

2. **Mode `template_vierge`**
   - Meme structure que le mode complet
   - Champs a remplir marques avec `[A COMPLETER]`
   - Instructions en italique pour chaque section
   - Pas d'appel LLM (ou appel minimal pour la structure)

3. **Nouvelles fonctions :**
```python
async def build_fiche_projet(entreprise, fonds, intermediaire, scores, carbon, llm_callback, mode="complet") -> Document

async def build_note_impact_esg(entreprise, fonds, scores, action_plan, benchmarks, llm_callback, mode="complet") -> Document

async def build_page_garde(entreprise, fonds, intermediaire, documents_inclus) -> Document

async def build_checklist(fonds, intermediaire, documents_status) -> Document
```

4. **Prompts LLM adaptes par fonds :**
```python
PROMPTS_PAR_FONDS = {
    "GCF": {
        "lettre_motivation": "Redige une lettre de motivation pour le Green Climate Fund. "
                             "Mets l'accent sur l'impact climatique et l'alignement avec "
                             "les priorites du GCF (adaptation, attenuation). "
                             "Mentionne le passage par l'entite accreditee {intermediaire}.",
        "fiche_projet": "...",
    },
    "BOAD-PME": {
        "lettre_motivation": "Redige une lettre pour la Facilite Verte BOAD-PME. "
                             "Mets l'accent sur la dimension PME, le developpement "
                             "de l'espace UEMOA, et la conformite BCEAO.",
        "fiche_projet": "...",
    },
    # ... pour chaque fonds
}
```

## Generation du ZIP

### Fichier : `backend/app/documents/dossier_assembler.py` (nouveau)

```python
import zipfile
from pathlib import Path
from io import BytesIO

class DossierAssembler:
    """Assemble un dossier complet de candidature en ZIP."""

    def __init__(self, entreprise_nom: str, fonds_nom: str, intermediaire_nom: str):
        self.prefix = f"Dossier_{fonds_nom}_{intermediaire_nom}_{entreprise_nom}"
        self.documents: list[tuple[str, bytes]] = []

    def add_document(self, filename: str, content: bytes):
        """Ajoute un document au dossier."""
        self.documents.append((filename, content))

    def add_from_path(self, filename: str, filepath: Path):
        """Ajoute un fichier existant au dossier."""
        self.documents.append((filename, filepath.read_bytes()))

    def assemble(self) -> bytes:
        """Cree le ZIP final."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in self.documents:
                zf.writestr(f"{self.prefix}/{filename}", content)
        return buffer.getvalue()
```

## Nomenclature des fichiers generes

```
Dossier_GCF_BOAD_GreenEnergySARL/
    00_Page_Garde.pdf
    01_Checklist_Documents.pdf
    02_Lettre_Motivation.docx
    02_Lettre_Motivation.pdf
    03_Fiche_Projet.docx
    03_Fiche_Projet.pdf
    04_Plan_Affaires_Vert.docx
    04_Plan_Affaires_Vert.pdf
    05_Budget_Previsionnel.docx
    05_Budget_Previsionnel.pdf
    06_Note_Impact_ESG.pdf
    07_Rapport_ESG_Complet.pdf
    08_Bilan_Carbone.pdf
    09_Engagement_ESG.docx
    09_Engagement_ESG.pdf
    10_Plan_Action_ESG.pdf
```

## Stockage des dossiers generes

### Nouveau modele (optionnel mais recommande)

**Fichier :** `backend/app/models/dossier_candidature.py`

```python
class DossierCandidature(Base):
    __tablename__ = "dossiers_candidature"

    id: Mapped[str] = mapped_column(primary_key=True)
    entreprise_id: Mapped[str] = mapped_column(ForeignKey("entreprises.id"))
    fonds_id: Mapped[str] = mapped_column(ForeignKey("fonds_verts.id"))
    intermediaire_id: Mapped[str | None] = mapped_column(ForeignKey("intermediaires.id"))
    fund_application_id: Mapped[str | None] = mapped_column(ForeignKey("fund_applications.id"))

    type_dossier: Mapped[str]   # "complet" ou "template_vierge"
    documents_json: Mapped[list]  # Liste des documents generes avec chemins
    zip_path: Mapped[str | None]
    statut: Mapped[str]  # "genere", "en_revision", "finalise"

    created_at: Mapped[datetime]
```

### API de telechargement

```python
# Existant : GET /api/reports/download/{filename}
# Etendre pour supporter les ZIP :
# GET /api/reports/download/{filename}  (fonctionne deja pour .zip)

# Nouveau : GET /api/dossiers/{dossier_id}/documents
#   -> Liste les documents du dossier avec URLs de telechargement
```

## Integration avec le frontend

### Signal "Dossier genere" dans le chat

Quand le skill retourne les documents, le frontend affiche :

```vue
<!-- Nouveau composant : DossierGeneratedCard.vue -->
<div class="dossier-card">
  <h3>Dossier de candidature - {{ fonds_nom }}</h3>
  <p>Via {{ intermediaire_nom }}</p>

  <div v-for="doc in documents" class="doc-row">
    <span>{{ doc.nom }}</span>
    <div class="flex gap-2">
      <a :href="doc.url_docx" v-if="doc.url_docx">DOCX</a>
      <a :href="doc.url_pdf" v-if="doc.url_pdf">PDF</a>
    </div>
  </div>

  <a :href="zip_url" class="download-all-btn">
    Telecharger le dossier complet (ZIP)
  </a>
</div>
```

### Affichage dans le message du chat

Le composant `ChatMessage.vue` doit detecter les resultats de `generate_dossier_candidature` dans les `tool_calls_json` et afficher le `DossierGeneratedCard` au lieu du JSON brut.

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `backend/app/skills/handlers/generate_dossier_candidature.py` | Handler skill (~400 lignes) |
| `backend/app/documents/templates/fiche_projet.py` | Template fiche projet (~150 lignes) |
| `backend/app/documents/templates/note_impact_esg.py` | Template note impact (~200 lignes) |
| `backend/app/documents/templates/page_garde.py` | Template page de garde (~80 lignes) |
| `backend/app/documents/templates/checklist_documents.py` | Template checklist (~100 lignes) |
| `backend/app/documents/dossier_assembler.py` | Assemblage ZIP (~60 lignes) |
| `backend/app/models/dossier_candidature.py` | Modele DB optionnel |
| `frontend/src/components/chat/DossierGeneratedCard.vue` | Composant UI |
| `backend/migrations/versions/xxxx_create_dossiers_candidature.py` | Migration |

## Fichiers a modifier

| Fichier | Modification |
|---------|--------------|
| `backend/app/documents/word_generator.py` | Ajouter fonctions + prompts par fonds |
| `backend/app/skills/registry.py` | Importer le nouveau handler |
| `backend/app/seed/seed_skills.py` | Ajouter definition du skill |
| `frontend/src/components/chat/ChatMessage.vue` | Detecter et afficher DossierGeneratedCard |
| `backend/app/api/reports.py` | Support telechargement ZIP |

## Criteres de validation

- [ ] `generate_dossier_candidature` genere 5+ documents en un appel
- [ ] Mode "complet" : documents pre-remplis avec donnees entreprise
- [ ] Mode "template_vierge" : structure avec placeholders [A COMPLETER]
- [ ] ZIP contient tous les documents avec nomenclature correcte
- [ ] Prompts LLM adaptes par fonds (GCF != BOAD != BAD)
- [ ] Fiche projet contient graphique impact ESG
- [ ] Page de garde professionnelle avec infos correctes
- [ ] Checklist marque correctement genere/disponible/manquant
- [ ] Frontend affiche le composant DossierGeneratedCard dans le chat
- [ ] Telechargement ZIP fonctionnel depuis le chat
