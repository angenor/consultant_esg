# Phase 5 : Configurations extension pour tous les fonds

## Dependances

**Prerequis :** Phase 1 (table `intermediaires` doit exister pour lier chaque config a un intermediaire)
**Bloque :** Phase 6 (Interface suivi candidatures - l'extension doit pouvoir tracker la progression sur chaque site)

## Progression

- [ ] 5.1 Ajouter `intermediaire_id` au modele `FundSiteConfig` + migration Alembic
- [ ] 5.2 Explorer les sites des fonds avec agent-browser pour identifier formulaires et selecteurs CSS
- [ ] 5.3 Creer la config BEI-Proparco (direct) dans `fund_site_configs.json`
- [ ] 5.4 Creer la config GCF via BOAD (portail dedie) dans `fund_site_configs.json`
- [ ] 5.5 Creer les configs BAD, FIDA, SREP/CIF (appels a propositions / portails) dans `fund_site_configs.json`
- [ ] 5.6 Creer les configs banques partenaires (IFC/SGCI, SUNREF, BCEAO, FAGACE) dans `fund_site_configs.json`
- [ ] 5.7 Executer le seed et verifier les 10 configs actives en base
- [ ] 5.8 Tester la detection + auto-remplissage sur chaque site cible

## Objectif

Etendre les configurations `FundSiteConfig` de 1 fonds (BOAD) a 10 fonds. Chaque configuration definit les URL patterns, les etapes du formulaire, les champs a auto-remplir, et les documents requis pour que l'extension Chrome puisse guider l'utilisateur sur le site de chaque fonds ou intermediaire.

## Etat actuel

### Ce qui existe
- 1 FundSiteConfig pour BOAD-PME avec 5 etapes et 13 champs
- Modele FundSiteConfig complet (url_patterns, steps, fields, required_docs, tips)
- Infrastructure d'autofill (DataMapper, batch-autofill, field highlighting)
- Systeme de detection de fonds (FundDetector)
- Side panel de guide (StepNavigator, StepContent, FieldHelper)

### Ce qui manque
- 9 configurations pour les autres fonds/intermediaires
- Configs pour les sites des intermediaires (banques partenaires, etc.)
- Adaptation aux formulaires reels de chaque site

## Strategie de configuration

### Approche par priorite

Les fonds n'ont pas tous des formulaires en ligne. La configuration depend du `mode_acces` et du `type_soumission` des intermediaires.

**Priorite 1 : Fonds avec formulaires en ligne directs**
- BEI-Proparco (direct, portail)
- BOAD-PME (deja configure)

**Priorite 2 : Intermediaires avec formulaires en ligne**
- IFC via banques partenaires (portails bancaires)
- SUNREF via banques partenaires (portail SUNREF/AFD)
- FAGACE via banques (formulaires bancaires)
- BCEAO via banques commerciales UEMOA

**Priorite 3 : Fonds avec portails dedies**
- GCF via portail BOAD-GCF
- BAD (portail appels a propositions)
- SREP/CIF via portail Banque Mondiale

**Priorite 4 : Fonds sans formulaire en ligne**
- FIDA (soumission par email/dossier physique)

### Une config par site, pas par fonds

Important : on cree une `FundSiteConfig` par **site web** a remplir, pas par fonds. Un meme fonds peut avoir plusieurs configs si on passe par differents intermediaires.

Exemple pour IFC :
- Config 1 : Formulaire SGCI (Societe Generale CI) pour IFC
- Config 2 : Formulaire Ecobank pour IFC
- Config 3 : Portail IFC direct (si applicable)

## Nouvelles configurations

### Config 1 : BEI-Proparco (direct)

```json
{
  "fonds_code": "BEI-PROPARCO",
  "url_patterns": [
    "https://www.proparco.fr/fr/formulaire*",
    "https://www.proparco.fr/en/form*",
    "https://www.eib.org/*/apply*"
  ],
  "steps": [
    {
      "order": 1,
      "title": "Identification de l'entreprise",
      "description": "Informations generales sur votre entreprise",
      "fields": [
        {
          "selector": "input[name='company_name'], #company-name",
          "label": "Raison sociale",
          "source": "entreprise.nom",
          "type": "text",
          "required": true,
          "ai_suggest": false
        },
        {
          "selector": "select[name='country'], #country",
          "label": "Pays",
          "source": "entreprise.pays",
          "type": "select",
          "required": true,
          "ai_suggest": false
        },
        {
          "selector": "select[name='sector'], #sector",
          "label": "Secteur d'activite",
          "source": "entreprise.secteur",
          "type": "select",
          "required": true,
          "ai_suggest": false
        },
        {
          "selector": "textarea[name='project_description'], #project-desc",
          "label": "Description du projet",
          "source": null,
          "type": "textarea",
          "required": true,
          "ai_suggest": true,
          "help_text": "Decrivez le projet vert pour lequel vous sollicitez un financement"
        }
      ]
    },
    {
      "order": 2,
      "title": "Donnees financieres",
      "fields": [
        {
          "selector": "input[name='revenue'], #annual-revenue",
          "label": "Chiffre d'affaires annuel (EUR)",
          "source": "entreprise.chiffre_affaires|format_currency",
          "type": "number",
          "required": true,
          "ai_suggest": false
        },
        {
          "selector": "input[name='employees'], #employees",
          "label": "Nombre d'employes",
          "source": "entreprise.effectifs",
          "type": "number",
          "required": true,
          "ai_suggest": false
        },
        {
          "selector": "input[name='amount_requested'], #amount",
          "label": "Montant demande (EUR)",
          "source": null,
          "type": "number",
          "required": true,
          "ai_suggest": true,
          "help_text": "Entre 500 000 et 5 000 000 EUR"
        }
      ]
    },
    {
      "order": 3,
      "title": "Impact environnemental et social",
      "fields": [
        {
          "selector": "textarea[name='env_impact'], #environmental-impact",
          "label": "Impact environnemental attendu",
          "source": null,
          "type": "textarea",
          "required": true,
          "ai_suggest": true,
          "help_text": "Reduction CO2, efficacite energetique, preservation biodiversite"
        },
        {
          "selector": "textarea[name='social_impact'], #social-impact",
          "label": "Impact social attendu",
          "source": null,
          "type": "textarea",
          "required": true,
          "ai_suggest": true,
          "help_text": "Emplois crees, communautes beneficiaires, egalite des genres"
        }
      ]
    },
    {
      "order": 4,
      "title": "Documents",
      "fields": [
        {
          "selector": "input[type='file'][name='business_plan']",
          "label": "Plan d'affaires vert",
          "type": "file",
          "required": true,
          "ai_suggest": false,
          "help_text": "PDF, max 10 Mo"
        },
        {
          "selector": "input[type='file'][name='financials']",
          "label": "Etats financiers (3 ans)",
          "type": "file",
          "required": true,
          "ai_suggest": false
        }
      ]
    },
    {
      "order": 5,
      "title": "Validation et soumission",
      "description": "Verifiez vos informations avant de soumettre",
      "fields": []
    }
  ],
  "required_docs": [
    {
      "name": "Plan d'affaires vert",
      "type": "plan_affaires",
      "format": "PDF",
      "description": "Plan d'affaires avec volet vert detaille",
      "available_on_platform": true,
      "document_id": null
    },
    {
      "name": "Etats financiers (3 derniers exercices)",
      "type": "etats_financiers",
      "format": "PDF",
      "description": "Bilans, comptes de resultat certifies",
      "available_on_platform": false,
      "document_id": null
    },
    {
      "name": "Note d'impact ESG",
      "type": "note_impact_esg",
      "format": "PDF",
      "description": "Evaluation de l'impact environnemental et social",
      "available_on_platform": true,
      "document_id": null
    }
  ],
  "tips": {
    "general": "BEI-Proparco privilegie les projets d'energie renouvelable et d'efficacite energetique. Mettez en avant les indicateurs quantitatifs d'impact.",
    "amount": "Le ticket moyen est de 1-3M EUR. Les projets < 500K EUR sont rarement finances.",
    "timeline": "Delai moyen de traitement : 2-4 mois apres soumission complete."
  }
}
```

### Configs 2-9 : Autres fonds

Pour chaque fonds/intermediaire, creer une configuration similaire avec :
- URL patterns reels (recherche necessaire pour chaque site)
- Champs adaptes au formulaire reel du site
- Documents requis specifiques

**Note importante :** Les URL patterns et selecteurs CSS devront etre valides et verifies sur les sites reels. Certains sites peuvent changer leurs formulaires. Un systeme de versioning est prevu (`version` dans FundSiteConfig).

### Config GCF via BOAD

```json
{
  "fonds_code": "GCF",
  "intermediaire": "BOAD",
  "url_patterns": [
    "https://www.boad.org/fr/gcf*",
    "https://www.boad.org/fr/fonds-vert-climat*"
  ],
  "steps": [
    {
      "order": 1,
      "title": "Concept Note",
      "description": "Soumission de la note conceptuelle au GCF via la BOAD",
      "fields": [...]
    },
    {
      "order": 2,
      "title": "Informations sur l'entite executrice",
      "fields": [...]
    },
    {
      "order": 3,
      "title": "Description du projet climat",
      "fields": [...]
    },
    {
      "order": 4,
      "title": "Budget et plan de financement",
      "fields": [...]
    },
    {
      "order": 5,
      "title": "Indicateurs de performance",
      "fields": [...]
    },
    {
      "order": 6,
      "title": "Sauvegardes environnementales et sociales",
      "fields": [...]
    },
    {
      "order": 7,
      "title": "Documents et soumission",
      "fields": [...]
    }
  ]
}
```

### Config BAD (Appels a propositions)

```json
{
  "fonds_code": "BAD",
  "url_patterns": [
    "https://www.afdb.org/*/apply*",
    "https://www.afdb.org/*/proposals*",
    "https://procurement.afdb.org/*"
  ],
  "steps": [...]
}
```

### Configs Banques Partenaires (IFC, SUNREF, BCEAO, FAGACE)

Pour les fonds passant par des banques partenaires, les configs ciblent les portails bancaires :

```json
{
  "fonds_code": "IFC",
  "intermediaire": "SGCI",
  "url_patterns": [
    "https://www.societegenerale.ci/*/financement*",
    "https://www.societegenerale.ci/*/credit-vert*"
  ],
  "steps": [
    {
      "order": 1,
      "title": "Demande de credit vert",
      "description": "Formulaire de demande de financement vert via SGCI",
      "fields": [...]
    }
  ]
}
```

## Mise a jour du seed

**Fichier :** `data/fund_site_configs.json`

Ajouter les 9 nouvelles configurations (actuellement 1 seule pour BOAD-PME).

**Fichier :** `backend/app/seed/seed_fund_configs.py`

Le script existant devrait fonctionner si on respecte le format.

## Lien intermediaire -> config

### Modification du modele FundSiteConfig

Ajouter une reference optionnelle a l'intermediaire :

```python
# Dans fund_application.py ou nouveau fichier
intermediaire_id: Mapped[str | None] = mapped_column(
    ForeignKey("intermediaires.id", ondelete="SET NULL"),
    nullable=True
)
```

Cela permet de savoir quel intermediaire est concerne par chaque config.

### Migration Alembic

```python
op.add_column('fund_site_configs', sa.Column(
    'intermediaire_id', sa.String(36),
    sa.ForeignKey('intermediaires.id', ondelete='SET NULL'),
    nullable=True
))
```

## Recherche URLs reelles

Pour chaque fonds, il faut verifier les URLs reelles des formulaires :

| Fonds | Site | URL formulaire | Statut |
|-------|------|----------------|--------|
| BOAD-PME | boad.org | /fr/candidature | Configure |
| BEI-Proparco | proparco.fr | /fr/formulaire | A verifier |
| GCF via BOAD | boad.org | /fr/gcf | A verifier |
| BAD | afdb.org | Portail procurement | A verifier |
| IFC via SGCI | societegenerale.ci | Espace entreprises | A verifier |
| SUNREF via banque | sunref.org | Portail partenaire | A verifier |
| FAGACE | Site banque locale | Formulaire credit | A verifier |
| BCEAO via banque | Site banque UEMOA | Formulaire credit vert | A verifier |
| FIDA | fida.org | Email/portail | A verifier |
| SREP/CIF | climateinvestmentfunds.org | Portail | A verifier |

**Action requise :** Navigation manuelle sur chaque site pour identifier les formulaires exacts et leurs selecteurs CSS. Utiliser `agent-browser` pour l'exploration.

## Processus de creation des configs

Pour chaque fonds/intermediaire :

1. **Explorer le site** avec agent-browser
2. **Identifier le formulaire** de candidature/soumission
3. **Mapper les champs** : selecteur CSS, label, type, source
4. **Tester l'auto-remplissage** en local
5. **Documenter les particularites** (captcha, auth requise, etc.)
6. **Creer la config JSON** dans `fund_site_configs.json`

## Gestion du versioning

Quand un site change son formulaire :

1. Incrementer `version` dans la config
2. Mettre a jour les selecteurs CSS
3. Les utilisateurs recoivent la mise a jour via le cache 1h du service worker
4. Les candidatures en cours restent fonctionnelles (form_data sauvegarde)

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| Aucun nouveau fichier de code | Tout est de la configuration JSON |

## Fichiers a modifier

| Fichier | Modification |
|---------|--------------|
| `data/fund_site_configs.json` | Ajouter 9 configurations |
| `backend/app/models/fund_application.py` | Ajouter intermediaire_id a FundSiteConfig |
| `backend/migrations/versions/xxxx_add_intermediaire_to_configs.py` | Migration |
| `chrome-extension/src/content/detector.ts` | Tester avec les nouvelles URL patterns |

## Criteres de validation

- [ ] 10 FundSiteConfig actives en base (1 existante + 9 nouvelles)
- [ ] Chaque config a des URL patterns valides et verifies
- [ ] Au moins les champs basiques (nom, pays, secteur, montant) mappes par config
- [ ] Les champs AI-suggest fonctionnent sur chaque config
- [ ] Le side panel guide fonctionne sur chaque site cible
- [ ] L'auto-remplissage fonctionne sur les formulaires reels
- [ ] Le lien intermediaire_id est correct pour chaque config
- [ ] Le versioning est a 1 pour toutes les nouvelles configs
