# Phase 6 : Interface de suivi des candidatures

## Objectif

Creer une vue dediee dans la plateforme web pour suivre l'avancement de toutes les candidatures aux fonds verts. Cette vue centralise les informations de la plateforme et de l'extension Chrome, offrant une timeline interactive du processus de candidature.

## Etat actuel

### Ce qui existe
- Modele `FundApplication` avec statuts (brouillon, en_cours, soumise, acceptee, refusee, abandonnee)
- Endpoint `/api/extension/applications` pour lister les candidatures
- Extension Chrome : creation automatique de candidature lors de la detection d'un fonds
- Sauvegarde de progression (`form_data`, `current_step`, `progress_pct`)

### Ce qui manque
- **Vue frontend dediee** pour le suivi des candidatures
- **Timeline interactive** montrant les etapes du processus
- **Integration des dossiers generes** avec les candidatures
- **Historique des actions** (document genere, formulaire rempli, etc.)
- **Statistiques** de candidature
- **Notifications dans la plateforme** (pas seulement extension)

## Nouvelles vues frontend

### Vue 1 : Liste des candidatures

**Fichier :** `frontend/src/views/CandidaturesView.vue`

**Layout :**
```
+--------------------------------------------------+
| Mes Candidatures                    [+ Nouvelle]  |
|                                                    |
| Filtres: [Tous statuts v] [Tous fonds v] [Rech..] |
|                                                    |
| +----------------------------------------------+  |
| | BOAD-PME - Facilite Verte         En cours    |  |
| | Via SGCI | Demarre le 12/02/2026              |  |
| | [===========------] 65%                       |  |
| | Prochaine etape : Soumettre documents         |  |
| +----------------------------------------------+  |
|                                                    |
| +----------------------------------------------+  |
| | GCF - Green Climate Fund         Brouillon   |  |
| | Via BOAD (entite accreditee)                  |  |
| | [==-----------------] 15%                     |  |
| | Prochaine etape : Lettre de non-objection AND |  |
| +----------------------------------------------+  |
|                                                    |
| +----------------------------------------------+  |
| | BAD - Adaptation Climatique      Soumise      |  |
| | Appel a propositions sept. 2026               |  |
| | [====================] 100%                   |  |
| | Soumise le 01/09/2026 | Reponse attendue oct. |  |
| +----------------------------------------------+  |
+--------------------------------------------------+
```

**Fonctionnalites :**
- Liste cards avec progression visuelle
- Filtres par statut, fonds, date
- Badge couleur par statut
- Lien vers le detail de chaque candidature
- Bouton "Nouvelle candidature" -> ouvre le chat avec prompt pre-rempli

### Vue 2 : Detail d'une candidature

**Fichier :** `frontend/src/views/CandidatureDetailView.vue`

**Layout :**
```
+--------------------------------------------------+
| < Retour | Candidature BOAD-PME           [Edit]  |
|                                                    |
| +-- Info generales ----+  +-- Statut --------+   |
| | Fonds: BOAD-PME      |  | En cours         |   |
| | Intermediaire: SGCI  |  | 65% complete     |   |
| | Montant: 150M XOF   |  | [=========---]   |   |
| | Mode: Via banque     |  | Depuis 3 sem.    |   |
| +----------------------+  +------------------+   |
|                                                    |
| Timeline du processus                              |
| =================================================  |
| [v] Analyse eligibilite          12/02/2026        |
|     Score ESG: 72/100 - Eligible                   |
|                                                    |
| [v] Dossier prepare               14/02/2026       |
|     6 documents generes [Voir dossier]             |
|                                                    |
| [v] Contact intermediaire         15/02/2026       |
|     SGCI Abidjan contactee                         |
|                                                    |
| [>] Soumission formulaire         En cours          |
|     3/5 etapes completees [Ouvrir extension]       |
|                                                    |
| [ ] Comite de credit              Prevu ~mars       |
|                                                    |
| [ ] Decision et decaissement      Prevu ~avril      |
| =================================================  |
|                                                    |
| Documents du dossier                                |
| +----------------------------------------------+  |
| | Lettre de motivation    DOCX  PDF  12/02/26   |  |
| | Plan d'affaires vert    DOCX  PDF  12/02/26   |  |
| | Rapport ESG complet     PDF        14/02/26   |  |
| | Bilan carbone           PDF        14/02/26   |  |
| +----------------------------------------------+  |
| [Regenerer le dossier] [Telecharger ZIP]           |
|                                                    |
| Historique                                          |
| - 15/02 : Formulaire rempli a 65% via extension    |
| - 14/02 : Dossier de candidature genere (6 docs)  |
| - 12/02 : Candidature creee depuis le chat         |
+--------------------------------------------------+
```

**Fonctionnalites :**
- Timeline interactive avec etapes du processus
- Etapes cochees/en cours/a venir
- Lien vers les documents generes
- Bouton "Ouvrir extension" pour reprendre le remplissage
- Historique des actions
- Possibilite de changer le statut manuellement

## Nouveaux composants Vue

### 1. CandidatureCard.vue

```vue
<!-- Carte resumee d'une candidature dans la liste -->
<template>
  <div class="border rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer"
       @click="$router.push({ name: 'CandidatureDetail', params: { id: candidature.id } })">

    <div class="flex justify-between items-start">
      <div>
        <h3 class="font-semibold text-gray-900">{{ candidature.fonds_nom }}</h3>
        <p class="text-sm text-gray-500">{{ candidature.fonds_institution }}</p>
        <p v-if="intermediaire" class="text-xs text-gray-400 mt-1">
          Via {{ intermediaire.nom }}
        </p>
      </div>
      <StatusBadge :status="candidature.status" />
    </div>

    <!-- Barre de progression -->
    <div class="mt-3">
      <div class="flex justify-between text-xs text-gray-500 mb-1">
        <span>{{ candidature.current_step }}/{{ candidature.total_steps }} etapes</span>
        <span>{{ candidature.progress_pct }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div class="bg-emerald-500 h-2 rounded-full transition-all"
             :style="{ width: candidature.progress_pct + '%' }" />
      </div>
    </div>

    <!-- Prochaine etape -->
    <p v-if="nextStep" class="mt-2 text-xs text-gray-600">
      Prochaine etape : {{ nextStep }}
    </p>
  </div>
</template>
```

### 2. CandidatureTimeline.vue

```vue
<!-- Timeline verticale du processus de candidature -->
<template>
  <div class="relative">
    <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

    <div v-for="(step, index) in steps" :key="index"
         class="relative pl-10 pb-6">

      <!-- Icone de statut -->
      <div class="absolute left-2.5 w-3 h-3 rounded-full border-2"
           :class="stepClasses(step.status)" />

      <!-- Contenu -->
      <div class="bg-white border rounded-lg p-3"
           :class="{ 'border-emerald-200 bg-emerald-50': step.status === 'current' }">
        <div class="flex justify-between items-start">
          <h4 class="text-sm font-medium" :class="step.status === 'done' ? 'text-gray-500' : 'text-gray-900'">
            {{ step.title }}
          </h4>
          <span class="text-xs text-gray-400">{{ step.date || step.estimated }}</span>
        </div>
        <p v-if="step.description" class="text-xs text-gray-500 mt-1">
          {{ step.description }}
        </p>

        <!-- Actions specifiques a l'etape -->
        <div v-if="step.actions" class="mt-2 flex gap-2">
          <button v-for="action in step.actions" :key="action.type"
                  @click="$emit('action', action)"
                  class="text-xs text-emerald-600 hover:underline">
            {{ action.label }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 3. StatusBadge.vue

```vue
<!-- Badge de statut avec couleur adaptee -->
<template>
  <span class="px-2 py-0.5 text-xs font-medium rounded-full"
        :class="statusClasses">
    {{ statusLabel }}
  </span>
</template>

<script setup>
const STATUS_CONFIG = {
  brouillon: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Brouillon' },
  en_cours: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'En cours' },
  soumise: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Soumise' },
  acceptee: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Acceptee' },
  refusee: { bg: 'bg-red-100', text: 'text-red-700', label: 'Refusee' },
  abandonnee: { bg: 'bg-gray-100', text: 'text-gray-400', label: 'Abandonnee' },
}
</script>
```

### 4. DocumentsList.vue (reutilisable)

```vue
<!-- Liste des documents d'un dossier avec liens de telechargement -->
<template>
  <div class="border rounded-lg divide-y">
    <div v-for="doc in documents" :key="doc.type"
         class="flex items-center justify-between px-4 py-3">
      <div>
        <p class="text-sm font-medium text-gray-900">{{ doc.nom }}</p>
        <p class="text-xs text-gray-500">{{ doc.date }}</p>
      </div>
      <div class="flex gap-2">
        <a v-if="doc.url_docx" :href="doc.url_docx"
           class="text-xs text-blue-600 hover:underline">DOCX</a>
        <a v-if="doc.url_pdf" :href="doc.url_pdf"
           class="text-xs text-emerald-600 hover:underline">PDF</a>
      </div>
    </div>
  </div>
</template>
```

## Backend : Nouveaux endpoints

### API Candidatures (pour la plateforme web)

**Fichier :** `backend/app/api/candidatures.py` (nouveau)

```python
# GET /api/candidatures/
#   -> Liste toutes les candidatures de l'utilisateur
#   -> Filtres: status, fonds_id, date_debut, date_fin
#   -> Inclut: fonds info, intermediaire info, dossier info, progression

# GET /api/candidatures/{id}
#   -> Detail complet d'une candidature
#   -> Inclut: timeline, documents, historique

# POST /api/candidatures/
#   -> Creer une candidature depuis la plateforme (pas seulement via extension)
#   -> Body: fonds_id, intermediaire_id, montant_demande, notes

# PUT /api/candidatures/{id}
#   -> Modifier statut, notes, etc.

# GET /api/candidatures/{id}/timeline
#   -> Timeline du processus avec etapes et dates

# GET /api/candidatures/{id}/documents
#   -> Documents generes pour cette candidature

# POST /api/candidatures/{id}/history
#   -> Ajouter une entree dans l'historique
```

### Logique de timeline

La timeline est construite dynamiquement a partir de :
1. Les `acces_details.etapes` du fonds
2. Les `etapes_specifiques` de l'intermediaire
3. Le `current_step` et `progress_pct` de la candidature
4. L'historique des actions

```python
def build_timeline(candidature, fonds, intermediaire):
    etapes = []

    # Etapes generiques du processus
    etapes.append({
        "title": "Analyse d'eligibilite",
        "status": "done" if candidature.progress_pct > 0 else "pending",
        "date": candidature.started_at.strftime("%d/%m/%Y"),
        "description": f"Score ESG: {score}/100",
        "actions": [{"type": "view_score", "label": "Voir le score"}]
    })

    # Etapes du dossier
    if candidature.dossier_id:
        etapes.append({
            "title": "Dossier prepare",
            "status": "done",
            "date": dossier.created_at.strftime("%d/%m/%Y"),
            "description": f"{len(dossier.documents)} documents generes",
            "actions": [{"type": "view_dossier", "label": "Voir dossier"}]
        })

    # Etapes specifiques a l'intermediaire
    for i, etape in enumerate(intermediaire.etapes_specifiques or []):
        status = "done" if i < candidature.current_step else "current" if i == candidature.current_step else "pending"
        etapes.append({
            "title": etape,
            "status": status,
            "actions": [{"type": "open_extension", "label": "Ouvrir extension"}] if status == "current" else []
        })

    return etapes
```

## Routing frontend

**Fichier :** `frontend/src/router/index.ts`

```typescript
// Ajouter les routes :
{
  path: '/candidatures',
  name: 'Candidatures',
  component: () => import('../views/CandidaturesView.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/candidatures/:id',
  name: 'CandidatureDetail',
  component: () => import('../views/CandidatureDetailView.vue'),
  meta: { requiresAuth: true }
}
```

### Navigation

Ajouter dans `AppSidebar.vue` :
```html
<SidebarLink to="/candidatures" icon="document-check">
  Candidatures
</SidebarLink>
```

## Store Pinia

**Fichier :** `frontend/src/stores/candidatures.ts` (nouveau)

```typescript
export const useCandidaturesStore = defineStore('candidatures', () => {
  const candidatures = ref<Candidature[]>([])
  const loading = ref(false)

  async function loadCandidatures(filters?: CandidatureFilters) { ... }
  async function getCandidature(id: string) { ... }
  async function createCandidature(data: CreateCandidatureRequest) { ... }
  async function updateCandidature(id: string, data: UpdateCandidatureRequest) { ... }

  const activeCount = computed(() =>
    candidatures.value.filter(c => ['brouillon', 'en_cours'].includes(c.status)).length
  )

  return { candidatures, loading, activeCount, loadCandidatures, getCandidature, createCandidature, updateCandidature }
})
```

## Integration avec le dashboard

**Fichier :** `frontend/src/views/DashboardView.vue`

Ajouter un widget "Candidatures en cours" :

```vue
<!-- Widget candidatures -->
<div class="rounded-2xl border p-5 bg-white shadow-sm">
  <h2 class="font-semibold text-gray-900 mb-4">Candidatures en cours</h2>

  <div v-if="activeCandidatures.length === 0" class="text-sm text-gray-500 text-center py-4">
    Aucune candidature en cours.
    <router-link to="/chat" class="text-emerald-600">Demandez au conseiller IA</router-link>
  </div>

  <CandidatureCard v-for="c in activeCandidatures.slice(0, 3)" :key="c.id" :candidature="c" />

  <router-link v-if="activeCandidatures.length > 3" to="/candidatures"
               class="block text-center text-sm text-emerald-600 mt-3">
    Voir toutes ({{ activeCandidatures.length }})
  </router-link>
</div>
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `frontend/src/views/CandidaturesView.vue` | Liste des candidatures |
| `frontend/src/views/CandidatureDetailView.vue` | Detail candidature avec timeline |
| `frontend/src/components/candidatures/CandidatureCard.vue` | Carte resumee |
| `frontend/src/components/candidatures/CandidatureTimeline.vue` | Timeline interactive |
| `frontend/src/components/candidatures/StatusBadge.vue` | Badge de statut |
| `frontend/src/components/candidatures/DocumentsList.vue` | Liste documents |
| `frontend/src/stores/candidatures.ts` | Store Pinia |
| `backend/app/api/candidatures.py` | API endpoints |
| `backend/app/schemas/candidature.py` | Schemas Pydantic |

## Fichiers a modifier

| Fichier | Modification |
|---------|--------------|
| `frontend/src/router/index.ts` | Ajouter routes candidatures |
| `frontend/src/components/common/AppSidebar.vue` | Ajouter lien navigation |
| `frontend/src/views/DashboardView.vue` | Widget candidatures en cours |
| `backend/app/main.py` | Inclure le router candidatures |

## Criteres de validation

- [ ] Vue liste affiche toutes les candidatures avec progression
- [ ] Filtres par statut et fonds fonctionnels
- [ ] Vue detail affiche la timeline interactive
- [ ] Timeline reflete l'etat reel (done/current/pending)
- [ ] Documents du dossier telechargeables depuis le detail
- [ ] Bouton "Ouvrir extension" declenche le side panel
- [ ] Widget dashboard affiche les candidatures actives
- [ ] Navigation sidebar inclut "Candidatures"
- [ ] Creation de candidature depuis la plateforme fonctionne
- [ ] Changement de statut manuel fonctionne
- [ ] Historique des actions visible dans le detail
