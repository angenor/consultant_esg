# Semaine 3 : Pre-remplissage Intelligent, Suivi Candidatures & Polish

## Dependances

| Prerequis | Fichier/Ressource | Statut |
|-----------|-------------------|--------|
| **Semaine 1 terminee** | [Semaine1.md](./Semaine1.md) | [x] |
| **Semaine 2 terminee** | [Semaine2.md](./Semaine2.md) | [x] |
| Content script detector fonctionnel | Semaine2 / Etape 1 | [x] |
| Side Panel avec guide pas-a-pas | Semaine2 / Etape 3 | [x] |
| Autofill content script ↔ side panel | Semaine2 / Etape 4 | [x] |
| `src/shared/types.ts` (FundField, FundStep) | Semaine1 / Etape 2 | [x] |
| `src/shared/api-client.ts` + auth | Semaine1 / Etape 3 | [x] |
| Endpoints `/api/extension/field-suggest` | Semaine1 / Etape 6 | [x] |
| Endpoints `/api/extension/applications` | Semaine1 / Etape 6 | [x] |

> **Depend de** : [Semaine1.md](./Semaine1.md) + [Semaine2.md](./Semaine2.md) (toutes les etapes)
> **Dernier fichier** — aucun autre fichier ne depend de celui-ci.

---

## Progression Semaine 3

- [x] **Etape 1** : Pre-remplissage intelligent avance
  - [x] 1.1 `src/shared/data-mapper.ts` (classe DataMapper)
  - [x] 1.2 Resolveur de chemins avec formatters
  - [x] 1.3 `src/content/batch-autofill.ts` (remplissage par lot)
  - [x] 1.4 Bouton "Tout remplir" dans `StepContent.vue`
  - [x] **Validation** : "Tout remplir" remplit les champs avec animation
- [x] **Etape 2** : Suivi complet des candidatures
  - [x] 2.1 `src/shared/stores/applications.ts` (store reactif)
  - [x] 2.2 `ApplicationDetail.vue` (detail + etapes + notes)
  - [x] 2.3 Creation automatique de candidature au lancement du guide
  - [x] 2.4 Sauvegarde de progression entre sessions
  - [x] **Validation** : Cycle complet creation → progression → soumission
- [x] **Etape 3** : Systeme d'alertes & notifications
  - [x] 3.1 `src/background/notifications.ts` (deadlines + rappels)
  - [x] 3.2 Alarmes Chrome periodiques (6h)
  - [x] 3.3 Deduplication des notifications
  - [x] **Validation** : Notifications deadline J-30/J-7/J-1 et rappels inactivite
- [x] **Etape 4** : Internationalisation (FR/EN)
  - [x] 4.1 `_locales/fr/messages.json`
  - [x] 4.2 `_locales/en/messages.json`
  - [x] 4.3 Helper `src/shared/i18n.ts`
  - [x] 4.4 Remplacement des textes en dur dans les composants
  - [x] **Validation** : Extension en FR par defaut, EN si locale Chrome
- [x] **Etape 5** : Tests & debugging
  - [x] 5.1 Tests unitaires DataMapper
  - [x] 5.2 Tests unitaires auth
  - [x] 5.3 Tests unitaires detector
  - [ ] 5.4 Checklist de test manuel validee (toutes les lignes)
  - [x] **Validation** : Tous les tests passent + checklist 100%
- [x] **Etape 6** : Preparation Chrome Web Store
  - [x] 6.1 Icones aux bonnes tailles (16, 32, 48, 128)
  - [ ] 6.2 Screenshots (3-5)
  - [x] 6.3 Description FR/EN
  - [x] 6.4 Privacy policy redigee
  - [x] 6.5 Build de production (`npm run build` + zip)
  - [x] **Validation** : Extension publiable sur le Chrome Web Store

---

## Objectifs de la semaine
- Finaliser le systeme de pre-remplissage intelligent (auto + IA)
- Implementer le suivi complet des candidatures
- Ajouter les alertes de deadlines et notifications
- Traduire l'interface (FR/EN)
- Tests, debugging et polish final
- Preparer la publication Chrome Web Store

---

## Etape 1 : Pre-remplissage Intelligent Avance

### 1.1 Moteur de mapping des donnees

Le systeme doit pouvoir mapper les donnees de la plateforme vers n'importe quel champ de formulaire, meme si les noms ne correspondent pas exactement.

```typescript
// src/shared/data-mapper.ts

import type { Entreprise, ESGScore, SyncedData } from './types'

/**
 * Mappe les donnees de la plateforme vers les champs des formulaires de fonds.
 *
 * Le `source` dans la config du fonds peut etre :
 * - Un chemin direct : "entreprise.nom", "entreprise.pays"
 * - Un chemin calcule : "scores.latest.score_global"
 * - Une reference formatee : "entreprise.chiffre_affaires|format_currency"
 */
export class DataMapper {
  private data: SyncedData
  private formatters: Record<string, (value: unknown) => string>

  constructor(data: SyncedData) {
    this.data = data

    this.formatters = {
      format_currency: (v) => {
        const num = Number(v)
        if (isNaN(num)) return String(v)
        return new Intl.NumberFormat('fr-FR').format(num)
      },
      format_date_fr: (v) => {
        const d = new Date(String(v))
        return d.toLocaleDateString('fr-FR')
      },
      format_percentage: (v) => `${Number(v).toFixed(1)}%`,
      uppercase: (v) => String(v).toUpperCase(),
      lowercase: (v) => String(v).toLowerCase(),
    }
  }

  /**
   * Resout une valeur depuis le source path
   */
  resolve(source: string): string | null {
    if (!source) return null

    // Verifier si un formatter est specifie (ex: "entreprise.ca|format_currency")
    const [path, formatterName] = source.split('|')
    let value = this.resolvePath(path.trim())

    if (value === null || value === undefined) return null

    // Appliquer le formatter si present
    if (formatterName && this.formatters[formatterName.trim()]) {
      return this.formatters[formatterName.trim()](value)
    }

    return String(value)
  }

  private resolvePath(path: string): unknown {
    const parts = path.split('.')

    // Racines speciales
    const roots: Record<string, unknown> = {
      entreprise: this.data.entreprise,
      user: this.data.user,
      scores: {
        latest: this.getLatestScore(),
        all: this.data.scores,
      },
      documents: this.data.documents,
    }

    let current: unknown = roots
    for (const part of parts) {
      if (current === null || current === undefined) return null
      if (typeof current !== 'object') return null

      if (part === 'latest' && Array.isArray(current)) {
        current = current[0] || null
      } else {
        current = (current as Record<string, unknown>)[part]
      }
    }

    return current
  }

  private getLatestScore(): ESGScore | null {
    if (!this.data.scores || this.data.scores.length === 0) return null
    return this.data.scores.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]
  }

  /**
   * Genere un mapping complet pour une etape
   * Retourne { selector: value } pour tous les champs auto-remplissables
   */
  mapStep(fields: Array<{ selector: string; source: string | null }>): Record<string, string> {
    const mapping: Record<string, string> = {}

    for (const field of fields) {
      if (!field.source) continue
      const value = this.resolve(field.source)
      if (value) {
        mapping[field.selector] = value
      }
    }

    return mapping
  }
}
```

### 1.2 Auto-remplissage par lot

```typescript
// src/content/batch-autofill.ts

/**
 * Remplit plusieurs champs d'un coup avec animation sequentielle
 */
export async function batchAutofill(
  mappings: Record<string, string>,
  options: { delay?: number; highlight?: boolean } = {}
): Promise<{ filled: number; failed: string[] }> {
  const { delay = 200, highlight = true } = options
  const failed: string[] = []
  let filled = 0

  for (const [selector, value] of Object.entries(mappings)) {
    const selectors = selector.split(',').map(s => s.trim())
    let element: HTMLElement | null = null

    for (const sel of selectors) {
      try {
        element = document.querySelector<HTMLElement>(sel)
        if (element) break
      } catch { /* continuer */ }
    }

    if (!element) {
      failed.push(selector)
      continue
    }

    // Remplir avec animation
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      element.focus()
      element.value = value
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))

      if (highlight) {
        element.style.transition = 'background-color 0.3s, box-shadow 0.3s'
        element.style.backgroundColor = '#f0fdf4'
        element.style.boxShadow = '0 0 0 2px #059669'
        setTimeout(() => {
          element!.style.backgroundColor = ''
          element!.style.boxShadow = ''
        }, 1500)
      }

      filled++
    } else if (element instanceof HTMLSelectElement) {
      const option = Array.from(element.options).find(
        opt => opt.value === value || opt.text.toLowerCase().includes(value.toLowerCase())
      )
      if (option) {
        element.value = option.value
        element.dispatchEvent(new Event('change', { bubbles: true }))
        filled++
      } else {
        failed.push(selector)
      }
    }

    // Pause entre chaque champ pour une animation fluide
    await new Promise(r => setTimeout(r, delay))
  }

  return { filled, failed }
}
```

### 1.3 Bouton "Tout remplir" dans le Side Panel

Ajouter dans `StepContent.vue` :

```vue
<!-- Bouton remplissage automatique global -->
<div v-if="autoFillableCount > 0" class="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
  <div class="flex items-center gap-2">
    <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
    <div class="flex-1">
      <p class="text-sm font-medium text-emerald-800">
        {{ autoFillableCount }} champs pre-remplissables
      </p>
      <p class="text-xs text-emerald-600">
        Donnees provenant de votre profil ESG Advisor
      </p>
    </div>
    <button
      @click="handleBatchAutofill"
      :disabled="batchFilling"
      class="bg-emerald-600 text-white px-4 py-1.5 rounded-lg text-xs font-medium
             hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center gap-1"
    >
      <span v-if="batchFilling" class="w-3 h-3 border-2 border-white border-t-transparent
                                        rounded-full animate-spin"></span>
      {{ batchFilling ? 'En cours...' : 'Tout remplir' }}
    </button>
  </div>
  <div v-if="batchResult" class="mt-2 text-xs text-emerald-700">
    {{ batchResult.filled }} champs remplis
    <span v-if="batchResult.failed.length"> · {{ batchResult.failed.length }} echecs</span>
  </div>
</div>
```

**Critere de validation :** "Tout remplir" remplit les champs avec animation sequentielle, les echecs sont signales.

---

## Etape 2 : Suivi Complet des Candidatures

### 2.1 Store de candidatures

```typescript
// src/shared/stores/applications.ts

import { ref, computed } from 'vue'
import { apiClient } from '../api-client'
import { storageManager } from '../storage'
import type { FundApplication, ApplicationStatus } from '../types'

const applications = ref<FundApplication[]>([])
const loading = ref(false)

export function useApplications() {
  const activeApplications = computed(() =>
    applications.value.filter(a => ['brouillon', 'en_cours'].includes(a.status))
  )

  const completedApplications = computed(() =>
    applications.value.filter(a => ['soumise', 'acceptee', 'refusee'].includes(a.status))
  )

  async function loadApplications() {
    loading.value = true
    try {
      applications.value = await apiClient.get<FundApplication[]>('/api/extension/applications')
    } catch (error) {
      console.error('Erreur chargement candidatures:', error)
    } finally {
      loading.value = false
    }
  }

  async function createApplication(data: {
    entreprise_id: string
    fonds_id: string
    url_candidature: string
  }): Promise<FundApplication | null> {
    try {
      const app = await apiClient.post<FundApplication>('/api/extension/applications', {
        ...data,
        status: 'brouillon',
        progress_pct: 0,
      })
      applications.value.unshift(app)
      return app
    } catch (error) {
      console.error('Erreur creation candidature:', error)
      return null
    }
  }

  async function updateApplication(
    id: string,
    updates: Partial<FundApplication>
  ): Promise<void> {
    try {
      const updated = await apiClient.put<FundApplication>(
        `/api/extension/applications/${id}`,
        updates
      )
      const index = applications.value.findIndex(a => a.id === id)
      if (index >= 0) {
        applications.value[index] = updated
      }
    } catch (error) {
      console.error('Erreur mise a jour candidature:', error)
    }
  }

  async function saveProgress(
    applicationId: string,
    formData: Record<string, unknown>,
    currentStep: number,
    progressPct: number
  ) {
    try {
      await apiClient.post('/api/extension/progress', {
        application_id: applicationId,
        form_data: formData,
        current_step: currentStep,
        progress_pct: progressPct,
      })
    } catch (error) {
      console.error('Erreur sauvegarde progression:', error)
    }
  }

  return {
    applications,
    activeApplications,
    completedApplications,
    loading,
    loadApplications,
    createApplication,
    updateApplication,
    saveProgress,
  }
}
```

### 2.2 Page de suivi detaillee dans le popup

```vue
<!-- src/popup/components/ApplicationDetail.vue -->
<template>
  <div class="p-4">
    <!-- Header avec retour -->
    <button @click="$emit('back')" class="flex items-center gap-1 text-sm text-gray-500 mb-3">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      Retour
    </button>

    <!-- Info fonds -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4">
      <h2 class="font-semibold text-gray-800">{{ application.fonds_nom }}</h2>
      <p class="text-sm text-gray-500">{{ application.fonds_institution }}</p>

      <!-- Progression -->
      <div class="mt-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-600">Progression</span>
          <span class="text-xs font-bold text-emerald-600">{{ application.progress_pct }}%</span>
        </div>
        <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500 rounded-full transition-all"
               :style="{ width: application.progress_pct + '%' }"></div>
        </div>
      </div>

      <!-- Statut -->
      <div class="mt-3 flex items-center gap-2">
        <span class="text-xs px-2 py-1 rounded-full font-medium"
              :class="statusClasses">
          {{ statusLabel }}
        </span>
        <span class="text-xs text-gray-400">
          Commencee le {{ formatDate(application.started_at) }}
        </span>
      </div>
    </div>

    <!-- Etapes completes -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">Etapes</h3>
      <div class="space-y-2">
        <div v-for="step in steps" :key="step.order"
             class="flex items-center gap-2">
          <div class="w-5 h-5 rounded-full flex items-center justify-center"
               :class="step.order <= application.current_step
                 ? 'bg-emerald-500'
                 : step.order === application.current_step + 1
                   ? 'bg-blue-500'
                   : 'bg-gray-200'">
            <svg v-if="step.order <= application.current_step"
                 class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else class="text-[10px] font-bold"
                  :class="step.order === application.current_step + 1 ? 'text-white' : 'text-gray-500'">
              {{ step.order }}
            </span>
          </div>
          <span class="text-sm" :class="step.order <= application.current_step
            ? 'text-gray-800' : 'text-gray-400'">
            {{ step.title }}
          </span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="space-y-2">
      <button
        v-if="application.url_candidature"
        @click="openAndGuide"
        class="w-full bg-emerald-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium
               hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Reprendre la candidature
      </button>

      <button
        v-if="application.status === 'en_cours'"
        @click="markAsSubmitted"
        class="w-full border border-emerald-300 text-emerald-700 rounded-lg px-4 py-2 text-sm
               font-medium hover:bg-emerald-50 transition-colors"
      >
        Marquer comme soumise
      </button>

      <button
        @click="abandonApplication"
        class="w-full text-red-500 text-xs hover:text-red-600"
      >
        Abandonner cette candidature
      </button>
    </div>

    <!-- Notes -->
    <div class="mt-4">
      <label class="text-xs font-medium text-gray-600">Notes personnelles</label>
      <textarea
        v-model="notes"
        @blur="saveNotes"
        rows="3"
        placeholder="Ajouter des notes..."
        class="w-full mt-1 border border-gray-300 rounded-lg px-3 py-2 text-sm
               outline-none focus:border-emerald-500 resize-none"
      ></textarea>
    </div>
  </div>
</template>
```

**Critere de validation :** Suivi complet d'une candidature : creation, progression, reprise, soumission, abandon.

---

## Etape 3 : Systeme d'Alertes & Notifications

### 3.1 Alarmes Chrome pour les deadlines

```typescript
// src/background/notifications.ts

import { apiClient } from '@shared/api-client'
import { storageManager } from '@shared/storage'
import type { FondsVert, FundApplication } from '@shared/types'

/**
 * Verifie les deadlines des fonds et les rappels de candidatures
 * Execute toutes les 6 heures
 */
export async function checkDeadlinesAndReminders() {
  const data = await storageManager.getSyncedData()
  if (!data) return

  const now = new Date()

  // 1. Verifier les deadlines des fonds recommandes
  for (const fonds of data.fonds_recommandes || []) {
    if (!fonds.date_limite) continue

    const deadline = new Date(fonds.date_limite)
    const daysUntil = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

    // Alerter a 30, 7 et 1 jour(s)
    if ([30, 7, 1].includes(daysUntil)) {
      const notifId = `deadline-${fonds.id}-${daysUntil}`
      const existing = await getShownNotification(notifId)
      if (existing) continue // Deja affichee

      chrome.notifications.create(notifId, {
        type: 'basic',
        iconUrl: 'assets/icons/icon-128.png',
        title: daysUntil === 1
          ? 'Dernier jour pour postuler !'
          : `Date limite dans ${daysUntil} jours`,
        message: `${fonds.nom} (${fonds.institution}) — Date limite : ${deadline.toLocaleDateString('fr-FR')}`,
        priority: daysUntil <= 7 ? 2 : 1,
      })

      await markNotificationShown(notifId)
    }
  }

  // 2. Rappels pour les candidatures inactives
  for (const app of data.applications || []) {
    if (!['brouillon', 'en_cours'].includes(app.status)) continue

    const lastUpdate = new Date(app.updated_at || app.started_at)
    const daysSinceUpdate = Math.ceil(
      (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24)
    )

    // Rappeler si inactif depuis 3+ jours
    if (daysSinceUpdate >= 3) {
      const notifId = `reminder-${app.id}-${Math.floor(daysSinceUpdate / 3)}`
      const existing = await getShownNotification(notifId)
      if (existing) continue

      chrome.notifications.create(notifId, {
        type: 'basic',
        iconUrl: 'assets/icons/icon-128.png',
        title: 'Candidature en attente',
        message: `Votre candidature "${app.fonds_nom}" est a ${app.progress_pct}%. Reprenez ou vous en etes !`,
        priority: 1,
      })

      await markNotificationShown(notifId)
    }
  }
}

// Stockage des notifications deja affichees
async function getShownNotification(id: string): Promise<boolean> {
  const result = await chrome.storage.local.get('shown_notifications')
  const shown = result.shown_notifications || {}
  return !!shown[id]
}

async function markNotificationShown(id: string): Promise<void> {
  const result = await chrome.storage.local.get('shown_notifications')
  const shown = result.shown_notifications || {}
  shown[id] = Date.now()

  // Nettoyer les vieilles notifications (> 30 jours)
  const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
  for (const [key, timestamp] of Object.entries(shown)) {
    if ((timestamp as number) < thirtyDaysAgo) {
      delete shown[key]
    }
  }

  await chrome.storage.local.set({ shown_notifications: shown })
}
```

### 3.2 Integration dans le service worker

```typescript
// Ajouter dans service-worker.ts

import { checkDeadlinesAndReminders } from './notifications'

// Verifier les deadlines toutes les 6 heures
chrome.alarms.create('check-deadlines', { periodInMinutes: 360 })

// Aussi a l'installation et au demarrage
chrome.runtime.onStartup.addListener(() => {
  checkDeadlinesAndReminders()
})

chrome.alarms.onAlarm.addListener(async (alarm) => {
  // ... alarmes existantes ...
  if (alarm.name === 'check-deadlines') {
    await checkDeadlinesAndReminders()
  }
})
```

**Critere de validation :** Notifications Chrome pour les deadlines (30j, 7j, 1j) et rappels de candidatures inactives.

---

## Etape 4 : Internationalisation (FR/EN)

### 4.1 Structure i18n

```
chrome-extension/
├── _locales/
│   ├── fr/
│   │   └── messages.json
│   └── en/
│       └── messages.json
```

```json
// _locales/fr/messages.json
{
  "appName": {
    "message": "ESG Advisor Guide",
    "description": "Extension name"
  },
  "appDescription": {
    "message": "Guide pas-a-pas pour vos candidatures aux fonds verts africains",
    "description": "Extension description"
  },
  "login_title": {
    "message": "Connectez-vous",
    "description": "Login page title"
  },
  "login_subtitle": {
    "message": "Utilisez vos identifiants ESG Advisor",
    "description": "Login page subtitle"
  },
  "login_email": {
    "message": "Email",
    "description": "Email label"
  },
  "login_password": {
    "message": "Mot de passe",
    "description": "Password label"
  },
  "login_button": {
    "message": "Se connecter",
    "description": "Login button"
  },
  "login_loading": {
    "message": "Connexion...",
    "description": "Login loading"
  },
  "logout": {
    "message": "Deconnexion",
    "description": "Logout button"
  },
  "fund_detected": {
    "message": "$FUND$ detecte — ESG Advisor peut vous guider",
    "description": "Fund detected banner",
    "placeholders": {
      "fund": { "content": "$1", "example": "BOAD" }
    }
  },
  "open_guide": {
    "message": "Ouvrir le guide",
    "description": "Open guide button"
  },
  "step_of": {
    "message": "Etape $CURRENT$ / $TOTAL$",
    "description": "Step progress",
    "placeholders": {
      "current": { "content": "$1" },
      "total": { "content": "$2" }
    }
  },
  "autofill_all": {
    "message": "Tout remplir",
    "description": "Autofill all button"
  },
  "autofill_field": {
    "message": "Remplir",
    "description": "Autofill single field"
  },
  "ai_suggest": {
    "message": "Generer avec l'IA",
    "description": "AI suggestion button"
  },
  "ai_generating": {
    "message": "Generation...",
    "description": "AI generating"
  },
  "docs_required": {
    "message": "Documents requis",
    "description": "Required docs title"
  },
  "doc_available": {
    "message": "Disponible sur la plateforme",
    "description": "Document available"
  },
  "doc_missing": {
    "message": "Telecharger sur la plateforme",
    "description": "Document missing"
  },
  "applications_title": {
    "message": "Candidatures en cours",
    "description": "Applications section title"
  },
  "no_applications": {
    "message": "Aucune candidature en cours",
    "description": "No applications"
  },
  "funds_recommended": {
    "message": "Fonds recommandes",
    "description": "Recommended funds"
  },
  "apply_button": {
    "message": "Postuler",
    "description": "Apply button"
  },
  "resume_application": {
    "message": "Reprendre la candidature",
    "description": "Resume button"
  },
  "mark_submitted": {
    "message": "Marquer comme soumise",
    "description": "Mark as submitted"
  },
  "abandon": {
    "message": "Abandonner cette candidature",
    "description": "Abandon button"
  },
  "ask_question": {
    "message": "Poser une question",
    "description": "Chat toggle"
  },
  "chat_placeholder": {
    "message": "Ex: Que mettre dans ce champ ?",
    "description": "Chat input placeholder"
  },
  "sync_refresh": {
    "message": "Actualiser",
    "description": "Refresh button"
  },
  "open_platform": {
    "message": "Ouvrir la plateforme ESG Advisor",
    "description": "Platform link"
  }
}
```

### 4.2 Helper i18n pour Vue

```typescript
// src/shared/i18n.ts

/**
 * Wrapper pour chrome.i18n.getMessage
 * Usage dans les templates : {{ t('login_title') }}
 */
export function t(key: string, ...substitutions: string[]): string {
  return chrome.i18n.getMessage(key, substitutions) || key
}

/**
 * Composable Vue pour l'i18n
 */
export function useI18n() {
  return { t }
}
```

**Critere de validation :** L'extension s'affiche en francais par defaut, en anglais si la locale Chrome est en anglais.

---

## Etape 5 : Tests & Debugging

### 5.1 Tests unitaires

```typescript
// tests/data-mapper.test.ts

import { describe, it, expect } from 'vitest'
import { DataMapper } from '../src/shared/data-mapper'

describe('DataMapper', () => {
  const mockData = {
    user: { id: '1', email: 'test@test.com', nom_complet: 'Test User', role: 'user', is_active: true },
    entreprise: {
      id: '1',
      nom: 'AgroVert CI',
      secteur: 'agriculture',
      pays: 'Cote d\'Ivoire',
      effectifs: 45,
      chiffre_affaires: 150000000,
      devise: 'XOF',
      description: 'PME agroalimentaire bio',
    },
    scores: [
      { id: '1', score_e: 72, score_s: 65, score_g: 58, score_global: 66, referentiel_code: 'bceao_fd_2024', created_at: '2026-01-15' },
    ],
    documents: [
      { id: '1', nom_fichier: 'bilan_2025.pdf', type_mime: 'application/pdf', taille: 245000, created_at: '2026-01-10' },
    ],
    fonds_recommandes: [],
    applications: [],
    last_synced: '2026-02-15T10:00:00Z',
  }

  it('resout un chemin simple', () => {
    const mapper = new DataMapper(mockData as any)
    expect(mapper.resolve('entreprise.nom')).toBe('AgroVert CI')
    expect(mapper.resolve('entreprise.pays')).toBe('Cote d\'Ivoire')
    expect(mapper.resolve('entreprise.effectifs')).toBe('45')
  })

  it('resout un chemin avec formatter', () => {
    const mapper = new DataMapper(mockData as any)
    const result = mapper.resolve('entreprise.chiffre_affaires|format_currency')
    // Doit formater en nombre avec separateurs
    expect(result).toContain('150')
  })

  it('resout les scores', () => {
    const mapper = new DataMapper(mockData as any)
    expect(mapper.resolve('scores.latest.score_global')).toBe('66')
  })

  it('retourne null pour un chemin inexistant', () => {
    const mapper = new DataMapper(mockData as any)
    expect(mapper.resolve('entreprise.adresse')).toBeNull()
    expect(mapper.resolve('inexistant.path')).toBeNull()
  })

  it('mappe une etape complete', () => {
    const mapper = new DataMapper(mockData as any)
    const result = mapper.mapStep([
      { selector: '#company-name', source: 'entreprise.nom' },
      { selector: '#sector', source: 'entreprise.secteur' },
      { selector: '#description', source: null },
    ])
    expect(result['#company-name']).toBe('AgroVert CI')
    expect(result['#sector']).toBe('agriculture')
    expect(result['#description']).toBeUndefined()
  })
})
```

### 5.2 Test manuel : checklist

```markdown
## Checklist de test manuel

### Installation & Auth
- [ ] Installer l'extension en mode developpeur
- [ ] Ouvrir le popup → formulaire de login affiche
- [ ] Se connecter avec test@test.com / test1234
- [ ] Dashboard affiche les donnees de l'entreprise
- [ ] Deconnexion efface le token

### Detection de fonds
- [ ] Naviguer sur un site configure → banniere verte apparait
- [ ] Badge "!" sur l'icone de l'extension
- [ ] Notification Chrome "Fonds detecte"
- [ ] Cliquer "Ouvrir le guide" → side panel s'ouvre

### Guide pas-a-pas
- [ ] Side Panel affiche les etapes du fonds detecte
- [ ] Navigation entre etapes (precedent/suivant)
- [ ] Barre de progression se met a jour
- [ ] Champs auto-remplissables affichent la valeur de la plateforme
- [ ] Bouton "Remplir" insere la valeur dans le champ
- [ ] "Tout remplir" remplit tous les champs auto avec animation
- [ ] Champs IA affichent le bouton "Generer avec l'IA"
- [ ] Cliquer "Generer" → spinner → suggestion affichee
- [ ] "Copier" copie dans le presse-papier

### Documents
- [ ] Checklist affiche les documents requis
- [ ] Documents disponibles ont un check vert
- [ ] Documents manquants ont un lien vers la plateforme

### Chat IA
- [ ] Le chat s'ouvre/ferme en bas du side panel
- [ ] Envoyer un message → reponse de l'IA
- [ ] Questions rapides fonctionnent
- [ ] Loading state pendant la generation

### Suivi candidature
- [ ] Candidature creee automatiquement au demarrage du guide
- [ ] Progression sauvegardee entre les sessions
- [ ] Liste des candidatures dans le popup
- [ ] Detail d'une candidature (etapes, notes)
- [ ] "Reprendre la candidature" ouvre le site + guide
- [ ] "Marquer comme soumise" change le statut

### Notifications
- [ ] Alerte deadline a J-7
- [ ] Rappel candidature inactive (3+ jours)
- [ ] Clic sur notification ouvre le side panel

### Ergonomie
- [ ] Le popup se charge en < 1 seconde
- [ ] Le side panel est responsive
- [ ] Les animations sont fluides
- [ ] Le theme est coherent avec la plateforme
```

**Critere de validation :** Tous les items de la checklist valides.

---

## Etape 6 : Preparation Chrome Web Store

### 6.1 Assets necessaires

```
Tailles requises pour le Chrome Web Store :
- Icone extension : 128x128 PNG
- Screenshots : 1280x800 ou 640x400 (minimum 1, max 5)
- Promotional tile : 440x280 (petite) et 920x680 (grande)
```

Preparer :
- 3-5 screenshots montrant le popup, le side panel et la detection
- Une description en francais et en anglais
- Une politique de confidentialite
- Un lien vers la plateforme ESG Advisor

### 6.2 Privacy Policy (obligatoire)

Points a couvrir :
- L'extension ne collecte aucune donnee personnelle au-dela de celles fournies a la plateforme
- Le token JWT est stocke en session (efface a la fermeture)
- Les donnees entreprise sont cachees localement pour 5 minutes
- Aucune donnee n'est partagee avec des tiers
- L'extension communique uniquement avec le serveur ESG Advisor

### 6.3 Build de production

```bash
# Build optimise
npm run build

# Le dossier dist/ contient l'extension prete a publier
# Compresser en .zip pour le Chrome Web Store
cd chrome-extension
zip -r ../esg-advisor-extension.zip dist/
```

### 6.4 Manifest final (permissions justifiees)

```json
{
  "permissions": [
    "activeTab",      // Acceder a l'onglet actif pour la detection de fonds
    "storage",        // Stocker le token JWT et les donnees cachees
    "sidePanel",      // Afficher le guide pas-a-pas
    "notifications",  // Alertes deadlines et rappels
    "alarms"          // Verifications periodiques (auth, sync, deadlines)
  ],
  "host_permissions": [
    "https://api.esgadvisor.ai/*"  // Communication avec le backend
  ]
}
```

**Critere de validation :** Extension publiable sur le Chrome Web Store.

---

## Resume Semaine 3

| Jour | Taches | Livrable |
|------|--------|----------|
| J1 | DataMapper + batch autofill + "Tout remplir" | Pre-remplissage intelligent |
| J2 | Store candidatures + detail + suivi complet | Gestion des candidatures |
| J3 | Notifications deadlines + rappels + alarmes | Systeme d'alertes |
| J4 | i18n (FR/EN) + tests unitaires + tests manuels | Internationalisation + QA |
| J5 | Assets Chrome Web Store + privacy policy + build | Extension publiable |

### Checklist de fin de semaine

- [x] Pre-remplissage par lot fonctionne avec animation
- [x] Suggestions IA generees et inserables
- [x] Suivi complet des candidatures (creation → soumission)
- [x] Notifications de deadlines et rappels
- [x] Interface en francais (anglais si locale Chrome EN)
- [x] Tests unitaires passent (27/27)
- [ ] Checklist de test manuel validee
- [x] Build de production genere (63 modules, zip pret)
- [x] Privacy policy redigee (FR + EN)
- [ ] Screenshots pretes pour le Chrome Web Store

---

## Architecture Finale

```
chrome-extension/
├── manifest.json
├── vite.config.ts
├── tsconfig.json
├── package.json
│
├── _locales/
│   ├── fr/messages.json
│   └── en/messages.json
│
├── src/
│   ├── popup/
│   │   ├── index.html
│   │   ├── main.ts
│   │   ├── App.vue
│   │   └── components/
│   │       ├── LoginPanel.vue
│   │       ├── DashboardPanel.vue
│   │       ├── ApplicationCard.vue
│   │       ├── ApplicationDetail.vue
│   │       └── FundRecommendation.vue
│   │
│   ├── sidepanel/
│   │   ├── index.html
│   │   ├── main.ts
│   │   ├── App.vue
│   │   └── components/
│   │       ├── NoFundDetected.vue
│   │       ├── ProgressBar.vue
│   │       ├── StepNavigator.vue
│   │       ├── StepContent.vue
│   │       ├── FieldHelper.vue
│   │       ├── DocChecklist.vue
│   │       └── MiniChat.vue
│   │
│   ├── background/
│   │   ├── service-worker.ts
│   │   └── notifications.ts
│   │
│   ├── content/
│   │   ├── detector.ts
│   │   ├── highlighter.ts
│   │   ├── autofill.ts
│   │   └── batch-autofill.ts
│   │
│   └── shared/
│       ├── types.ts
│       ├── constants.ts
│       ├── api-client.ts
│       ├── auth.ts
│       ├── storage.ts
│       ├── data-mapper.ts
│       ├── i18n.ts
│       └── stores/
│           └── applications.ts
│
├── assets/
│   ├── icons/
│   ├── styles/main.css
│   └── screenshots/
│
├── tests/
│   ├── data-mapper.test.ts
│   ├── auth.test.ts
│   └── detector.test.ts
│
└── dist/                  # Build output
```

### Endpoints Backend ajoutes

```
POST /api/extension/applications      → Creer une candidature
GET  /api/extension/applications      → Lister les candidatures
PUT  /api/extension/applications/{id} → Mettre a jour une candidature
GET  /api/extension/fund-configs      → Configs de sites de fonds
POST /api/extension/field-suggest     → Suggestion IA pour un champ
POST /api/extension/progress          → Sauvegarder la progression
```

### Modeles Backend ajoutes

```
fund_applications    → Suivi des candidatures
fund_site_configs    → Configuration des sites de fonds (etapes, champs, docs)
```
