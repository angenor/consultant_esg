# Extension Chrome ESG Advisor Guide

> **Fichier racine** — Ce document est le point d'entree. Il n'a aucune dependance.
> Les 3 fichiers Semaine suivants dependent de ce document.

## Progression globale du projet

- [ ] **Semaine 1** : Infrastructure, Auth & Popup → [Semaine1.md](./Semaine1.md)
  - [ ] Etape 1 : Initialisation du projet extension
  - [ ] Etape 2 : Types & constantes partages
  - [ ] Etape 3 : Client API & authentification
  - [ ] Etape 4 : Service Worker (background)
  - [ ] Etape 5 : Popup (interface principale)
  - [ ] Etape 6 : Nouveaux endpoints backend
  - [ ] Etape 7 : Seed des configurations de sites
- [ ] **Semaine 2** : Detection, Side Panel & Guide → [Semaine2.md](./Semaine2.md)
  - [ ] Etape 1 : Content script — detection de sites
  - [ ] Etape 2 : Content script — surlignage des champs
  - [ ] Etape 3 : Side Panel — guide pas-a-pas
  - [ ] Etape 4 : Integration content script ↔ side panel
- [ ] **Semaine 3** : Pre-remplissage, IA, Suivi & Polish → [Semaine3.md](./Semaine3.md)
  - [ ] Etape 1 : Pre-remplissage intelligent avance
  - [ ] Etape 2 : Suivi complet des candidatures
  - [ ] Etape 3 : Systeme d'alertes & notifications
  - [ ] Etape 4 : Internationalisation (FR/EN)
  - [ ] Etape 5 : Tests & debugging
  - [ ] Etape 6 : Preparation Chrome Web Store

---

## Vision

L'extension Chrome "ESG Advisor Guide" est le **pont entre la plateforme ESG Advisor et les sites de candidature des fonds verts**. Elle accompagne pas-a-pas les PME francophones africaines dans leurs demarches de candidature aux financements verts, directement depuis leur navigateur.

### Probleme resolu

Les PME abandonnent souvent leurs candidatures aux fonds verts a cause de :
- Formulaires complexes en anglais ou avec du jargon technique
- Manque de connaissance des documents requis
- Difficulte a traduire leurs donnees ESG dans le format attendu
- Perte de progression entre les sessions de travail

### Solution

Une extension Chrome qui :
1. **Detecte** quand l'utilisateur navigue sur un site de fonds vert reference
2. **Guide** pas-a-pas avec des instructions contextuelles
3. **Pre-remplit** les champs avec les donnees de la plateforme ESG Advisor
4. **Sauvegarde** la progression pour reprendre plus tard
5. **Assiste** via un chatbot IA contextuel

---

## Architecture Technique

### Stack Extension

```
Extension Chrome (Manifest V3)
├── popup/              → Mini-dashboard (auth, fonds suivis, statut)
│   ├── Popup.vue       → Composant principal
│   ├── LoginPanel.vue  → Connexion JWT
│   └── FundsList.vue   → Liste des candidatures en cours
│
├── sidepanel/          → Guide pas-a-pas (Chrome Side Panel API)
│   ├── SidePanel.vue   → Layout principal
│   ├── StepGuide.vue   → Etapes de candidature
│   ├── FieldHelper.vue → Aide contextuelle par champ
│   ├── DocChecklist.vue→ Liste des documents requis
│   └── MiniChat.vue    → Assistant IA contextuel
│
├── content/            → Scripts injectes dans les pages web
│   ├── detector.ts     → Detection de site de fonds
│   ├── highlighter.ts  → Surlignage des champs a remplir
│   ├── autofill.ts     → Suggestions de pre-remplissage
│   └── scraper.ts      → Extraction de structure de formulaire
│
├── background/         → Service Worker (Manifest V3)
│   ├── service-worker.ts → Orchestration principale
│   ├── api-client.ts   → Communication avec backend ESG Advisor
│   ├── auth.ts         → Gestion JWT (chrome.storage.session)
│   ├── sync.ts         → Synchronisation donnees plateforme
│   └── notifications.ts→ Alertes deadlines et progres
│
├── shared/             → Code partage
│   ├── types.ts        → Interfaces TypeScript
│   ├── constants.ts    → URLs, cles de storage, etc.
│   ├── fund-configs/   → Configurations par site de fonds
│   │   ├── boad.json   → Config BOAD (selecteurs CSS, etapes)
│   │   ├── bad.json    → Config BAD (Banque Africaine Dev.)
│   │   ├── gcf.json    → Config Green Climate Fund
│   │   ├── ifc.json    → Config IFC
│   │   └── index.ts    → Registry des configs
│   └── utils.ts        → Utilitaires communs
│
└── assets/             → Ressources statiques
    ├── icons/          → Icones extension (16, 32, 48, 128px)
    ├── styles/         → TailwindCSS (meme theme que la plateforme)
    └── locales/        → Traductions fr/en
```

### Communication avec le Backend

```
Extension Chrome ←→ Backend ESG Advisor API
                     │
                     ├── /api/auth/login          → Authentification JWT
                     ├── /api/auth/me             → Verification token
                     ├── /api/entreprises/         → Profil entreprise
                     ├── /api/entreprises/{id}/scores → Scores ESG
                     ├── /api/documents/entreprise/{id} → Documents disponibles
                     ├── /api/carbon/latest        → Empreinte carbone
                     ├── /api/credit-score/latest  → Score credit vert
                     ├── /api/action-plans/latest  → Plans d'action
                     │
                     ├── [NOUVEAU] /api/extension/fund-configs    → Configs des sites
                     ├── [NOUVEAU] /api/extension/applications    → Suivi candidatures
                     ├── [NOUVEAU] /api/extension/field-suggest   → Suggestions IA
                     └── [NOUVEAU] /api/extension/progress        → Sauvegarde progres
```

### Nouveaux Endpoints Backend (a creer)

```python
# backend/app/api/extension.py

# GET /api/extension/fund-configs
# → Retourne les configurations de sites de fonds (URLs, selecteurs CSS, etapes)
# → Permet la mise a jour sans republier l'extension

# POST /api/extension/applications
# → Cree/met a jour une candidature en cours
# → Body: { fonds_id, status, progress_pct, fields_filled, notes }

# GET /api/extension/applications
# → Liste les candidatures en cours de l'utilisateur

# POST /api/extension/field-suggest
# → Appelle le LLM pour suggerer le contenu d'un champ
# → Body: { fonds_id, field_name, field_label, field_context, entreprise_id }

# POST /api/extension/progress
# → Sauvegarde l'etat du formulaire (champs remplis, position)
# → Body: { application_id, form_data, current_step }
```

### Nouveaux Modeles de Donnees

```python
# backend/app/models/fund_application.py

class FundApplication(Base):
    """Suivi d'une candidature a un fonds vert"""
    __tablename__ = "fund_applications"

    id          = Column(UUID, primary_key=True, default=uuid4)
    entreprise_id = Column(UUID, ForeignKey("entreprises.id", ondelete="CASCADE"))
    fonds_id    = Column(UUID, ForeignKey("fonds_verts.id"), nullable=True)

    # Statut de candidature
    status      = Column(String(30), default="brouillon")
      # brouillon, en_cours, soumise, acceptee, refusee, abandonnee
    progress_pct = Column(Integer, default=0)

    # Donnees du formulaire sauvegardees
    form_data   = Column(JSONB, default={})
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=True)

    # Metadonnees
    url_candidature = Column(String(500), nullable=True)
    notes       = Column(Text, nullable=True)

    # Dates
    started_at  = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())


class FundSiteConfig(Base):
    """Configuration d'un site de fonds pour le guidage"""
    __tablename__ = "fund_site_configs"

    id          = Column(UUID, primary_key=True, default=uuid4)
    fonds_id    = Column(UUID, ForeignKey("fonds_verts.id", ondelete="CASCADE"))

    # Detection du site
    url_patterns = Column(JSONB, nullable=False)
      # ["https://www.boad.org/appel-*", "https://apply.boad.org/*"]

    # Etapes de candidature
    steps       = Column(JSONB, nullable=False)
      # [
      #   {
      #     "order": 1,
      #     "title": "Informations generales",
      #     "description": "Remplissez les informations de base sur votre entreprise",
      #     "url_pattern": "*/step-1*",
      #     "fields": [
      #       {
      #         "selector": "#company-name",
      #         "label": "Nom de l'entreprise",
      #         "source": "entreprise.nom",
      #         "help_text": "Le nom legal enregistre de votre entreprise"
      #       }
      #     ]
      #   }
      # ]

    # Documents requis
    required_docs = Column(JSONB, nullable=True)
      # [
      #   {
      #     "name": "Registre de commerce",
      #     "type": "legal",
      #     "format": "PDF",
      #     "platform_equivalent": "document.type_mime == 'application/pdf'"
      #   }
      # ]

    # Traductions et aide
    tips        = Column(JSONB, nullable=True)
    is_active   = Column(Boolean, default=True)
    version     = Column(Integer, default=1)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## Flux Utilisateur Principal

```
1. INSTALLATION & CONNEXION
   ┌─────────────────────────────────────┐
   │  L'utilisateur installe l'extension │
   │  depuis le Chrome Web Store         │
   └──────────────┬──────────────────────┘
                  ▼
   ┌─────────────────────────────────────┐
   │  Clic sur l'icone → Popup           │
   │  → Connexion avec ses identifiants  │
   │    ESG Advisor (email + mot de passe)│
   └──────────────┬──────────────────────┘
                  ▼
   ┌─────────────────────────────────────┐
   │  Synchronisation automatique :      │
   │  - Profil entreprise                │
   │  - Scores ESG                       │
   │  - Documents disponibles            │
   │  - Fonds recommandes                │
   └──────────────┬──────────────────────┘

2. NAVIGATION & DETECTION
                  ▼
   ┌─────────────────────────────────────┐
   │  L'utilisateur navigue sur le web   │
   │  → Content script detecte un site   │
   │    de fonds vert connu              │
   └──────────────┬──────────────────────┘
                  ▼
   ┌─────────────────────────────────────┐
   │  Badge notification sur l'icone :   │
   │  "Fonds BOAD detecte !              │
   │   Compatibilite: 78%               │
   │   Cliquez pour etre guide"          │
   └──────────────┬──────────────────────┘

3. GUIDAGE PAS-A-PAS
                  ▼
   ┌─────────────────────────────────────┐
   │  Side Panel s'ouvre avec :          │
   │  ┌───────────────────────────────┐  │
   │  │ BOAD - Facilite Verte PME    │  │
   │  │ Compatibilite: 78%           │  │
   │  │                              │  │
   │  │ Etape 1/5: Infos generales   │  │
   │  │ ■■■■□□□□□□ 20%              │  │
   │  │                              │  │
   │  │ ▸ Nom entreprise    [Auto]   │  │
   │  │ ▸ Secteur           [Auto]   │  │
   │  │ ▸ Pays              [Auto]   │  │
   │  │ ▸ Description       [IA]     │  │
   │  │                              │  │
   │  │ Documents requis:            │  │
   │  │ ✅ Registre commerce (pret)  │  │
   │  │ ✅ Bilan ESG (genere)       │  │
   │  │ ⬜ Business plan (manquant) │  │
   │  │                              │  │
   │  │ [💡 Demander a l'IA]         │  │
   │  └───────────────────────────────┘  │
   └──────────────┬──────────────────────┘

4. PRE-REMPLISSAGE & ASSISTANCE
                  ▼
   ┌─────────────────────────────────────┐
   │  Sur la page du formulaire :        │
   │  - Champs surlignés en vert (auto)  │
   │  - Champs surlignés en bleu (IA)    │
   │  - Tooltip avec suggestion au hover │
   │  - Bouton "Copier" a cote de chaque │
   │    suggestion                       │
   │  - Chat IA pour questions libres    │
   └──────────────┬──────────────────────┘

5. SUIVI & REPRISE
                  ▼
   ┌─────────────────────────────────────┐
   │  Sauvegarde automatique du progres  │
   │  → Reprise la ou on s'est arrete   │
   │  → Tableau de bord dans le popup   │
   │  → Alertes pour les deadlines      │
   └─────────────────────────────────────┘
```

---

## Phases d'Implementation

| Phase | Contenu | Duree estimee |
|-------|---------|---------------|
| **Semaine 1** | Infrastructure extension + Auth + Popup + Backend endpoints | 5 jours |
| **Semaine 2** | Detection de sites + Side Panel + Guide pas-a-pas | 5 jours |
| **Semaine 3** | Pre-remplissage + Assistant IA + Suivi candidatures + Polish | 5 jours |

---

## Contraintes Techniques

### Manifest V3 (obligatoire Chrome Web Store)
- **Service Worker** au lieu de background page persistante
- **chrome.storage.session** pour les tokens JWT (plus securise)
- **Content Security Policy** stricte (pas d'eval, pas d'inline scripts)
- **Permissions declaratives** : activeTab, storage, sidePanel, notifications

### Securite
- JWT stocke dans `chrome.storage.session` (efface a la fermeture du navigateur)
- Aucun credential en clair dans `chrome.storage.local`
- Communication backend via HTTPS uniquement en production
- Content scripts isoles (shadow DOM pour le UI injecte)

### Performance
- Bundle size minimal (< 500KB)
- Lazy loading des configs de fonds
- Cache local des donnees entreprise (TTL 5 minutes)
- Debounce sur la detection de pages

### Compatibilite Chrome Web Store
- Permissions minimales et justifiees
- Privacy policy obligatoire
- Description claire de l'utilisation des donnees
- Pas d'acces a toutes les URLs par defaut (activeTab uniquement)
