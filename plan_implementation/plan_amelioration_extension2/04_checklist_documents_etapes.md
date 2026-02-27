# Phase 4 : Checklist documents & etapes interactives

## Dependances

**Prerequis :** Phase 3 (le guide adaptatif doit exister pour y integrer la checklist)
**Bloque :** Rien (derniere phase)

## Progression

- [x] 4.1 Enrichir la checklist documents avec statut temps-reel
- [x] 4.2 Lien direct vers le telechargement/generation de documents sur la plateforme
- [x] 4.3 Validation automatique des documents (format, taille, completude)
- [x] 4.4 Etapes interactives avec persistance de l'etat
- [x] 4.5 Barre de progression enrichie (documents + etapes + pre-etapes)
- [x] 4.6 Tests unitaires de la checklist et des etapes

## Objectif

Transformer la checklist de documents et le suivi d'etapes en outils interactifs et connectes a la plateforme. L'utilisateur doit voir en temps reel quels documents sont prets, lesquels manquent, et pouvoir agir directement depuis l'extension.

## Etat actuel

### Ce qui existe
- `DocChecklist.vue` : affiche les documents requis avec statut disponible/manquant
- Matching par nom de fichier et type MIME entre `required_docs` et `availableDocs`
- Lien vers `/documents` de la plateforme pour telecharger les manquants
- `acces_details.documents_requis` dans la reponse API (liste de noms)
- `FundSiteConfig.required_docs[]` avec `name`, `type`, `format`, `description`, `available_on_platform`, `document_id`

### Ce qui manque
- **Statut temps-reel** : la checklist ne se rafraichit pas quand l'utilisateur telecharge un document
- **Actions directes** : pas de bouton "Generer" pour les documents auto-generables (rapport ESG, fiche entreprise)
- **Validation** : aucune verification du format, de la taille ou de la completude
- **Persistance etapes** : les etapes cochees ne sont pas sauvegardees entre les sessions
- **Progression globale** : la barre de progression ne tient compte que des etapes, pas des documents ni des pre-etapes

## Implementation detaillee

### 4.1 Checklist documents avec statut temps-reel

**Fichier :** `chrome-extension/src/sidepanel/components/DocChecklist.vue`

Refactoriser pour ajouter :
- Rafraichissement automatique quand l'extension detecte un changement
- 3 etats par document : `ready` (disponible), `missing` (manquant), `generating` (en cours)
- Icones de statut distinctes

```vue
<template>
  <div class="px-4 py-4 border-t border-gray-200">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-800 flex items-center gap-2">
        <DocumentIcon />
        Documents requis
        <span class="text-xs text-gray-400">{{ readyCount }}/{{ docs.length }}</span>
      </h3>
      <button @click="refreshDocs" class="text-xs text-emerald-600 hover:text-emerald-700">
        Actualiser
      </button>
    </div>

    <!-- Barre de progression documents -->
    <div class="w-full bg-gray-200 rounded-full h-1.5 mb-3">
      <div class="bg-emerald-500 h-1.5 rounded-full transition-all"
           :style="{ width: `${(readyCount / docs.length) * 100}%` }">
      </div>
    </div>

    <div class="space-y-2">
      <DocItem
        v-for="doc in docs"
        :key="doc.name"
        :doc="doc"
        @generate="handleGenerate(doc)"
        @upload="handleUploadRedirect(doc)"
      />
    </div>

    <!-- Message si tout est pret -->
    <div v-if="readyCount === docs.length" class="mt-3 bg-emerald-50 rounded-lg p-3 text-center">
      <p class="text-sm text-emerald-700 font-medium">Tous les documents sont prets !</p>
    </div>
  </div>
</template>
```

**Fichier a creer :** `chrome-extension/src/sidepanel/components/DocItem.vue`

Composant unitaire pour un document avec les 3 etats et actions :

```vue
<template>
  <div class="flex items-start gap-2 p-2 rounded-lg" :class="bgClass">
    <!-- Icone statut -->
    <StatusIcon :status="doc.status" />

    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium" :class="textClass">{{ doc.name }}</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 text-gray-500">
          {{ doc.format }}
        </span>
      </div>
      <p class="text-[11px] text-gray-500 mt-0.5">{{ doc.description }}</p>

      <!-- Actions selon statut -->
      <div v-if="doc.status === 'missing'" class="flex gap-2 mt-1.5">
        <button v-if="doc.can_generate"
                @click="$emit('generate')"
                class="text-[11px] text-emerald-600 hover:text-emerald-700 font-medium">
          Generer automatiquement
        </button>
        <button @click="$emit('upload')"
                class="text-[11px] text-blue-600 hover:text-blue-700 font-medium">
          Telecharger sur la plateforme
        </button>
      </div>

      <!-- Spinner generation -->
      <div v-if="doc.status === 'generating'" class="flex items-center gap-1 mt-1">
        <span class="w-3 h-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></span>
        <span class="text-[11px] text-emerald-600">Generation en cours...</span>
      </div>

      <!-- Validation warnings -->
      <div v-if="doc.warnings?.length" class="mt-1">
        <p v-for="w in doc.warnings" :key="w" class="text-[11px] text-amber-600">
          ⚠ {{ w }}
        </p>
      </div>
    </div>
  </div>
</template>
```

### 4.2 Actions directes (generation + telechargement)

**Fichier :** `chrome-extension/src/sidepanel/components/DocChecklist.vue`

```typescript
// Documents auto-generables depuis la plateforme
const GENERATABLE_DOCS = [
  'rapport_esg',          // Genere depuis les scores ESG
  'fiche_entreprise',     // Genere depuis le profil entreprise
  'bilan_carbone',        // Genere depuis CarbonFootprint
  'plan_action_esg',      // Genere depuis ActionPlan
]

async function handleGenerate(doc: DocWithStatus) {
  doc.status = 'generating'
  try {
    // Appeler l'API plateforme pour generer le document
    await apiClient.post(`/api/documents/generate`, {
      type: doc.type,
      entreprise_id: companyData.value?.entreprise?.id,
    })
    // Rafraichir la liste des documents
    await refreshDocs()
  } catch (error) {
    doc.status = 'missing'
    console.error('Erreur generation document:', error)
  }
}

function handleUploadRedirect(doc: DocWithStatus) {
  // Ouvrir la page documents de la plateforme avec un filtre pre-rempli
  const url = `http://localhost:5173/documents?upload=true&type=${doc.type}`
  chrome.tabs.create({ url })
}
```

### 4.3 Validation automatique des documents

**Fichier a creer :** `chrome-extension/src/shared/doc-validator.ts`

```typescript
export interface DocValidation {
  valid: boolean
  warnings: string[]
}

export function validateDocument(
  doc: RequiredDoc,
  available: DocumentSummary | null,
): DocValidation {
  const warnings: string[] = []

  if (!available) {
    return { valid: false, warnings: ['Document non trouve'] }
  }

  // Verification format
  const expectedFormats = doc.format.split(',').map(f => f.trim().toLowerCase())
  const actualFormat = available.type_mime?.split('/')[1]?.toLowerCase() || ''
  if (expectedFormats.length && !expectedFormats.some(f => actualFormat.includes(f))) {
    warnings.push(`Format attendu : ${doc.format}, recu : ${actualFormat}`)
  }

  // Verification taille (max 10 Mo par defaut)
  const maxSize = 10 * 1024 * 1024
  if (available.taille > maxSize) {
    warnings.push(`Fichier trop volumineux (${(available.taille / 1024 / 1024).toFixed(1)} Mo, max 10 Mo)`)
  }

  // Verification anciennete (alerte si > 6 mois)
  const sixMonths = 180 * 24 * 60 * 60 * 1000
  if (Date.now() - new Date(available.created_at).getTime() > sixMonths) {
    warnings.push('Document date de plus de 6 mois — verifiez sa validite')
  }

  return { valid: warnings.length === 0, warnings }
}
```

### 4.4 Etapes interactives avec persistance

**Fichier :** `chrome-extension/src/sidepanel/App.vue`

Ajouter la persistance des pre-etapes et etapes cochees via `chrome.storage.local` :

```typescript
const preStepCompleted = ref<boolean[]>([])

// Charger l'etat sauvegarde
onMounted(async () => {
  const stored = await chrome.storage.local.get(`steps_${fundConfig.value?.id}`)
  if (stored) {
    preStepCompleted.value = stored.preSteps || []
    currentStep.value = stored.currentStep || 0
  }
})

// Sauvegarder a chaque changement
watch([preStepCompleted, currentStep], async () => {
  if (!fundConfig.value) return
  await chrome.storage.local.set({
    [`steps_${fundConfig.value.id}`]: {
      preSteps: preStepCompleted.value,
      currentStep: currentStep.value,
    },
  })
  // Sauvegarder aussi cote backend
  saveProgress()
}, { deep: true })

function togglePreStep(index: number) {
  preStepCompleted.value[index] = !preStepCompleted.value[index]
}
```

### 4.5 Barre de progression enrichie

**Fichier :** `chrome-extension/src/sidepanel/components/ProgressBar.vue`

Modifier pour integrer 3 sources de progression :

```vue
<template>
  <div class="px-4 py-3 bg-white border-b border-gray-100">
    <div class="flex items-center justify-between mb-1">
      <span class="text-xs font-medium text-gray-600">Progression globale</span>
      <span class="text-xs font-bold" :class="progressColor">{{ globalProgress }}%</span>
    </div>

    <!-- Barre composite -->
    <div class="w-full bg-gray-200 rounded-full h-2 flex overflow-hidden">
      <!-- Pre-etapes (bleu) -->
      <div class="bg-blue-400 h-2 transition-all"
           :style="{ width: `${preStepWidth}%` }" />
      <!-- Documents (amber) -->
      <div class="bg-amber-400 h-2 transition-all"
           :style="{ width: `${docWidth}%` }" />
      <!-- Etapes formulaire (emerald) -->
      <div class="bg-emerald-500 h-2 transition-all"
           :style="{ width: `${stepWidth}%` }" />
    </div>

    <!-- Legende -->
    <div class="flex gap-3 mt-1.5">
      <span v-if="preStepCount > 0" class="flex items-center gap-1 text-[10px] text-gray-500">
        <span class="w-2 h-2 rounded-full bg-blue-400"></span>
        Pre-etapes {{ preStepDone }}/{{ preStepCount }}
      </span>
      <span class="flex items-center gap-1 text-[10px] text-gray-500">
        <span class="w-2 h-2 rounded-full bg-amber-400"></span>
        Documents {{ docReady }}/{{ docTotal }}
      </span>
      <span class="flex items-center gap-1 text-[10px] text-gray-500">
        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        Etapes {{ currentStep }}/{{ totalSteps }}
      </span>
    </div>
  </div>
</template>
```

```typescript
const props = defineProps<{
  currentStep: number
  totalSteps: number
  preStepDone?: number
  preStepCount?: number
  docReady?: number
  docTotal?: number
}>()

const globalProgress = computed(() => {
  const total = (props.preStepCount || 0) + (props.docTotal || 0) + props.totalSteps
  if (total === 0) return 0
  const done = (props.preStepDone || 0) + (props.docReady || 0) + props.currentStep
  return Math.round((done / total) * 100)
})
```

### 4.6 Tests unitaires

**Fichier :** `chrome-extension/tests/doc-checklist.test.ts`

```typescript
// Cas a tester :
// - validateDocument() : format PDF correct → valid=true, warnings=[]
// - validateDocument() : format incorrect → valid=false, warning format
// - validateDocument() : fichier > 10 Mo → warning taille
// - validateDocument() : document > 6 mois → warning anciennete
// - DocChecklist : readyCount correct avec mix disponible/manquant
// - DocChecklist : document generable affiche le bouton "Generer"
// - ProgressBar : calcul globalProgress avec pre-etapes + docs + etapes
// - ProgressBar : 0% si rien fait, 100% si tout complete
// - Persistance : etat restaure depuis chrome.storage.local
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `chrome-extension/src/sidepanel/components/DocItem.vue` | Composant unitaire document avec actions |
| `chrome-extension/src/shared/doc-validator.ts` | Validation format/taille/anciennete des documents |
| `chrome-extension/tests/doc-checklist.test.ts` | Tests unitaires checklist et progression |

## Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `chrome-extension/src/sidepanel/components/DocChecklist.vue` | Statut temps-reel, actions, progression |
| `chrome-extension/src/sidepanel/components/ProgressBar.vue` | Progression composite (pre-etapes + docs + etapes) |
| `chrome-extension/src/sidepanel/App.vue` | Persistance etapes, props enrichies |
| `chrome-extension/src/shared/types.ts` | Types DocWithStatus, DocValidation |

## Criteres de validation

- [x] La checklist se met a jour quand un document est ajoute sur la plateforme
- [x] Le bouton "Generer" fonctionne pour les documents auto-generables
- [x] Les warnings de validation (format, taille, anciennete) s'affichent
- [x] Les etapes cochees sont persistees entre les sessions
- [x] La barre de progression integre les 3 sources (pre-etapes, docs, etapes)
- [x] Tests unitaires passent (74 tests, 6 fichiers)
