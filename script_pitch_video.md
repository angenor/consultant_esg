# Réponses - Hackathon Francophone IA (Green Open Lab / IFDD)

---

## Pitch (200 mots max)

ESG Mefali est une plateforme conversationnelle d'IA qui démocratise l'accès à la finance verte pour les PME francophones africaines.

En Afrique francophone, 90 % des PME sont exclues des fonds verts : dossiers complexes, consultants inabordables (5 000–20 000 $), barrières linguistiques. ESG Mefali résout ce problème grâce à un agent conversationnel intelligent qui guide les entrepreneurs en français.

La plateforme combine : un scoring ESG multi-référentiel (BCEAO, IFC, GCF, etc) adapté aux réalités ouest-africaines, un calculateur d'empreinte carbone contextualisé, un matching intelligent vers 10 fonds verts régionaux et internationaux, un crédit scoring alternatif intégrant mobile money et pratiques vertes, et la génération automatique de dossiers PDF prêts à soumettre.

Une extension Chrome accompagne les PME directement sur les sites de fonds, avec pré-remplissage automatique et suggestions IA pour chaque champ.

Stack technique : Vue 3 + FastAPI + PostgreSQL/pgvector + Claude (OpenRouter). Architecture RAG hybride (SQL + recherche sémantique), 20+ skills dynamiques, streaming SSE.

Notre ambition : rendre chaque PME africaine capable de financer sa transition verte, sans intermédiaire coûteux.

---

## Thématique principale

Finance Durable (avec des composantes Climat et Employabilité verte)

---

## Problème

Les PME francophones africaines sont massivement exclues de la finance verte. Trois barrières les bloquent :

1. Complexité ESG — Les référentiels (IFC, GCF, BCEAO) sont techniques, volumineux et en anglais. Sans consultant spécialisé (5 000–20 000 $), une PME ne peut ni évaluer sa conformité, ni identifier ses lacunes.

2. Opacité du financement vert — Il existe des dizaines de fonds (BOAD, BAD, GCF, AFD/SUNREF...) avec des critères d'éligibilité différents. Les PME ne savent pas lesquels existent, ne savent pas si elles sont éligibles, et abandonnent face à la complexité des dossiers.

3. Invisibilité financière — Sans historique de crédit formel, même les PME vertueuses sur le plan environnemental ne peuvent pas accéder aux prêts bancaires. Leurs bonnes pratiques ESG ne sont ni mesurées ni valorisées.

Résultat : moins de 10 % des financements climat en Afrique atteignent les PME, alors qu'elles représentent 80 % de l'emploi et sont les premières impactées par le changement climatique.

---

## Comment utilisez-vous l'intelligence artificielle concrètement ?

L'IA est au cœur de chaque fonctionnalité :

- Agent conversationnel (Claude via OpenRouter) — Un LLM orchestre 20+ skills dynamiques via function calling. Il collecte les données par dialogue naturel (pas de formulaires), exécute les calculs, et synthétise les résultats en français. Boucle agentique multi-tours (max 10 itérations) avec streaming SSE.

- RAG hybride (SQL + pgvector) — Les documents entreprise et les descriptions de fonds sont découpés en chunks, vectorisés (Voyage AI, 1024 dimensions) et indexés avec HNSW dans PostgreSQL. La recherche combine filtrage SQL (secteur, pays, montant) et similarité cosinus sémantique pour un matching précis des fonds.

- Scoring ESG par NLP — L'agent extrait les réponses quantitatives (pourcentages, kWh, tonnes) et qualitatives (pratiques déclarées) du langage naturel, les mappe sur les grilles multi-référentielles, et calcule les scores pondérés par pilier (E/S/G).

- Crédit scoring alternatif — Modèle hybride combinant score de solvabilité et score d'impact vert, intégrant données ESG, tendances carbone et transactions mobile money.

- Suggestion IA pour formulaires (extension Chrome) — Le LLM génère des contenus adaptés (descriptions de projet, motivations) pour chaque champ de candidature, en contexte avec le profil entreprise et le fonds ciblé.

- Analyse documentaire — OCR (pytesseract) + extraction PDF/Word + chunking intelligent pour analyser les documents entreprise et pré-remplir les dossiers.

---

## En quoi votre approche se distingue par rapport aux solutions existantes ? (200 mots max)

Les solutions ESG existantes (Refinitiv, Sustainalytics, CDP) ciblent les grandes entreprises occidentales avec des abonnements à 10 000+ $/an, des interfaces en anglais et des référentiels inadaptés à l'Afrique.

ESG Mefali se distingue sur 5 axes :

1. Conversationnel-first — Zéro formulaire. L'agent IA pose les bonnes questions, extrait les données du dialogue naturel, et enrichit le profil progressivement. Accessible aux entrepreneurs peu alphabétisés grâce à la saisie vocale.

2. Multi-référentiel contextualisé — Supporte simultanément les cadres BCEAO (UEMOA), IFC et GCF, avec des critères et pondérations adaptés par secteur et pays africain. Pas de grille unique imposée.

3. Du diagnostic à l'action — Ne s'arrête pas au score : génère des plans de réduction carbone chiffrés (coût, ROI en XOF), assemble les dossiers PDF, et guide le remplissage des formulaires en ligne via l'extension Chrome.

4. Crédit scoring inclusif — Valorise les pratiques vertes dans l'accès au crédit, intégrant mobile money et données alternatives pour les PME sans historique bancaire formel.

5. Architecture ouverte — Skills dynamiques en base de données, modèle LLM interchangeable (Claude/GPT/Mistral via OpenRouter), extensible sans redéploiement.

---

## Stade de développement

MVP — Infrastructure complète déployée via Docker, 20 tables en base, authentification, chat IA avec streaming, scoring ESG, calculateur carbone, matching de fonds, extension Chrome fonctionnelle avec 27 tests unitaires. Prêt pour démonstration.

---

## À quels Objectifs de Développement Durable contribuez-vous ?

- ODD 8 — Travail décent et croissance économique : accès au capital pour les PME vertes, promotion de l'emploi vert
- ODD 9 — Industrie, innovation et infrastructure : adoption de technologies propres par les PME africaines
- ODD 10 — Inégalités réduites : démocratisation de la finance verte, inclusion des non-bancarisés via le crédit scoring alternatif
- ODD 12 — Consommation et production responsables : suivi des déchets, promotion de l'économie circulaire
- ODD 13 — Mesures relatives à la lutte contre les changements climatiques : quantification de l'empreinte carbone, plans de réduction, canalisation du financement climat vers les PME
- ODD 17 — Partenariats pour la réalisation des objectifs : connexion PME ↔ fonds internationaux ↔ banques

---

## Qu'attendez-vous du programme de mentorat ?

Nous attendons du programme de mentorat un accompagnement sur trois axes :

1. Validation terrain et go-to-market — Confronter notre MVP à des retours d'utilisateurs réels (PME ouest-africaines), affiner le produit, et définir une stratégie de déploiement pays par pays en commençant par la Côte d'Ivoire et le Sénégal.

2. Partenariats stratégiques — Être mis en relation avec des acteurs clés : institutions financières régionales (BOAD, BCEAO), organisations de microfinance, incubateurs africains, et bailleurs de fonds verts pour des pilotes concrets.

3. Modèle économique et financement — Structurer un modèle de revenus viable (freemium pour PME, licences pour institutions financières, commissions sur fonds débloqués) et préparer un dossier de levée de fonds pour passer du MVP à l'échelle.

Le coaching sur l'IA responsable nous intéresse particulièrement pour assurer la transparence de nos algorithmes de scoring et éviter les biais dans le crédit scoring alternatif.

---

## Lien drive de votre vidéo Pitch (2 min)

(À compléter)

---

## Lien Drive de votre Deck PDF

(À compléter)





# Script Vidéo Pitch — ESG Mefali (2 minutes)

## Conseils avant d'enregistrer

- **Format** : Filme-toi face caméra (webcam ou téléphone en mode paysage)
- **Fond** : Neutre ou avec ton écran d'ordi visible derrière toi
- **Tenue** : Correcte mais pas trop formelle (chemise, polo)
- **Ton** : Passionné, naturel, pas robotique — tu parles d'un problème qui te tient à cœur
- **Durée cible** : 1min50 (garde 10s de marge)
- **Astuce** : Tu peux alterner entre toi face caméra et des captures d'écran de la plateforme

---

## Structure et texte à dire

### ACCROCHE — Face caméra (0:00 – 0:15)

> « Bonjour, je suis [TON NOM], createur d'ESG Mefali.
>
> Saviez-vous que moins de 10 % des financements climat en Afrique atteignent les PME ? Pourtant, elles représentent 80 % de l'emploi sur le continent.
>
> Le problème n'est pas le manque de fonds. C'est que les PME n'y ont pas accès. »

---

### LE PROBLÈME — Face caméra (0:15 – 0:40)

> « Aujourd'hui, une PME ivoirienne ou sénégalaise qui veut accéder à un fonds vert fait face à trois murs :
>
> **Premier mur** : les référentiels ESG sont complexes, techniques, souvent en anglais. Pour s'y conformer, il faut un consultant à 5 000 voire 20 000 dollars — impensable pour une PME.
>
> **Deuxième mur** : il existe des dizaines de fonds — BOAD, GCF, BAD, AFD — mais personne ne sait lequel correspond à son profil, ni comment remplir le dossier.
>
> **Troisième mur** : sans historique de crédit formel, pas de prêt bancaire. Même si l'entreprise a d'excellentes pratiques environnementales. »

---

### LA SOLUTION — Montrer l'écran / démo (0:40 – 1:20)

> « ESG Mefali change la donne. C'est un conseiller ESG virtuel, accessible en français, qui accompagne les PME de A à Z. »

*[Montre l'interface du chat]*

> « L'entrepreneur dialogue simplement avec l'agent IA. Pas de formulaires compliqués. L'agent pose les bonnes questions, calcule le score ESG selon les référentiels africains — BCEAO, IFC, GCF — et identifie les fonds verts compatibles. »

*[Montre le dashboard avec les scores ESG]*

> « Il calcule aussi l'empreinte carbone, propose un plan de réduction chiffré en francs CFA, et génère les dossiers de candidature en PDF, prêts à soumettre. »

*[Montre l'extension Chrome si possible]*

> « Et notre extension Chrome va encore plus loin : elle accompagne l'entrepreneur directement sur le site du fonds, pré-remplit les formulaires et suggère les réponses grâce à l'IA. »

---

### LA TECH — Face caméra (1:20 – 1:35)

> « Techniquement, la plateforme repose sur une architecture RAG hybride : on combine recherche sémantique par vecteurs et filtrage SQL pour matcher précisément les PME avec les bons fonds. L'agent utilise Claude comme LLM avec plus de 20 skills dynamiques. Le tout tourne sur Vue 3, FastAPI et PostgreSQL avec pgvector. On est au stade MVP, fonctionnel et prêt pour démonstration. »

---

### L'AMBITION — Face caméra, regard caméra (1:35 – 1:55)

> « Notre vision : que chaque PME africaine puisse financer sa transition verte, sans intermédiaire coûteux. On cible d'abord la zone UEMOA — Côte d'Ivoire, Sénégal, Mali — avant de s'étendre à toute l'Afrique francophone.
>
> ESG Mefali, c'est la finance verte rendue accessible à ceux qui en ont le plus besoin. Merci. »

---

## Récapitulatif du timing

| Segment | Durée | Cumul | Ce que tu fais |
|---------|-------|-------|----------------|
| Accroche | 15s | 0:15 | Face caméra, ton accrocheur |
| Problème | 25s | 0:40 | Face caméra, 3 points clairs |
| Solution | 40s | 1:20 | Partage d'écran / captures de la plateforme |
| Tech | 15s | 1:35 | Face caméra, résumé technique rapide |
| Ambition | 20s | 1:55 | Face caméra, regard direct, conclusion forte |

---

## Checklist avant d'enregistrer

- [ ] La plateforme tourne (`docker compose up -d`) pour les captures
- [ ] Préparer 3-4 captures d'écran clés : chat, dashboard ESG, calculateur carbone, extension Chrome
- [ ] Tester le son (pas de bruit de fond)
- [ ] Répéter 2-3 fois à voix haute pour le timing
- [ ] Filmer en 1080p minimum
- [ ] Uploader sur Google Drive et mettre le lien en accès "Tous ceux qui ont le lien"

---
---

# Script Vidéo de Présentation — ESG Mefali (1 minute, haute qualité)

## Consignes techniques

- **Durée** : 60 secondes max
- **Format** : Paysage (16:9), 1080p minimum
- **Cadrage** : Face caméra, buste visible, fond neutre ou professionnel
- **Audio** : Micro-cravate ou pièce calme, pas de musique pendant la parole
- **Ton** : Confiant, naturel, engagé — pas de lecture monotone

---

## Script à dire

### 1. PRÉSENTATION PERSONNELLE (0:00 – 0:10)

> « Bonjour, je suis **[TON PRÉNOM NOM]**, développeur et entrepreneur, créateur d'ESG Mefali. Je suis basé en **Côte d'Ivoire**. »

*[Face caméra, sourire, regard direct]*

---

### 2. NOM ET DESCRIPTION DU PROJET (0:10 – 0:25)

> « **ESG Mefali**, c'est un conseiller ESG virtuel propulsé par l'intelligence artificielle. Une plateforme conversationnelle qui accompagne les PME francophones africaines pour accéder à la finance verte — du diagnostic ESG jusqu'au montage complet du dossier de financement. »

*[Possibilité d'insérer 2-3 secondes de captures d'écran de la plateforme]*

---

### 3. GROUPE CIBLE (0:25 – 0:35)

> « Notre cible : les **PME de la zone UEMOA** — Côte d'Ivoire, Sénégal, Mali et au-delà. Des entrepreneurs qui veulent verdir leur activité mais qui n'ont ni les moyens de payer un consultant ESG, ni les outils pour naviguer seuls dans la complexité des fonds verts. »

---

### 4. PROBLÉMATIQUE ADRESSÉE (0:35 – 0:55)

> « Aujourd'hui, **moins de 10 % des financements climat en Afrique atteignent les PME**, alors qu'elles représentent 80 % de l'emploi. Pourquoi ? Parce que les référentiels ESG sont complexes et en anglais, les consultants coûtent entre 5 000 et 20 000 dollars, et sans historique bancaire, pas de crédit.
>
> ESG Mefali brise ces barrières : l'entrepreneur dialogue en français avec l'IA, obtient son score ESG, trouve les fonds compatibles, et génère ses dossiers — **gratuitement, en quelques minutes**. »

---

### 5. CONCLUSION (0:55 – 1:00)

> « ESG Mefali : la finance verte accessible à ceux qui en ont le plus besoin. Merci. »

*[Sourire, regard caméra]*

---

## Récapitulatif du timing (1 min)

| Segment | Durée | Cumul | Contenu |
|---------|-------|-------|---------|
| Présentation + Pays | 10s | 0:10 | Prénom, rôle, pays |
| Nom + Description | 15s | 0:25 | Ce que fait ESG Mefali |
| Groupe cible | 10s | 0:35 | PME UEMOA |
| Problématique + Solution | 20s | 0:55 | Chiffres clés + proposition de valeur |
| Conclusion | 5s | 1:00 | Phrase de fermeture |

---

## Conseils pour la haute qualité

- **Éclairage** : Face à une fenêtre (lumière naturelle) ou avec une ring light
- **Stabilité** : Trépied ou téléphone posé sur support fixe — pas de main tremblante
- **Montage** : Tu peux insérer des captures d'écran de la plateforme entre 0:10 et 0:25 pour dynamiser
- **Sous-titres** : Ajoute des sous-titres français — ça renforce l'accessibilité et le professionnalisme
- **Habillage** : Un bandeau titre en bas avec « ESG Mefali — Finance verte accessible » pendant les premières secondes
- **Répétition** : Répète 3-4 fois avant d'enregistrer pour tenir les 60s naturellement
