# 07 - Administration des Skills

## Vue d'ensemble

L'admin peut depuis l'interface :
1. **Voir** tous les skills (builtin + custom)
2. **Créer** de nouveaux skills custom
3. **Modifier** la description, le schéma, le code d'un skill
4. **Activer/Désactiver** un skill (builtin ou custom)
5. **Tester** un skill avec des paramètres fictifs
6. **Supprimer** un skill custom (les builtins sont protégés)

---

## Interface Admin - Liste des Skills

```
/admin/skills

┌──────────────────────────────────────────────────────────────┐
│  Administration des Skills                    [+ Nouveau Skill]│
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Filtres : [Tous ▼]  [Actifs ▼]  [Rechercher...          ]   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ● analyze_document                           builtin     │ │
│  │   Analyse un document uploadé via OCR et extraction      │ │
│  │   Catégorie: esg  │  Version: 3  │  Actif: ✅           │ │
│  │                                    [Modifier] [Désactiver]│ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ ● calculate_esg_score                        builtin     │ │
│  │   Calcule le score ESG à partir des données collectées   │ │
│  │   Catégorie: esg  │  Version: 2  │  Actif: ✅           │ │
│  │                                    [Modifier] [Désactiver]│ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ ● search_green_funds                         builtin     │ │
│  │   Cherche les fonds verts compatibles                    │ │
│  │   Catégorie: finance  │  Version: 1  │  Actif: ✅       │ │
│  │                                    [Modifier] [Désactiver]│ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ ○ verifier_conformite_bceao                  custom      │ │
│  │   Vérifie la conformité aux directives BCEAO             │ │
│  │   Catégorie: esg  │  Version: 1  │  Actif: ❌           │ │
│  │                          [Modifier] [Tester] [Supprimer] │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

● = builtin (non supprimable)
○ = custom (supprimable)
```

## Interface Admin - Création/Édition d'un Skill

```
/admin/skills/new       → Création
/admin/skills/:id/edit  → Édition

┌──────────────────────────────────────────────────────────────┐
│  Créer un nouveau Skill                                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Nom technique *          [verifier_conformite_bceao      ]   │
│  (lettres, _, pas d'espace)                                   │
│                                                                │
│  Description *                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Vérifie si l'entreprise respecte les directives BCEAO   │ │
│  │ sur la finance durable. Consulte la base réglementaire  │ │
│  │ et compare avec le profil ESG de l'entreprise.          │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ⚠️ Cette description est envoyée au LLM. Soyez précis.    │
│                                                                │
│  Catégorie *              [esg           ▼]                   │
│                           (esg / finance / carbon /            │
│                            report / utils)                     │
│                                                                │
│  ─── Paramètres d'entrée (JSON Schema) ──────────────────── │
│                                                                │
│  Mode : ○ Visuel   ● JSON                                    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ {                                                         │ │
│  │   "type": "object",                                      │ │
│  │   "properties": {                                        │ │
│  │     "entreprise_id": {                                   │ │
│  │       "type": "string",                                  │ │
│  │       "description": "ID de l'entreprise à vérifier"     │ │
│  │     },                                                   │ │
│  │     "type_verification": {                               │ │
│  │       "type": "string",                                  │ │
│  │       "enum": ["reporting", "taxonomie",                 │ │
│  │                "risques_climatiques"],                    │ │
│  │       "description": "Type de vérification BCEAO"        │ │
│  │     }                                                    │ │
│  │   },                                                     │ │
│  │   "required": ["entreprise_id"]                          │ │
│  │ }                                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ⚠️ Ce schéma définit les paramètres que le LLM peut          │
│     envoyer au skill.                                         │
│                                                                │
│  ─── Code Python ──────────────────────────────────────────  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ # Éditeur CodeMirror (coloration Python)                 │ │
│  │                                                           │ │
│  │ async def execute(params, context):                      │ │
│  │     """                                                   │ │
│  │     params: dict avec les paramètres définis ci-dessus   │ │
│  │     context: dict avec db, rag, entreprise_id            │ │
│  │     Retourne: dict avec les résultats                    │ │
│  │     """                                                   │ │
│  │     entreprise_id = params["entreprise_id"]              │ │
│  │     type_verif = params.get("type_verification",         │ │
│  │                             "reporting")                  │ │
│  │                                                           │ │
│  │     # Chercher dans la base réglementaire                │ │
│  │     reglements = await context["rag"].search(            │ │
│  │         query=f"BCEAO {type_verif} finance durable",     │ │
│  │         category="regulation",                            │ │
│  │         top_k=5                                           │ │
│  │     )                                                     │ │
│  │                                                           │ │
│  │     # Récupérer le dernier score ESG                     │ │
│  │     score = await context["db"].fetch_one(               │ │
│  │         """SELECT * FROM esg_scores                       │ │
│  │            WHERE entreprise_id = $1                       │ │
│  │            ORDER BY created_at DESC LIMIT 1""",          │ │
│  │         entreprise_id                                     │ │
│  │     )                                                     │ │
│  │                                                           │ │
│  │     return {                                              │ │
│  │         "type_verification": type_verif,                  │ │
│  │         "references": [r["contenu"]                       │ │
│  │                        for r in reglements],              │ │
│  │         "score_actuel": score["score_global"]             │ │
│  │                         if score else None,               │ │
│  │         "conforme": score and                             │ │
│  │                     score["score_global"] >= 50,          │ │
│  │     }                                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Fonctions disponibles dans context :                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ context["db"].fetch_one(sql, *args) → dict               │ │
│  │ context["db"].fetch_all(sql, *args) → list[dict]         │ │
│  │ context["rag"].search(query, category, top_k) → list     │ │
│  │ json, datetime, math, re → modules Python autorisés      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ─── Test ─────────────────────────────────────────────────  │
│                                                                │
│  Paramètres de test (JSON) :                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ {                                                         │ │
│  │   "entreprise_id": "test-uuid-123",                      │ │
│  │   "type_verification": "reporting"                        │ │
│  │ }                                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                           [🧪 Tester le Skill]│
│                                                                │
│  Résultat du test :                                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ✅ Succès (230ms)                                        │ │
│  │ {                                                         │ │
│  │   "type_verification": "reporting",                       │ │
│  │   "references": ["La BCEAO exige...", "Selon la..."],    │ │
│  │   "score_actuel": 62.5,                                   │ │
│  │   "conforme": true                                        │ │
│  │ }                                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│                              [Annuler]  [Sauvegarder le Skill] │
└──────────────────────────────────────────────────────────────┘
```

## Mode Visuel du JSON Schema (optionnel, simplifie la saisie)

```
┌──────────────────────────────────────────────────────────────┐
│  Paramètres d'entrée                           [+ Paramètre] │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Nom: [entreprise_id     ]  Type: [string ▼]  Requis: [✅]│ │
│  │ Description: [ID de l'entreprise à vérifier             ] │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ Nom: [type_verification ]  Type: [string ▼]  Requis: [❌]│ │
│  │ Description: [Type de vérification BCEAO                ] │ │
│  │ Valeurs possibles: [reporting, taxonomie, risques_clim. ] │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Composant Vue.js - SkillForm

```vue
<!-- === frontend/src/components/admin/SkillForm.vue === -->

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">

    <!-- Nom -->
    <div>
      <label class="block text-sm font-medium">Nom technique</label>
      <input v-model="form.nom" type="text" required
             pattern="[a-z_]+"
             placeholder="mon_nouveau_skill"
             class="mt-1 w-full border rounded px-3 py-2" />
      <p class="text-xs text-gray-500 mt-1">
        Lettres minuscules et underscores uniquement
      </p>
    </div>

    <!-- Description -->
    <div>
      <label class="block text-sm font-medium">
        Description (envoyée au LLM)
      </label>
      <textarea v-model="form.description" rows="3" required
                class="mt-1 w-full border rounded px-3 py-2"
                placeholder="Décrivez précisément ce que fait ce skill..." />
    </div>

    <!-- Catégorie -->
    <div>
      <label class="block text-sm font-medium">Catégorie</label>
      <select v-model="form.category" class="mt-1 border rounded px-3 py-2">
        <option value="esg">ESG</option>
        <option value="finance">Finance</option>
        <option value="carbon">Carbone</option>
        <option value="report">Rapports</option>
        <option value="utils">Utilitaires</option>
      </select>
    </div>

    <!-- JSON Schema -->
    <div>
      <label class="block text-sm font-medium">
        Paramètres d'entrée (JSON Schema)
      </label>
      <div class="flex gap-2 mt-1 mb-2">
        <button type="button" @click="schemaMode = 'visual'"
                :class="schemaMode === 'visual' ? 'bg-blue-100' : ''">
          Visuel
        </button>
        <button type="button" @click="schemaMode = 'json'"
                :class="schemaMode === 'json' ? 'bg-blue-100' : ''">
          JSON
        </button>
      </div>

      <!-- Mode visuel -->
      <SchemaBuilder v-if="schemaMode === 'visual'"
                     v-model="form.input_schema" />

      <!-- Mode JSON -->
      <CodeEditor v-else
                  v-model="inputSchemaJson"
                  language="json"
                  :height="200" />
    </div>

    <!-- Code Python -->
    <div>
      <label class="block text-sm font-medium">
        Code Python du handler
      </label>
      <CodeEditor v-model="form.handler_code"
                  language="python"
                  :height="400"
                  placeholder="async def execute(params, context):
    # Votre code ici
    return {}" />

      <!-- Documentation inline -->
      <details class="mt-2 text-sm text-gray-600">
        <summary class="cursor-pointer">Fonctions disponibles</summary>
        <ul class="mt-1 ml-4 list-disc">
          <li><code>context["db"].fetch_one(sql, *args)</code> → un résultat</li>
          <li><code>context["db"].fetch_all(sql, *args)</code> → liste</li>
          <li><code>context["rag"].search(query, category, top_k)</code> → recherche sémantique</li>
          <li>Modules : json, datetime, math, re</li>
        </ul>
      </details>
    </div>

    <!-- Zone de test -->
    <div class="border rounded p-4 bg-gray-50">
      <h3 class="font-medium mb-2">Tester le skill</h3>
      <CodeEditor v-model="testParams"
                  language="json"
                  :height="100"
                  placeholder='{"entreprise_id": "test-123"}' />
      <button type="button" @click="testSkill"
              class="mt-2 px-4 py-2 bg-yellow-500 text-white rounded">
        Tester
      </button>

      <div v-if="testResult" class="mt-2 p-3 rounded"
           :class="testResult.success ? 'bg-green-50' : 'bg-red-50'">
        <p class="font-medium">
          {{ testResult.success ? '✅ Succès' : '❌ Erreur' }}
          ({{ testResult.duration }}ms)
        </p>
        <pre class="mt-1 text-sm overflow-auto">{{
          JSON.stringify(testResult.success ? testResult.result : testResult.error, null, 2)
        }}</pre>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-3">
      <button type="button" @click="$router.back()"
              class="px-4 py-2 border rounded">
        Annuler
      </button>
      <button type="submit"
              class="px-4 py-2 bg-green-600 text-white rounded">
        {{ isEdit ? 'Sauvegarder' : 'Créer le Skill' }}
      </button>
    </div>
  </form>
</template>
```

## Workflow Admin Complet

```
1. L'admin identifie un besoin
   Ex: "Je veux que l'agent puisse vérifier la conformité BCEAO"

2. Il va dans /admin/skills → clique "Nouveau Skill"

3. Il remplit :
   - Nom : verifier_conformite_bceao
   - Description : (ce que le LLM lira pour savoir quand utiliser ce skill)
   - Paramètres : JSON Schema des inputs
   - Code : fonction Python execute()

4. Il teste avec des paramètres fictifs → vérifie que ça marche

5. Il sauvegarde → le skill est actif immédiatement

6. Prochain message utilisateur :
   - Le Skill Registry charge le nouveau skill depuis la BDD
   - Le LLM le voit dans ses tools disponibles
   - Si pertinent, le LLM l'appelle automatiquement

7. Si le skill a un bug :
   - L'admin va dans Modifier
   - Corrige le code
   - Re-teste
   - Sauvegarde → version incrémentée
```

## Sécurité Admin - Skills

| Action | Builtin | Custom |
|--------|---------|--------|
| Voir | ✅ | ✅ |
| Activer/Désactiver | ✅ | ✅ |
| Modifier description | ✅ | ✅ |
| Modifier input_schema | ✅ | ✅ |
| Modifier code | ❌ (dans le code source) | ✅ |
| Supprimer | ❌ | ✅ |
| Tester | ✅ | ✅ |

---

## Administration des Référentiels ESG

### Pourquoi c'est nécessaire

Le score ESG n'est pas universel. Chaque institution (BCEAO, GCF, IFC, BAD...)
utilise sa propre grille avec des critères et des pondérations différentes.
L'admin doit pouvoir créer et ajuster ces grilles sans toucher au code.

### Interface Admin - Liste des Référentiels

```
/admin/referentiels

┌──────────────────────────────────────────────────────────────┐
│  Référentiels ESG                      [+ Nouveau Référentiel]│
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Filtres : [Toutes régions ▼]  [Actifs ▼]                    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ BCEAO Finance Durable 2024                                │ │
│  │ Institution: BCEAO  │  Région: UEMOA  │  Actif: ✅       │ │
│  │ E: 40%  S: 30%  G: 30%  │  Méthode: Moyenne pondérée    │ │
│  │ 12 critères  │  Lié à 3 fonds                             │ │
│  │                              [Modifier] [Simuler] [Désact]│ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ Green Climate Fund Assessment                             │ │
│  │ Institution: GCF  │  Région: International  │  Actif: ✅  │ │
│  │ E: 60%  S: 25%  G: 15%  │  Méthode: Seuils minimum      │ │
│  │ 8 critères  │  Lié à 1 fonds                              │ │
│  │                              [Modifier] [Simuler] [Désact]│ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ IFC Performance Standards                                 │ │
│  │ Institution: IFC  │  Région: International  │  Actif: ✅  │ │
│  │ E: 35%  S: 40%  G: 25%  │  Méthode: Moyenne pondérée    │ │
│  │ 15 critères  │  Lié à 2 fonds                             │ │
│  │                              [Modifier] [Simuler] [Désact]│ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Interface Admin - Éditeur de Grille ESG

```
/admin/referentiels/new      → Création
/admin/referentiels/:id      → Modification

┌──────────────────────────────────────────────────────────────┐
│  Créer un Référentiel ESG                                     │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Nom *                  [BCEAO Finance Durable 2024        ]  │
│  Code technique *       [bceao_fd_2024                     ]  │
│  Institution            [BCEAO                             ]  │
│  Région                 [UEMOA        ▼]                      │
│  Description            [Référentiel basé sur les           ] │
│                         [directives BCEAO 2024...           ] │
│                                                                │
│  Méthode d'agrégation * [Moyenne pondérée ▼]                  │
│                         (Moyenne pondérée / Seuils minimum)   │
│                                                                │
│  ─── Pilier : Environnement ──── Poids global : [0.40] ──── │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [+ Ajouter critère]                                       │ │
│  │                                                            │ │
│  │ 1. Émissions de gaz à effet de serre                      │ │
│  │    ID: [emissions_carbone  ]  Poids: [0.30]               │ │
│  │    Type: [Quantitatif ▼]   Unité: [tCO2e/an]             │ │
│  │    Seuils:                                                 │ │
│  │      Excellent: max [50  ] → score [100]                  │ │
│  │      Bon:       max [200 ] → score [70 ]                  │ │
│  │      Moyen:     max [500 ] → score [40 ]                  │ │
│  │      Faible:    min [500 ] → score [10 ]                  │ │
│  │    Question: [Estimez vos émissions annuelles de CO2    ] │ │
│  │                                              [Supprimer]  │ │
│  │ ──────────────────────────────────────────────────────── │ │
│  │ 2. Gestion et valorisation des déchets                    │ │
│  │    ID: [gestion_dechets    ]  Poids: [0.25]               │ │
│  │    Type: [Qualitatif ▼]                                   │ │
│  │    Options:                                                │ │
│  │      [Politique formelle + recyclage actif ] → [100]      │ │
│  │      [Tri sélectif en place               ] → [70 ]      │ │
│  │      [Collecte basique                    ] → [40 ]      │ │
│  │      [Aucune gestion structurée           ] → [10 ]      │ │
│  │    Question: [Comment gérez-vous vos déchets ?          ] │ │
│  │                                              [Supprimer]  │ │
│  │ ──────────────────────────────────────────────────────── │ │
│  │ 3. ...                                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│  Somme des poids : 1.00 ✅                                    │
│                                                                │
│  ─── Pilier : Social ──────────── Poids global : [0.30] ──── │
│  (même structure que ci-dessus)                               │
│                                                                │
│  ─── Pilier : Gouvernance ──────── Poids global : [0.30] ─── │
│  (même structure que ci-dessus)                               │
│                                                                │
│  Somme des poids globaux : 1.00 ✅                            │
│                                                                │
│  ─── Simuler un scoring ─────────────────────────────────── │
│                                                                │
│  Données test (JSON) :                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ {                                                         │ │
│  │   "emissions_carbone": 350,                               │ │
│  │   "gestion_dechets": "Tri sélectif en place",            │ │
│  │   "energie_renouvelable": 25                              │ │
│  │ }                                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                            [Simuler le scoring]│
│                                                                │
│  Résultat simulation :                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Score Global : 58.5/100 (Niveau: À améliorer)            │ │
│  │                                                            │ │
│  │ E: 52.0/100  │  S: 65.0/100  │  G: 60.0/100             │ │
│  │                                                            │ │
│  │ Détail Environnement :                                    │ │
│  │   emissions_carbone    40/100  ⚠ partiel   (350 tCO2e)   │ │
│  │   gestion_dechets      70/100  ✅ conforme               │ │
│  │   energie_renouvelable 40/100  ⚠ partiel   (25%)        │ │
│  │   ressource_eau         0/100  ❌ manquant               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│                              [Annuler]  [Sauvegarder]         │
└──────────────────────────────────────────────────────────────┘
```

### Lien Fonds → Référentiel

Quand l'admin crée ou modifie un fonds vert, il peut associer un référentiel :

```
/admin/fonds/:id

┌──────────────────────────────────────────────────────────────┐
│  Modifier le Fonds : Fonds Vert pour le Climat               │
│                                                                │
│  ...                                                          │
│  Référentiel ESG associé : [Green Climate Fund Assessment ▼]  │
│                             (Aucun / BCEAO / GCF / IFC / ...) │
│  ...                                                          │
│                                                                │
│  → L'agent scorera automatiquement l'entreprise selon         │
│    ce référentiel quand il évalue l'éligibilité à ce fonds    │
└──────────────────────────────────────────────────────────────┘
```
