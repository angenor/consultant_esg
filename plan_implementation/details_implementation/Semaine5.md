# Semaine 5 — Admin + Support Vocal + Polish + Déploiement

> **Objectif** : Finaliser le produit — interface admin complète, support vocal, données réalistes, polish UX, tests, vidéo pitch, et déploiement de la démo.

> **Prérequis** : Semaine 4 terminée (toutes les fonctionnalités métier + vues frontend en place)

---

## Étape 26 — Admin CRUD Skills (API + Frontend)

**Fichiers concernés** : [07_admin_skills.md](../07_admin_skills.md) · [05_api_endpoints.md](../05_api_endpoints.md#admin---skills)

### À faire

- [x] 26.1 Compléter `backend/app/api/admin/skills.py` (si pas déjà fait)
  - `GET /api/admin/skills/` — lister tous les skills (filtrable par catégorie, statut)
  - `POST /api/admin/skills/` — créer un skill custom (valide le code Python)
  - `GET /api/admin/skills/{id}` — détail
  - `PUT /api/admin/skills/{id}` — modifier (incrémente version)
  - `DELETE /api/admin/skills/{id}` — supprimer (seulement custom, pas builtin)
  - `POST /api/admin/skills/{id}/toggle` — activer/désactiver
  - `POST /api/admin/skills/{id}/test` — tester avec des params fictifs
  - Code dans [05_api_endpoints.md](../05_api_endpoints.md#admin---skills)

- [x] 26.2 Créer `src/views/admin/SkillsListView.vue`
  - Tableau des skills avec filtres (catégorie, statut)
  - Badges : builtin vs custom, actif/inactif
  - Actions : modifier, désactiver, supprimer (custom uniquement), tester
  - Bouton "Nouveau Skill"
  - Maquette dans [07_admin_skills.md](../07_admin_skills.md#interface-admin---liste-des-skills)

- [x] 26.3 Créer `src/views/admin/SkillEditView.vue`
  - Formulaire complet : nom, description, catégorie, input_schema, code Python
  - Intègre les composants admin ci-dessous

- [x] 26.4 Créer les composants admin skills
  - [x] `components/admin/SkillForm.vue` — formulaire principal, code dans [07_admin_skills.md](../07_admin_skills.md#composant-vuejs---skillform)
  - [x] `components/admin/SkillCodeEditor.vue` — éditeur code (textarea thème sombre, support Tab)
    - Note : utilise un textarea stylisé au lieu de CodeMirror (plus léger pour le MVP)
  - [x] `components/admin/SkillTestPanel.vue` — zone de test avec params JSON + résultat
  - [x] `components/admin/SchemaBuilder.vue` — builder visuel de JSON Schema (mode visuel optionnel)

- [x] 26.5 Créer `src/stores/admin.ts` — Pinia store admin
  - Actions : `loadSkills()`, `createSkill()`, `updateSkill()`, `deleteSkill()`, `toggleSkill()`, `testSkill()`

- [x] 26.6 Tester le workflow admin complet
  - 10 tests API passés (LIST, CREATE, GET, UPDATE, TOGGLE, TEST, DELETE, protection builtin, filtrage, validation code)
  - Frontend type-check OK (vue-tsc --noEmit)

### Comment

1. L'éditeur de code Python est le composant le plus complexe — utiliser CodeMirror 6
2. Le mode visuel du JSON Schema est optionnel (le mode JSON brut suffit pour le MVP)
3. Le test de skill est critique : l'admin doit pouvoir vérifier avant de mettre en production

---

## Étape 27 — Admin CRUD Référentiels ESG

**Fichiers concernés** : [07_admin_skills.md](../07_admin_skills.md#administration-des-référentiels-esg) · [05_api_endpoints.md](../05_api_endpoints.md#admin---référentiels-esg)

### À faire

- [x] 27.1 Compléter `backend/app/api/admin/referentiels.py`
  - `GET /api/admin/referentiels/` — lister (filtrable par région, statut)
  - `POST /api/admin/referentiels/` — créer (valide la grille)
  - `GET /api/admin/referentiels/{id}` — détail avec grille + fonds liés
  - `PUT /api/admin/referentiels/{id}` — modifier (valide la grille si modifiée)
  - `DELETE /api/admin/referentiels/{id}` — supprimer
  - `POST /api/admin/referentiels/{id}/toggle` — activer/désactiver
  - `POST /api/admin/referentiels/{id}/preview` — simuler un scoring avec données test
  - Validation de la grille : `validate_grille()` dans [05_api_endpoints.md](../05_api_endpoints.md#admin---référentiels-esg)

- [x] 27.2 Compléter `backend/app/api/admin/fonds.py`
  - CRUD fonds verts avec association au référentiel
  - `POST /api/admin/fonds/` — créer un fonds (+ `referentiel_id`)
  - `PUT /api/admin/fonds/{id}` — modifier
  - `DELETE /api/admin/fonds/{id}` — supprimer

- [x] 27.3 Compléter `backend/app/api/admin/templates.py`
  - CRUD templates de rapports

- [x] 27.4 Créer `src/views/admin/ReferentielsListView.vue`
  - Tableau des référentiels avec : institution, région, poids E/S/G, méthode, nb critères, fonds liés
  - Actions : modifier, simuler, désactiver
  - Maquette dans [07_admin_skills.md](../07_admin_skills.md#interface-admin---liste-des-référentiels)

- [x] 27.5 Créer `src/views/admin/ReferentielEditView.vue`
  - Formulaire : nom, code, institution, région, description, méthode agrégation
  - Éditeur de grille ESG intégré

- [x] 27.6 Créer les composants admin référentiels
  - [x] `components/admin/ReferentielForm.vue` — formulaire principal
  - [x] `components/admin/GrilleEditor.vue` — éditeur visuel de grille ESG
    - Piliers avec poids global (slider ou input)
    - Pour chaque pilier : liste de critères (ajout/suppression)
    - Pour chaque critère : ID, label, poids, type (quantitatif/qualitatif), seuils ou options, question de collecte
    - Validation en temps réel : somme des poids = 1.00
    - Maquette dans [07_admin_skills.md](../07_admin_skills.md#interface-admin---éditeur-de-grille-esg)
  - [x] `components/admin/ScoringSimulator.vue` — tester le scoring avec données fictives
    - Input JSON des réponses aux critères
    - Affiche le résultat : scores par pilier + global + détail critères

- [x] 27.7 Créer les vues admin fonds + templates
  - [x] `src/views/admin/FondsListView.vue` — liste fonds verts
  - [x] `src/views/admin/FondEditView.vue` — formulaire fonds (avec sélecteur référentiel)
  - [x] `src/views/admin/TemplatesListView.vue` — liste templates rapports

- [x] 27.8 Créer `src/views/admin/AdminLayout.vue`
  - Navigation admin : Skills, Référentiels, Fonds, Templates, Stats
  - Layout avec sidebar admin

- [x] 27.9 Créer `backend/app/api/admin/stats.py`
  - `GET /api/admin/stats/dashboard` — statistiques globales
  - Nombre d'utilisateurs, d'entreprises, de conversations, de scores calculés, de rapports générés

- [x] 27.10 Créer `src/views/admin/StatsView.vue`
  - Dashboard admin avec compteurs et graphiques d'usage

### Comment

1. L'éditeur de grille (`GrilleEditor.vue`) est le composant le plus complexe de l'admin
2. Il gère des listes dynamiques (piliers → critères) avec validation croisée (somme poids)
3. Le simulateur permet de vérifier en live qu'une grille produit des scores cohérents
4. Le lien fonds → référentiel est un simple sélecteur dropdown

---

## Étape 28 — Support vocal : AudioRecordButton + API /audio + STT

**Fichiers concernés** : [01_architecture_globale.md](../01_architecture_globale.md#6-support-vocal-speech-to-text) · [05_api_endpoints.md](../05_api_endpoints.md#endpoint-audio-stt)

### À faire

- [x] 28.1 Créer `backend/app/core/stt.py` — service Speech-to-Text
  - `transcribe(audio_file, language="fr")` → str
  - Option 1 : Whisper API (OpenAI) — simple, payant
  - Option 2 : Google Cloud Speech — gratuit (quota), plus de config
  - Configurable via `.env` : `STT_PROVIDER`, `OPENAI_API_KEY` ou `GOOGLE_STT_CREDENTIALS`

- [x] 28.2 Créer l'endpoint `POST /api/chat/conversations/{id}/audio`
  - Accepte un fichier audio (webm, wav, mp3, ogg)
  - Transcrit via le service STT
  - Injecte le texte transcrit dans la boucle agent (comme un message texte)
  - Retourne un SSE stream (même format que `/message`)
  - Envoie d'abord un événement `transcript` avec le texte transcrit
  - Code dans [05_api_endpoints.md](../05_api_endpoints.md#endpoint-audio-stt)

- [x] 28.3 Créer `src/composables/useAudioRecorder.ts`
  - Utilise l'API `MediaRecorder` du navigateur
  - `startRecording()` — demande la permission micro + commence l'enregistrement
  - `stopRecording()` → Blob audio
  - Gestion des erreurs (permission refusée, pas de micro)
  - Format de sortie : webm (default MediaRecorder)

- [x] 28.4 Créer `src/components/chat/AudioRecordButton.vue`
  - Bouton micro dans la zone de saisie
  - États : inactif → enregistrement (animation pulse) → envoi
  - Au clic : commence l'enregistrement
  - Au relâchement (ou re-clic) : arrête + envoie au backend
  - Affiche la transcription reçue dans le message utilisateur

- [x] 28.5 Intégrer dans `MessageInput.vue`
  - Ajouter le bouton AudioRecord à côté du bouton envoyer

- [x] 28.6 Tester le flow vocal complet avec 'agent-browser --headed'
  - Cliquer sur le micro → parler → relâcher → voir la transcription → voir la réponse de l'agent

### Comment

1. Whisper API est le plus simple : un appel API avec le fichier audio → texte
2. MediaRecorder produit du webm par défaut — compatible avec Whisper
3. L'événement SSE `transcript` permet au frontend d'afficher ce que l'utilisateur a dit
4. La réponse reste en texte (pas de TTS pour le MVP)

---

## Étape 29 — Seed données réalistes

**Fichiers concernés** : [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [x] 29.1 Enrichir les référentiels ESG
  - Compléter les grilles avec tous les critères réalistes (pas juste 2-3)
  - BCEAO : 16 critères (5E+6S+5G), pondération E:40 S:30 G:30
  - GCF : 8 critères (4E+2S+2G), pondération E:60 S:25 G:15
  - IFC : 17 critères (6E+8S+3G), pondération E:35 S:40 G:25

- [x] 29.2 Enrichir les fonds verts
  - 10 fonds réalistes (5 existants + 5 ajoutés : BCEAO, SUNREF/AFD, FIDA, BEI-Proparco, SREP/CIF)
  - Montants, secteurs, pays, critères, dates, URLs sources
  - 30 descriptions chunks détaillées (éligibilité, critères, processus) pour chaque fonds

- [x] 29.3 Enrichir les benchmarks sectoriels
  - 16 benchmarks pour 8 secteurs × 2 pays (CIV + SEN)
  - Agriculture, énergie, recyclage, agroalimentaire, transport, textile, BTP, services

- [x] 29.4 Enrichir la base de connaissances (`data/knowledge_base/`)
  - Réglementation UEMOA/BCEAO (directive finance durable, cadre réglementaire, incitations)
  - Guide ESG pour PME africaines (actions pratiques par pilier, recommandations sectorielles)
  - Taxonomie verte BCEAO (6 objectifs, activités éligibles, critères DNSH, seuils)

- [x] 29.5 Créer un compte admin de démo et une entreprise de démo avec données pré-remplies
  - Admin : demo@esgadvisor.ai / demo1234 (role admin)
  - Entreprise : AgroVert Côte d'Ivoire (agroalimentaire, 85 employés, 450M FCFA CA)
  - 2 scores ESG (initial 38.5 → actuel 52.0, +13.5 pts en 6 mois)
  - 5 empreintes carbone mensuelles (oct 2024 → fév 2025, tendance baisse)
  - Plan d'action 9 items (3 faits, 4 en cours, 2 à faire)

### Comment

1. Les données réalistes sont cruciales pour la démo et le hackathon
2. Rechercher les vrais critères BCEAO, les vrais fonds (BAD, BOAD, GCF, etc.)
3. L'entreprise de démo doit avoir un historique suffisant pour montrer toutes les fonctionnalités

---

## Étape 30 — UX/UI Polish + Tests

### À faire

- [x] 30.1 Polish UX général
  - Loading states partout (spinners, skeletons) — déjà en place
  - Messages d'erreur clairs et localisés en français — déjà en place
  - Empty states ("Pas encore de score ESG. Démarrez une conversation pour commencer !") — déjà en place
  - Responsive design (sidebar collapsible sur mobile) — ajouté
  - Transitions et animations subtiles — route transitions fade ajoutées

- [x] 30.2 Polish du chat
  - Scroll automatique vers le bas pendant le streaming (smart: seulement si near bottom)
  - Auto-resize de la zone de saisie — ajouté
  - Raccourci Entrée pour envoyer, Shift+Entrée pour retour à la ligne — déjà en place
  - Messages d'accueil contextuels — suggestion chips ajoutés
  - Typing indicator (dots animation) — ajouté
  - Bouton "scroll to bottom" flottant — ajouté

- [x] 30.3 Polish du dashboard
  - Animations des jauges et graphiques au chargement — score counter animation ajouté
  - Tooltips sur les graphiques — gérés par Chart.js par défaut

- [x] 30.4 Tests backend
  - [x] Tests existants des handlers de skills (test_skills.py — 15 tests)
  - [x] Tests existants de l'agent (test_agent.py — 9 tests)
  - [x] Tests des endpoints API auth (4 tests : register, duplicate, login, wrong password)
  - [x] Tests des endpoints API entreprises (3 tests : create, list, get)
  - [x] Tests des endpoints API chat (3 tests : create, list, delete conversation)
  - pytest + pytest-asyncio ajoutés aux dépendances, conftest.py créé

- [x] 30.5 Tests frontend
  - [x] Test du composable `useChat` (2 tests : clearMessages, sendMessage avec mock SSE)
  - [x] Test du store auth (3 tests : login, logout, init)
  - vitest + @vue/test-utils + jsdom installés, 5 tests passent

- [x] 30.6 Test de bout en bout avec 'agent-browser --headed'
  - Scénario complet : login → chat (suggestion chips, streaming SSE, skills) → dashboard (score cards, radar) → empreinte carbone (KPI, pie chart) → score crédit (empty state) → plan d'action (progress, actions) → documents (empty state) → fonds verts admin (table) → mobile responsive (sidebar overlay)
  - Bug trouvé et corrigé : race condition suggestion chips (skipRouteWatcher flag)
  - Vérifier que tout fonctionne de bout en bout ✅

### Comment

1. Prioriser les polish qui ont le plus d'impact visuel pour la démo
2. Les tests ne doivent pas être exhaustifs — couvrir les chemins critiques
3. Le test E2E peut être manuel (pas besoin de Cypress pour le hackathon)

---

## Étape 31 — Vidéo pitch + deck

### À faire

- [ ] 31.1 Préparer le scénario de démo
  - Script de 3-5 minutes montrant les fonctionnalités clés
  - Parcours : arrivée → inscription → première conversation → score ESG → fonds verts → empreinte carbone → rapport PDF → dashboard
  - Montrer l'innovation : scoring multi-référentiel, crédit vert, support vocal

- [ ] 31.2 Enregistrer la vidéo de démo
  - Screen recording avec voix off
  - Montrer l'interface fluide (streaming, indicateurs skills, graphiques)
  - Outil : OBS Studio, Loom, ou QuickTime

- [ ] 31.3 Préparer le deck (si nécessaire)
  - Problème → Solution → Démo → Impact → Équipe
  - Chiffres clés : nombre de PME ciblées, volume fonds verts disponibles, etc.

### Comment

1. Le scénario doit montrer la valeur ajoutée en 3 minutes max
2. Utiliser l'entreprise de démo avec données pré-remplies
3. Mettre en avant les innovations : IA conversationnelle + multi-référentiel + crédit vert

---

## Étape 32 — Déploiement démo

### À faire

- [ ] 32.1 Choisir la plateforme de déploiement
  - Option rapide : Railway, Render, ou Fly.io (supporte Docker Compose)
  - Option manuelle : VPS (Hetzner, DigitalOcean) + Docker Compose
  - Base de données : service managé (Railway PostgreSQL, Supabase, Neon) ou container

- [ ] 32.2 Configurer les variables d'environnement en production
  - `DB_PASSWORD` (fort), `JWT_SECRET` (64 chars random), `LLM_API_KEY`, etc.
  - `APP_URL` = URL de production

- [ ] 32.3 Configurer le frontend pour la production
  - `vite build` → fichiers statiques
  - Nginx pour servir le frontend + proxy vers le backend

- [ ] 32.4 Configurer HTTPS
  - Certificat SSL (Let's Encrypt ou fourni par la plateforme)

- [ ] 32.5 Déployer
  - `docker compose up -d` en production
  - Exécuter les migrations : `alembic upgrade head`
  - Exécuter le seed : `python -m app.seed`

- [ ] 32.6 Tester en production
  - Vérifier tous les flux : inscription, chat, skills, rapports, admin
  - Vérifier les performances (temps de réponse LLM, streaming)

- [ ] 32.7 Partager l'URL de démo

### Comment

1. Railway est probablement le plus simple (support Docker, PostgreSQL intégré, HTTPS automatique)
2. Ne pas oublier les variables d'env en production (surtout les clés API)
3. Tester le streaming SSE en production (certains reverse proxies bufferisent)

---

## Récapitulatif Semaine 5

| # | Étape | Statut |
|---|-------|--------|
| 26 | Admin CRUD skills | ✅ |
| 27 | Admin CRUD référentiels ESG | ✅ |
| 28 | Support vocal (STT) | ✅ |
| 29 | Seed données réalistes | ✅ |
| 30 | UX/UI polish + tests | ✅ |
| 31 | Vidéo pitch + deck | ⬜ |
| 32 | Déploiement démo | ⬜ |

**Critère de fin de semaine** : Le produit est déployé et accessible en ligne. L'admin peut gérer les skills et les référentiels. Le support vocal fonctionne. Les données de démo sont réalistes. La vidéo de démo est prête.

---

## Fichiers du plan à consulter

| Fichier | Quand le consulter |
|---------|-------------------|
| [05_api_endpoints.md](../05_api_endpoints.md) | Endpoints admin skills, référentiels, fonds, templates, stats, audio |
| [07_admin_skills.md](../07_admin_skills.md) | Maquettes admin : liste skills, éditeur skills, liste référentiels, éditeur grille, simulateur scoring |
| [01_architecture_globale.md](../01_architecture_globale.md) | Support vocal (STT), système de notifications |
| [06_frontend.md](../06_frontend.md) | Composants admin, AudioRecordButton |
| [08_arborescence_projet.md](../08_arborescence_projet.md) | docker-compose production, .env |
