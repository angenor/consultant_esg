# Politique de Confidentialite — ESG Advisor Guide

**Derniere mise a jour : 15 fevrier 2026**

## Introduction

ESG Advisor Guide est une extension Chrome developpee par ESG Advisor AI pour aider les PME africaines francophones dans leurs candidatures aux fonds verts. Cette politique explique comment l'extension traite vos donnees.

## Donnees collectees

### Donnees d'authentification
- **Token JWT** : stocke en memoire de session Chrome (efface a la fermeture du navigateur)
- **Identifiants** : email et mot de passe transmis uniquement au serveur ESG Advisor pour l'authentification

### Donnees d'entreprise
- Les donnees de votre entreprise (nom, secteur, scores ESG, documents) sont recuperees depuis la plateforme ESG Advisor et mises en cache localement pendant 5 minutes pour ameliorer les performances
- Ces donnees sont celles que vous avez vous-meme saisies sur la plateforme ESG Advisor

### Donnees de navigation
- L'extension detecte uniquement les URLs correspondant aux sites de fonds verts configures (ex: BOAD, GCF, BAD)
- Aucun historique de navigation n'est collecte ni transmis

## Stockage des donnees

- **Token JWT** : `chrome.storage.session` (volatile, efface a la fermeture)
- **Donnees entreprise** : `chrome.storage.local` (cache local, TTL 5 minutes)
- **Configurations fonds** : `chrome.storage.local` (cache local, TTL 1 heure)

## Partage des donnees

- **Aucune donnee n'est partagee avec des tiers**
- L'extension communique exclusivement avec le serveur ESG Advisor (`https://api.esgadvisor.ai`)
- Aucune donnee n'est vendue, louee ou partagee a des fins publicitaires

## Permissions utilisees

| Permission | Justification |
|------------|---------------|
| `activeTab` | Acceder a l'onglet actif pour detecter les sites de fonds verts |
| `storage` | Stocker le token JWT et les donnees en cache |
| `sidePanel` | Afficher le guide pas-a-pas |
| `notifications` | Alertes de deadlines et rappels de candidatures |
| `alarms` | Verifications periodiques (authentification, synchronisation, deadlines) |

## Securite

- Toutes les communications utilisent HTTPS
- Les tokens JWT expirent apres 24 heures
- Les donnees en cache sont automatiquement invalidees

## Vos droits

Vous pouvez a tout moment :
- Vous deconnecter (efface toutes les donnees locales)
- Desinstaller l'extension (supprime toutes les donnees stockees)
- Supprimer votre compte sur la plateforme ESG Advisor

## Contact

Pour toute question relative a cette politique : **privacy@esgadvisor.ai**

---

# Privacy Policy — ESG Advisor Guide

**Last updated: February 15, 2026**

## Introduction

ESG Advisor Guide is a Chrome extension developed by ESG Advisor AI to help Francophone African SMEs with green fund applications. This policy explains how the extension handles your data.

## Data collected

### Authentication data
- **JWT token**: stored in Chrome session storage (cleared when browser closes)
- **Credentials**: email and password transmitted only to the ESG Advisor server for authentication

### Company data
- Your company data (name, sector, ESG scores, documents) is retrieved from the ESG Advisor platform and cached locally for 5 minutes to improve performance
- This data is what you have entered on the ESG Advisor platform

### Browsing data
- The extension only detects URLs matching configured green fund websites (e.g., BOAD, GCF, AfDB)
- No browsing history is collected or transmitted

## Data storage

- **JWT token**: `chrome.storage.session` (volatile, cleared on close)
- **Company data**: `chrome.storage.local` (local cache, 5-minute TTL)
- **Fund configurations**: `chrome.storage.local` (local cache, 1-hour TTL)

## Data sharing

- **No data is shared with third parties**
- The extension communicates exclusively with the ESG Advisor server (`https://api.esgadvisor.ai`)
- No data is sold, rented, or shared for advertising purposes

## Permissions used

| Permission | Justification |
|------------|---------------|
| `activeTab` | Access the active tab to detect green fund websites |
| `storage` | Store JWT token and cached data |
| `sidePanel` | Display the step-by-step guide |
| `notifications` | Deadline alerts and application reminders |
| `alarms` | Periodic checks (authentication, sync, deadlines) |

## Security

- All communications use HTTPS
- JWT tokens expire after 24 hours
- Cached data is automatically invalidated

## Your rights

You can at any time:
- Log out (clears all local data)
- Uninstall the extension (removes all stored data)
- Delete your account on the ESG Advisor platform

## Contact

For any questions about this policy: **privacy@esgadvisor.ai**
