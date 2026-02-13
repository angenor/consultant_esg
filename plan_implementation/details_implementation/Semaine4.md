# Semaine 4 — Crédit Vert + Plans d'Action + Rapports + Frontend Métier

> **Objectif** : Compléter les modules avancés (crédit vert, plans d'action, notifications, rapports PDF) et créer toutes les vues frontend métier.

> **Prérequis** : Semaine 3 terminée (skills métier fonctionnels via le chat)

---

## Étape 19 — Scoring crédit vert alternatif (Module 5)

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--calculate_credit_score) · [02_modeles_donnees.md](../02_modeles_donnees.md#credit_scores-scoring-crédit-vert-alternatif--module-5) · [06_frontend.md](../06_frontend.md#6-creditscoreview-module-5--innovation-3)

### À faire

- [x] 19.1 Implémenter le handler `calculate_credit_score`
  - **Score solvabilité (0-100)** : régularité transactions, volume activité, ancienneté, documents financiers uploadés
  - **Score impact vert (0-100)** : dernier score ESG, tendance, certifications, plan d'action actif
  - **Score combiné** : moyenne pondérée configurable (ex: 50/50)
  - **Transparence** : chaque facteur listé avec son impact (+/-) dans `facteurs_json`
  - Sauvegarde dans `credit_scores`
  - Retourne : scores + facteurs + recommandations d'amélioration
  - Détail complet dans [03_systeme_skills.md](../03_systeme_skills.md#skill--calculate_credit_score)

- [x] 19.2 Créer `backend/app/api/credit_score.py`
  - `POST /api/credit-score/calculate` — calculer le score crédit vert
  - `GET /api/credit-score/entreprise/{id}` — dernier score + historique
  - `POST /api/credit-score/entreprise/{id}/share` — générer un lien de partage sécurisé (token temporaire)

- [x] 19.3 Créer les schemas Pydantic `backend/app/schemas/credit_score.py`

- [x] 19.4 Tester via le chat avec agent-browser --headed : "Calcule mon score de crédit vert"
  - L'agent doit poser les questions financières puis calculer

### Comment

1. Pour le MVP, les données financières sont déclaratives (questionnaire via le chat)
2. Le score combine solvabilité + engagement ESG — c'est l'innovation clé du projet
3. La transparence des facteurs est critique : l'utilisateur doit comprendre pourquoi il a tel score

---

## Étape 20 — Plan d'action et suivi (Module 6)

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md#skill--manage_action_plan) · [02_modeles_donnees.md](../02_modeles_donnees.md#action_plans--action_items-plans-daction-et-suivi--module-6)

### À faire

- [x] 20.1 Implémenter le handler `manage_action_plan`
  - Action `create` : génère un plan basé sur les lacunes du dernier score ESG, priorise les actions, définit des échéances
  - Action `add_item` : ajoute une action au plan existant
  - Action `update_status` : met à jour le statut d'une action (a_faire → en_cours → fait), déclenche notification si palier atteint
  - Retourne : plan + items + barre de progression + prochaines échéances

- [x] 20.2 Créer `backend/app/api/action_plans.py`
  - `POST /api/action-plans/` — créer un plan
  - `GET /api/action-plans/entreprise/{id}` — plans de l'entreprise
  - `GET /api/action-plans/{id}` — détail d'un plan avec ses actions
  - `PUT /api/action-plans/items/{item_id}` — mettre à jour le statut d'une action
  - `GET /api/action-plans/{id}/progress` — progression globale

- [x] 20.3 Créer les schemas Pydantic `backend/app/schemas/action_plan.py`

- [x] 20.4 Tester : "Crée-moi un plan d'action pour passer de 62 à 75 sur le référentiel BCEAO"

### Comment

1. Le plan est généré en analysant les critères où le score est faible
2. Chaque action est classée : quick_win / moyen_terme / long_terme
3. L'impact estimé sur le score est calculé en fonction du poids du critère visé

---

## Étape 21 — Système de notifications

**Fichiers concernés** : [01_architecture_globale.md](../01_architecture_globale.md#7-système-de-notifications) · [02_modeles_donnees.md](../02_modeles_donnees.md#notifications-rappels-et-alertes)

### À faire

- [x] 21.1 Créer `backend/app/api/notifications.py`
  - `GET /api/notifications/` — mes notifications (paginées, triées par date)
  - `PUT /api/notifications/{id}/read` — marquer comme lue
  - `PUT /api/notifications/read-all` — tout marquer comme lu
  - `GET /api/notifications/unread-count` — compteur non lues

- [x] 21.2 Créer un service de notifications `backend/app/core/notifications.py`
  - `create_notification(user_id, type, titre, contenu, lien)` — crée une notification en BDD
  - Types : `rappel_action`, `echeance_fonds`, `nouveau_fonds`, `progres_score`, `action_completee`

- [x] 21.3 Brancher les notifications sur les événements métier
  - Quand une action passe à "fait" → notification `action_completee`
  - Quand le score ESG augmente → notification `progres_score`
  - Les échéances de fonds et rappels d'actions seront gérés par un job cron plus tard

- [x] 21.4 Créer `src/composables/useNotifications.ts`
  - Polling régulier de `/api/notifications/unread-count` (toutes les 30s)
  - Ou en même temps que d'autres requêtes

- [x] 21.5 Créer `src/components/common/NotificationBell.vue`
  - Icône cloche dans le header
  - Badge avec le nombre de non lues
  - Dropdown avec la liste des notifications récentes
  - Clic → marquer comme lue + naviguer vers le lien

- [x] 21.6 Créer `src/stores/notifications.ts` — Pinia store

### Comment

1. Le polling est simple et suffisant pour le MVP (pas besoin de WebSocket pour les notifications)
2. Les notifications sont créées côté backend quand un événement métier se produit
3. Le frontend les affiche via la cloche dans le header

---

## Étape 22 — Templates HTML rapports

**Fichiers concernés** : [02_modeles_donnees.md](../02_modeles_donnees.md#report_templates) · [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [ ] 22.1 Créer `backend/app/reports/__init__.py`

- [ ] 22.2 Créer les templates Jinja2 HTML/CSS
  - [ ] `templates/base.html` — template de base (header, footer, styles CSS, mise en page A4)
  - [ ] `templates/rapport_esg.html` — rapport ESG complet (page de garde, résumé, scores par pilier, détails critères, radar chart, plan d'action)
  - [ ] `templates/rapport_carbone.html` — rapport empreinte carbone (total, répartition, évolution, plan réduction)
  - [ ] `templates/dossier_candidature.html` — dossier de candidature fonds vert (profil, scores, plan, budget)
  - Les rapports doivent inclure la section multi-référentiel (comparaison des scores)

- [ ] 22.3 Seeder les templates dans `report_templates`
  - `sections_json` décrit la structure de chaque section (source: db, llm, code)
  - `template_html` contient le HTML Jinja2

### Comment

1. Les templates sont en HTML/CSS pur, stylés pour impression (format A4)
2. Jinja2 injecte les données (scores, graphiques, textes générés par le LLM)
3. Les sections `source: "llm"` seront générées par le skill `generate_report_section`

---

## Étape 23 — Génération PDF (WeasyPrint + charts)

**Fichiers concernés** : [08_arborescence_projet.md](../08_arborescence_projet.md) · [03_systeme_skills.md](../03_systeme_skills.md)

### À faire

- [ ] 23.1 Créer `backend/app/reports/charts.py`
  - `generate_radar_chart(scores_piliers)` → image base64 ou fichier
  - `generate_bar_chart(data, labels)` → image base64
  - `generate_pie_chart(data, labels)` → image base64
  - `generate_evolution_chart(dates, scores)` → image base64
  - Utilise `matplotlib` avec style personnalisé

- [ ] 23.2 Créer `backend/app/reports/generator.py`
  - `generate_report(entreprise_id, template_name, db)` → bytes (PDF)
  - Charge le template depuis `report_templates`
  - Pour chaque section : récupère les données (BDD, LLM, charts)
  - Rend le HTML avec Jinja2
  - Convertit en PDF avec WeasyPrint
  - Sauvegarde le PDF dans `uploads/reports/`

- [ ] 23.3 Implémenter le handler `generate_report_section`
  - Le LLM génère le texte d'une section de rapport à partir d'un prompt + données contextuelles
  - Utilisé par le générateur pour les sections `source: "llm"`

- [ ] 23.4 Implémenter le handler `assemble_pdf`
  - Appelé par le LLM quand l'utilisateur demande un rapport
  - Orchestre le générateur de rapports

- [ ] 23.5 Créer `backend/app/api/reports.py`
  - `POST /api/reports/generate` — lance la génération (body: `entreprise_id`, `template_name`)
  - `GET /api/reports/entreprise/{id}` — liste les rapports générés
  - `GET /api/reports/{id}/download` — télécharge le PDF

- [ ] 23.6 Ajouter `weasyprint` et `matplotlib` au `requirements.txt`

- [ ] 23.7 Tester : "Génère un rapport ESG complet pour mon entreprise" → PDF téléchargeable

### Comment

1. WeasyPrint convertit du HTML/CSS en PDF — parfait pour des rapports stylés
2. Les charts matplotlib sont générés en mémoire et injectés en base64 dans le HTML
3. Le handler `assemble_pdf` est le point d'entrée pour le LLM

---

## Étape 24 — Frontend : CarbonView + CreditScoreView + ActionPlanView

**Fichiers concernés** : [06_frontend.md](../06_frontend.md#5-carbonview) · [06_frontend.md](../06_frontend.md#6-creditscoreview-module-5--innovation-3) · [06_frontend.md](../06_frontend.md#7-actionplanview-module-6)

### À faire

- [ ] 24.1 Installer Chart.js
  - `npm install chart.js vue-chartjs`

- [ ] 24.2 Créer `CarbonView.vue` + composants carbone
  - [ ] `components/carbon/CarbonSummary.vue` — empreinte totale + variation vs N-1
  - [ ] `components/carbon/CarbonBySource.vue` — pie chart (énergie, transport, déchets, achats)
  - [ ] `components/carbon/CarbonEvolution.vue` — graphique ligne évolution mensuelle
  - [ ] `components/carbon/SectorComparison.vue` — comparaison avec moyenne sectorielle
  - [ ] `components/carbon/ReductionPlan.vue` — plan de réduction (quick-wins, moyen terme, long terme)
  - Maquette dans [06_frontend.md](../06_frontend.md#5-carbonview)

- [ ] 24.3 Créer `CreditScoreView.vue` + composants crédit
  - [ ] `components/credit/CreditScoreGauge.vue` — jauge semi-circulaire du score combiné
  - [ ] `components/credit/ScoreBreakdown.vue` — détail solvabilité vs impact vert + facteurs (+/-)
  - [ ] `components/credit/ShareScoreButton.vue` — bouton génération lien de partage sécurisé
  - Maquette dans [06_frontend.md](../06_frontend.md#6-creditscoreview-module-5--innovation-3)

- [ ] 24.4 Créer `ActionPlanView.vue` + composants plan d'action
  - [ ] `components/actions/ProgressTracker.vue` — barre de progression globale
  - [ ] `components/actions/ActionItemCard.vue` — carte action avec statut, échéance, priorité, toggle statut
  - [ ] `components/actions/ActionPlanTimeline.vue` — timeline visuelle par catégorie (quick-win, moyen, long)
  - Maquette dans [06_frontend.md](../06_frontend.md#7-actionplanview-module-6)

- [ ] 24.5 Ajouter les routes dans le router
  - `/carbon` → `CarbonView.vue`
  - `/credit-score` → `CreditScoreView.vue`
  - `/action-plan` → `ActionPlanView.vue`

- [ ] 24.6 Mettre à jour la sidebar avec les nouveaux liens

### Comment

1. Chaque vue appelle les API correspondantes pour charger les données
2. Chart.js (via vue-chartjs) pour tous les graphiques
3. Les composants doivent gérer l'état "pas encore de données" (encourager l'utilisateur à passer par le chat)

---

## Étape 25 — Dashboard entreprise (multi-référentiel)

**Fichiers concernés** : [06_frontend.md](../06_frontend.md#3-dashboardview-multi-référentiel)

### À faire

- [ ] 25.1 Créer les composants dashboard
  - [ ] `components/dashboard/ReferentielSelector.vue` — dropdown pour choisir le référentiel
  - [ ] `components/dashboard/ScoreCard.vue` — carte score E/S/G + score global
  - [ ] `components/dashboard/ScoreComparison.vue` — barres horizontales comparant les scores par référentiel
  - [ ] `components/dashboard/RadarChart.vue` — graphique radar E/S/G (Chart.js)
  - [ ] `components/dashboard/ScoreHistory.vue` — graphique évolution temporelle des scores
  - [ ] `components/dashboard/FundsMatchList.vue` — liste des fonds recommandés avec compatibilité
  - [ ] `components/dashboard/ActionPlan.vue` — résumé du plan d'action (prochaines échéances)

- [ ] 25.2 Compléter `DashboardView.vue`
  - Sélecteur de référentiel en haut
  - Cartes scores E/S/G + score global
  - Comparaison multi-référentiel (barres)
  - Alertes si seuil non atteint sur un référentiel
  - Radar chart + historique
  - Fonds recommandés
  - Plan d'action résumé
  - Maquette complète dans [06_frontend.md](../06_frontend.md#3-dashboardview-multi-référentiel)

- [ ] 25.3 Créer `DocumentsView.vue`
  - Liste des documents uploadés avec statut d'analyse
  - Bouton upload
  - Prévisualisation (nom, type, taille, date)

- [ ] 25.4 Tester le dashboard complet avec des données réelles

### Comment

1. Le dashboard est la vue synthétique de toutes les données de l'entreprise
2. Le sélecteur de référentiel filtre les scores affichés
3. La comparaison multi-référentiel montre d'un coup d'oeil les forces/faiblesses par institution

---

## Récapitulatif Semaine 4

| # | Étape | Statut |
|---|-------|--------|
| 19 | Scoring crédit vert alternatif | ✅ |
| 20 | Plan d'action et suivi | ✅ |
| 21 | Système de notifications | ✅ |
| 22 | Templates HTML rapports | ⬜ |
| 23 | Génération PDF (WeasyPrint + charts) | ⬜ |
| 24 | Frontend : CarbonView + CreditScoreView + ActionPlanView | ⬜ |
| 25 | Dashboard entreprise multi-référentiel | ⬜ |

**Critère de fin de semaine** : Toutes les vues frontend sont fonctionnelles. L'utilisateur peut voir son dashboard multi-référentiel, son empreinte carbone, son score crédit vert, son plan d'action, recevoir des notifications, et générer un rapport PDF complet.

---

## Fichiers du plan à consulter

| Fichier | Quand le consulter |
|---------|-------------------|
| [02_modeles_donnees.md](../02_modeles_donnees.md) | Tables credit_scores, action_plans, action_items, notifications, report_templates |
| [03_systeme_skills.md](../03_systeme_skills.md) | Handlers calculate_credit_score, manage_action_plan, generate_report_section, assemble_pdf |
| [05_api_endpoints.md](../05_api_endpoints.md) | Endpoints credit-score, action-plans, notifications, reports |
| [06_frontend.md](../06_frontend.md) | Maquettes CarbonView, CreditScoreView, ActionPlanView, DashboardView |
