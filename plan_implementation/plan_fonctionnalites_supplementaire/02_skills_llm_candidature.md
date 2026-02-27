# Phase 2 : Skills LLM pour candidature guidee

## Dependances

**Prerequis :** Phase 1 (table `intermediaires` doit exister pour que les skills puissent la requeter)
**Bloque :** Phase 4 (Sync plateforme-extension - necessite que `guide_candidature` retourne des `extension_action`)

## Progression

- [x] 2.1 Creer le handler `backend/app/skills/handlers/guide_candidature.py` (4 actions : analyser, lister_intermediaires, preparer_dossier, lancer_soumission)
- [x] 2.2 Creer le handler `backend/app/skills/handlers/generate_dossier_candidature.py`
- [x] 2.3 Creer le handler `backend/app/skills/handlers/get_intermediaires.py`
- [x] 2.4 Enregistrer les 3 handlers dans `backend/app/skills/registry.py`
- [x] 2.5 Ajouter les 3 definitions de skills dans `backend/app/seed/seed_skills.py`
- [x] 2.6 Mettre a jour le system prompt (`backend/app/agent/prompt_builder.py`) avec les regles de candidature
- [x] 2.7 Enrichir `search_green_funds` avec `nb_intermediaires` et `candidature_directe`
- [x] 2.8 Enrichir `simulate_funding` avec `intermediaires_recommandes` et `prochaine_action`
- [ ] 2.9 Tester : "comment postuler au GCF" -> mentionne entite accreditee + intermediaires filtres par pays

## Objectif

Creer les skills qui permettent au LLM de guider l'utilisateur dans le processus de candidature, depuis la decision de postuler jusqu'a la soumission effective. Le LLM doit pouvoir :

1. Identifier le mode d'acces et les intermediaires adaptes au pays de l'entreprise
2. Proposer les formulaires en ligne ou la preparation de dossiers
3. Declencher l'ouverture de l'extension Chrome sur le bon site
4. Orchestrer la generation de documents

## Nouveaux skills

### Skill 1 : `guide_candidature`

**Objectif :** Skill principal d'orchestration. Quand l'utilisateur dit "je veux postuler au GCF" ou "aide-moi a candidater", ce skill analyse la situation et propose le bon parcours.

**Input schema :**
```json
{
  "type": "object",
  "properties": {
    "entreprise_id": {"type": "string"},
    "fonds_id": {"type": "string", "description": "ID du fonds cible"},
    "fonds_nom": {"type": "string", "description": "Nom du fonds (si ID inconnu)"},
    "action": {
      "type": "string",
      "enum": ["analyser", "lister_intermediaires", "preparer_dossier", "lancer_soumission"],
      "default": "analyser"
    }
  },
  "required": ["entreprise_id"]
}
```

**Handler :** `backend/app/skills/handlers/guide_candidature.py`

**Logique par action :**

#### Action `analyser` (defaut)
1. Charger le fonds (par ID ou recherche par nom)
2. Charger l'entreprise et son dernier score ESG
3. Verifier l'eligibilite de base (pays, secteur, score)
4. Analyser le `mode_acces` du fonds
5. Retourner :
```json
{
  "fonds": { "nom", "institution", "mode_acces", "mode_acces_label" },
  "eligible": true/false,
  "criteres_manquants": [...],
  "mode_acces_explique": "Pour acceder au GCF, vous devez passer par...",
  "intermediaires_disponibles": [
    {
      "nom": "BOAD",
      "type": "entite_accreditee",
      "pays": "regional",
      "type_soumission": "portail_dedie",
      "url_formulaire": "https://...",
      "est_recommande": true,
      "delai": "6-18 mois"
    }
  ],
  "etapes_processus": [...],
  "documents_necessaires": [...],
  "candidature_directe_possible": false,
  "formulaire_en_ligne_disponible": true,
  "actions_proposees": [
    {"action": "preparer_dossier", "label": "Preparer le dossier de candidature"},
    {"action": "lancer_soumission", "label": "Ouvrir le formulaire en ligne"}
  ]
}
```

#### Action `lister_intermediaires`
1. Charger les intermediaires du fonds filtres par pays de l'entreprise
2. Trier par `est_recommande` DESC, puis par delai
3. Retourner la liste avec contacts et types de soumission

#### Action `preparer_dossier`
1. Identifier les documents requis (par le fonds ET par l'intermediaire)
2. Verifier quels documents l'entreprise a deja uploade sur la plateforme
3. Retourner :
```json
{
  "documents_requis": [
    {"nom": "Plan d'affaires vert", "statut": "a_generer", "skill": "generate_document", "type": "plan_affaires"},
    {"nom": "Lettre de motivation", "statut": "a_generer", "skill": "generate_document", "type": "lettre_motivation"},
    {"nom": "Etats financiers", "statut": "manquant", "note": "A fournir par l'entreprise"},
    {"nom": "Score ESG", "statut": "disponible", "skill": "assemble_pdf", "template": "esg_full"},
    {"nom": "Bilan carbone", "statut": "disponible", "skill": "assemble_pdf", "template": "carbon"}
  ],
  "dossier_complet_possible": true,
  "action_generer_tout": "generate_dossier_candidature"
}
```

#### Action `lancer_soumission`
1. Determiner le type de soumission (formulaire en ligne, email, physique)
2. Si formulaire en ligne :
   - Retourner l'URL + un signal pour l'extension Chrome
   - Le frontend enverra un message a l'extension via `window.postMessage`
3. Si email :
   - Retourner l'adresse email + les pieces jointes a envoyer
4. Si physique :
   - Retourner l'adresse postale + la checklist de documents

```json
{
  "type_soumission": "formulaire_en_ligne",
  "url": "https://www.boad.org/fr/candidature",
  "extension_action": {
    "type": "OPEN_FUND_APPLICATION",
    "fonds_id": "...",
    "url": "https://www.boad.org/fr/candidature",
    "intermediaire_id": "..."
  },
  "instructions": "L'extension Chrome va vous guider...",
  "documents_a_joindre": [...]
}
```

### Skill 2 : `generate_dossier_candidature`

**Objectif :** Generer un dossier complet de candidature pour un fonds specifique via un intermediaire. Produit tous les documents necessaires en un seul appel.

**Input schema :**
```json
{
  "type": "object",
  "properties": {
    "entreprise_id": {"type": "string"},
    "fonds_id": {"type": "string"},
    "intermediaire_id": {"type": "string"},
    "format": {"type": "string", "enum": ["word", "pdf", "both"], "default": "both"},
    "type_dossier": {
      "type": "string",
      "enum": ["complet", "template_vierge"],
      "default": "complet",
      "description": "complet = pre-rempli avec donnees entreprise, template_vierge = structure a remplir"
    },
    "documents": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Liste des documents a generer. Si vide, genere tous les documents requis."
    },
    "instructions": {
      "type": "string",
      "description": "Instructions specifiques de l'utilisateur pour la generation"
    }
  },
  "required": ["entreprise_id", "fonds_id"]
}
```

**Handler :** `backend/app/skills/handlers/generate_dossier_candidature.py`

**Documents generables :**

| Document | Format | Contenu |
|----------|--------|---------|
| lettre_motivation | DOCX + PDF | Adaptee au fonds et intermediaire |
| fiche_projet | DOCX + PDF | Resume du projet vert |
| plan_affaires_vert | DOCX + PDF | Business plan oriente ESG |
| budget_previsionnel | DOCX + PDF | Budget avec volet vert |
| note_impact_esg | DOCX + PDF | Analyse d'impact ESG detaillee |
| rapport_esg_complet | PDF | Rapport ESG de la plateforme |
| bilan_carbone | PDF | Bilan carbone de la plateforme |
| engagement_esg | DOCX + PDF | Lettre d'engagement ESG |
| plan_action_esg | PDF | Plan d'action ESG en cours |
| page_garde | DOCX + PDF | Page de garde du dossier |

**Retour :**
```json
{
  "dossier_id": "uuid",
  "fonds": "Green Climate Fund",
  "intermediaire": "BOAD",
  "documents_generes": [
    {
      "type": "lettre_motivation",
      "nom": "Lettre_Motivation_GCF_BOAD_GreenEnergySARL.docx",
      "format": "docx",
      "taille": 45678,
      "url_telechargement": "/api/reports/download/..."
    },
    {
      "type": "lettre_motivation",
      "nom": "Lettre_Motivation_GCF_BOAD_GreenEnergySARL.pdf",
      "format": "pdf",
      "taille": 67890,
      "url_telechargement": "/api/reports/download/..."
    }
  ],
  "documents_manquants": [
    {"nom": "Etats financiers", "note": "A fournir par l'entreprise (non generable automatiquement)"}
  ],
  "zip_url": "/api/reports/download/Dossier_GCF_BOAD_GreenEnergySARL.zip",
  "prochaine_etape": "Telecharger le dossier et le soumettre via le portail BOAD"
}
```

### Skill 3 : `get_intermediaires`

**Objectif :** Skill simple pour lister les intermediaires d'un fonds, filtrables par pays.

**Input schema :**
```json
{
  "type": "object",
  "properties": {
    "fonds_id": {"type": "string"},
    "pays": {"type": "string"},
    "type": {"type": "string", "enum": ["banque_partenaire", "entite_accreditee", "agence_nationale", "bmd"]}
  },
  "required": ["fonds_id"]
}
```

**Retour :** Liste d'intermediaires avec contacts et instructions.

## Mise a jour des skills existants

### `search_green_funds` - Ajouter `nb_intermediaires`

```python
# Dans le retour de chaque fonds, ajouter :
"nb_intermediaires": len(await _count_intermediaires(db, fonds.id, pays)),
"candidature_directe": fonds.mode_acces == "direct",
```

### `simulate_funding` - Ajouter section intermediaires

Dans le retour, ajouter :
```python
"intermediaires_recommandes": [
    {"nom": i.nom, "type": i.type, "delai": i.delai_traitement}
    for i in intermediaires[:3]
],
"prochaine_action": "guide_candidature" if eligible else "manage_action_plan",
```

## Mise a jour du system prompt

**Fichier :** `backend/app/agent/prompt_builder.py`

Ajouter dans la section des regles d'utilisation des skills :

```
## Candidature aux fonds verts

Quand l'utilisateur veut postuler a un fonds vert :
1. Utilise d'abord `guide_candidature` avec action="analyser" pour comprendre le processus
2. Si le mode d'acces n'est PAS "direct", explique clairement quel intermediaire contacter
3. Propose de generer les documents avec `generate_dossier_candidature`
4. Si un formulaire en ligne est disponible, propose d'ouvrir le site et d'utiliser l'extension Chrome
5. JAMAIS dire "candidature directe" si le mode_acces != "direct"

Quand l'utilisateur demande "comment postuler" ou "aide-moi a candidater" :
- Utilise `guide_candidature` avec l'action appropriee
- Presente les intermediaires filtres par le pays de l'entreprise
- Mets en avant l'intermediaire recommande (est_recommande=true)

Pour les dossiers :
- Propose d'abord un dossier "complet" (pre-rempli avec les donnees de l'entreprise)
- Mentionne l'option "template_vierge" si l'utilisateur prefere remplir lui-meme
- Genere en format "both" (Word + PDF) par defaut
```

## Seed des skills dans la base

**Fichier :** `backend/app/seed/seed_skills.py`

Ajouter les 3 nouvelles definitions de skills :

```python
{
    "nom": "guide_candidature",
    "description": "Guide l'utilisateur dans le processus de candidature a un fonds vert. "
                   "Analyse le mode d'acces, identifie les intermediaires, et propose les "
                   "prochaines etapes (preparation de dossier, formulaire en ligne, etc.).",
    "category": "finance",
    "input_schema": { ... },
    "handler_key": "builtin.guide_candidature",
},
{
    "nom": "generate_dossier_candidature",
    "description": "Genere un dossier complet de candidature pour un fonds vert. "
                   "Produit les documents necessaires (lettre de motivation, plan d'affaires, "
                   "note d'impact, etc.) en Word et PDF, adaptes au fonds et a l'intermediaire.",
    "category": "document",
    "input_schema": { ... },
    "handler_key": "builtin.generate_dossier_candidature",
},
{
    "nom": "get_intermediaires",
    "description": "Liste les intermediaires disponibles pour un fonds vert, "
                   "filtres par pays et type. Retourne les contacts, URLs de formulaires, "
                   "et instructions de soumission.",
    "category": "finance",
    "input_schema": { ... },
    "handler_key": "builtin.get_intermediaires",
}
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `backend/app/skills/handlers/guide_candidature.py` | Handler principal (~300 lignes) |
| `backend/app/skills/handlers/generate_dossier_candidature.py` | Generation dossier complet (~400 lignes) |
| `backend/app/skills/handlers/get_intermediaires.py` | Liste intermediaires (~80 lignes) |

## Fichiers a modifier

| Fichier | Modification |
|---------|--------------|
| `backend/app/skills/registry.py` | Ajouter imports des 3 handlers |
| `backend/app/seed/seed_skills.py` | Ajouter 3 definitions de skills |
| `backend/app/agent/prompt_builder.py` | Ajouter regles candidature |
| `backend/app/skills/handlers/search_green_funds.py` | Ajouter nb_intermediaires |
| `backend/app/skills/handlers/simulate_funding.py` | Ajouter intermediaires recommandes |

## Flux utilisateur type

```
Utilisateur: "Je veux postuler au fonds GCF"
    |
    v
LLM appelle guide_candidature(fonds_nom="GCF", action="analyser")
    |
    v
Retour: mode_acces=entite_accreditee, intermediaires=[BOAD, CSE, AND-CI]
    |
    v
LLM: "Le GCF ne permet pas la candidature directe. Vous devez passer
      par une Entite Nationale Accreditee. Pour la Cote d'Ivoire, je
      recommande la BOAD (entite regionale). Voici les etapes :
      1. Obtenir la lettre de non-objection de l'AND
      2. Soumettre via le portail BOAD-GCF
      Voulez-vous que je prepare le dossier ?"
    |
    v
Utilisateur: "Oui, prepare le dossier"
    |
    v
LLM appelle generate_dossier_candidature(fonds_id=..., intermediaire_id=...)
    |
    v
Retour: 6 documents generes (Word+PDF), zip disponible
    |
    v
LLM: "J'ai genere votre dossier complet :
      - Lettre de motivation (Word + PDF)
      - Fiche projet (Word + PDF)
      - Note d'impact ESG (PDF)
      [Telecharger le dossier ZIP]
      La BOAD a un formulaire en ligne. Voulez-vous l'ouvrir ?"
    |
    v
Utilisateur: "Oui, ouvre le formulaire"
    |
    v
LLM appelle guide_candidature(action="lancer_soumission")
    |
    v
Frontend recoit extension_action -> envoie message a l'extension Chrome
    |
    v
Extension Chrome ouvre le side panel avec le guide BOAD
```

## Criteres de validation

- [ ] Skill `guide_candidature` fonctionnel avec les 4 actions
- [ ] Skill `generate_dossier_candidature` genere Word + PDF + ZIP
- [ ] Skill `get_intermediaires` retourne les intermediaires filtres
- [ ] System prompt mis a jour avec regles de candidature
- [ ] `search_green_funds` enrichi avec nb_intermediaires
- [ ] `simulate_funding` enrichi avec intermediaires recommandes
- [ ] Test : "comment postuler au GCF" -> mentionne entite accreditee
- [ ] Test : "prepare mon dossier pour la BOAD" -> genere documents
- [ ] Test : "ouvre le formulaire" -> retourne extension_action
