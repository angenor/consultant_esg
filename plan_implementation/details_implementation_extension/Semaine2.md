# Semaine 2 : Detection de Sites, Side Panel & Guide Pas-a-Pas

## Dependances

| Prerequis | Fichier/Ressource | Statut |
|-----------|-------------------|--------|
| **Semaine 1 terminee** | [Semaine1.md](./Semaine1.md) | [ ] |
| Extension installable dans Chrome | `chrome://extensions` → charger `dist/` | [ ] |
| Popup fonctionnel avec login | Semaine1 / Etape 5 | [ ] |
| Endpoints `/api/extension/*` operationnels | Semaine1 / Etape 6 | [ ] |
| Configs de fonds en base de donnees | Semaine1 / Etape 7 | [ ] |
| `src/shared/types.ts` complet | Semaine1 / Etape 2 | [ ] |
| `src/shared/api-client.ts` fonctionnel | Semaine1 / Etape 3 | [ ] |
| Service Worker avec gestion des messages | Semaine1 / Etape 4 | [ ] |

> **Depend de** : [Semaine1.md](./Semaine1.md) (toutes les etapes)
> **Requis par** : [Semaine3.md](./Semaine3.md)

---

## Progression Semaine 2

- [ ] **Etape 1** : Content script — detection de sites
  - [ ] 1.1 `src/content/detector.ts` (classe FundDetector)
  - [ ] 1.2 Detection URL avec patterns glob
  - [ ] 1.3 Observation des changements SPA (pushState, popstate)
  - [ ] 1.4 Banniere de detection (Shadow DOM)
  - [ ] 1.5 Notification au service worker
  - [ ] **Validation** : Naviguer sur un site configure → banniere verte
- [ ] **Etape 2** : Content script — surlignage des champs
  - [ ] 2.1 `src/content/highlighter.ts` (classe FieldHighlighter)
  - [ ] 2.2 Detection d'elements par selecteurs multiples
  - [ ] 2.3 Surlignage colore (vert=auto, bleu=IA, orange=manuel)
  - [ ] 2.4 Tooltips d'aide avec actions
  - [ ] **Validation** : Champs surlignés avec couleurs et tooltips
- [ ] **Etape 3** : Side Panel — guide pas-a-pas
  - [ ] 3.1 `sidepanel/index.html` + `sidepanel/main.ts`
  - [ ] 3.2 `sidepanel/App.vue` (layout + logique principale)
  - [ ] 3.3 `ProgressBar.vue`
  - [ ] 3.4 `StepNavigator.vue`
  - [ ] 3.5 `StepContent.vue` + `FieldHelper.vue`
  - [ ] 3.6 `DocChecklist.vue`
  - [ ] 3.7 `MiniChat.vue` (assistant IA contextuel)
  - [ ] **Validation** : Side Panel s'ouvre, etapes navigables, chat repond
- [ ] **Etape 4** : Integration content script ↔ side panel
  - [ ] 4.1 `src/content/autofill.ts` (ecoute messages, remplit champs)
  - [ ] 4.2 Communication side panel → content script → page web
  - [ ] 4.3 Mise a jour service worker pour `OPEN_SIDEPANEL`
  - [ ] **Validation** : "Remplir" dans le side panel → valeur inseree dans la page

---

## Objectifs de la semaine
- Implementer la detection automatique des sites de fonds verts
- Creer le Side Panel Chrome avec le guide pas-a-pas
- Developper le systeme de surlignage des champs sur les pages web
- Integrer la checklist de documents requis
- Mettre en place la sauvegarde de progression

---

## Etape 1 : Content Script — Detection de Sites

### 1.1 Detecteur principal

Le content script s'execute sur toutes les pages et verifie si l'URL correspond a un site de fonds vert connu.

```typescript
// src/content/detector.ts

import type { FundSiteConfig, ExtensionMessage } from '@shared/types'

class FundDetector {
  private configs: FundSiteConfig[] = []
  private currentConfig: FundSiteConfig | null = null
  private isInitialized = false

  async init() {
    if (this.isInitialized) return
    this.isInitialized = true

    // Charger les configs depuis le service worker
    const response = await chrome.runtime.sendMessage({
      type: 'SYNC_DATA',
    } as ExtensionMessage)

    if (!response) return

    // Charger les configs de fonds
    const configResponse = await chrome.runtime.sendMessage({
      type: 'GET_FUND_CONFIGS',
    } as ExtensionMessage)

    if (configResponse?.configs) {
      this.configs = configResponse.configs
    }

    // Verifier l'URL actuelle
    this.checkCurrentUrl()

    // Observer les changements d'URL (SPA)
    this.observeUrlChanges()
  }

  /**
   * Verifie si l'URL actuelle correspond a un site de fonds
   */
  private checkCurrentUrl() {
    const url = window.location.href

    for (const config of this.configs) {
      const match = config.url_patterns.some(pattern => this.matchUrl(url, pattern))
      if (match) {
        this.onFundDetected(config)
        return
      }
    }

    // Pas de match : nettoyer si necessaire
    if (this.currentConfig) {
      this.onFundLeft()
    }
  }

  /**
   * Detecte les changements d'URL dans les SPA
   */
  private observeUrlChanges() {
    let lastUrl = window.location.href

    // Observer les changements via pushState/replaceState
    const originalPushState = history.pushState
    const originalReplaceState = history.replaceState

    history.pushState = (...args) => {
      originalPushState.apply(history, args)
      this.onUrlChange()
    }

    history.replaceState = (...args) => {
      originalReplaceState.apply(history, args)
      this.onUrlChange()
    }

    window.addEventListener('popstate', () => this.onUrlChange())

    // Fallback : verifier periodiquement
    setInterval(() => {
      if (window.location.href !== lastUrl) {
        lastUrl = window.location.href
        this.onUrlChange()
      }
    }, 1000)
  }

  private onUrlChange() {
    this.checkCurrentUrl()
  }

  /**
   * Quand un site de fonds est detecte
   */
  private async onFundDetected(config: FundSiteConfig) {
    this.currentConfig = config
    console.log(`[ESG Advisor] Fonds detecte : ${config.fonds_nom}`)

    // Notifier le service worker
    await chrome.runtime.sendMessage({
      type: 'FUND_DETECTED',
      payload: {
        url: window.location.href,
        tabId: undefined, // Le SW le recevra via sender.tab.id
        config,
      },
    } as ExtensionMessage)

    // Injecter l'indicateur visuel sur la page
    this.injectDetectionBanner(config)
  }

  /**
   * Quand on quitte un site de fonds
   */
  private onFundLeft() {
    this.currentConfig = null
    this.removeDetectionBanner()
  }

  /**
   * Injecte une banniere discrette en haut de la page
   */
  private injectDetectionBanner(config: FundSiteConfig) {
    // Supprimer l'ancienne si existante
    this.removeDetectionBanner()

    // Creer dans un Shadow DOM pour l'isolation CSS
    const host = document.createElement('div')
    host.id = 'esg-advisor-banner-host'
    host.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 2147483647;
      pointer-events: none;
    `

    const shadow = host.attachShadow({ mode: 'closed' })

    const banner = document.createElement('div')
    banner.innerHTML = `
      <style>
        .esg-banner {
          background: linear-gradient(135deg, #059669, #0d9488);
          color: white;
          padding: 8px 16px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 12px;
          pointer-events: auto;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          animation: slideDown 0.3s ease-out;
        }
        @keyframes slideDown {
          from { transform: translateY(-100%); }
          to { transform: translateY(0); }
        }
        .esg-banner-icon {
          width: 24px;
          height: 24px;
          background: rgba(255,255,255,0.2);
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .esg-banner-text { flex: 1; }
        .esg-banner-text strong { font-weight: 600; }
        .esg-banner-btn {
          background: white;
          color: #059669;
          border: none;
          padding: 6px 16px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }
        .esg-banner-btn:hover { background: #f0fdf4; }
        .esg-banner-close {
          background: none;
          border: none;
          color: rgba(255,255,255,0.7);
          cursor: pointer;
          padding: 4px;
          font-size: 18px;
          line-height: 1;
        }
        .esg-banner-close:hover { color: white; }
      </style>
      <div class="esg-banner">
        <div class="esg-banner-icon">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955
                  11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29
                  9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div class="esg-banner-text">
          <strong>${config.fonds_nom}</strong> detecte — ESG Advisor peut vous guider
        </div>
        <button class="esg-banner-btn" id="esg-open-guide">
          Ouvrir le guide
        </button>
        <button class="esg-banner-close" id="esg-close-banner">x</button>
      </div>
    `

    shadow.appendChild(banner)
    document.body.appendChild(host)

    // Event listeners
    shadow.getElementById('esg-open-guide')?.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' })
    })

    shadow.getElementById('esg-close-banner')?.addEventListener('click', () => {
      host.remove()
    })

    // Auto-hide apres 10 secondes
    setTimeout(() => {
      if (host.parentElement) {
        host.style.transition = 'opacity 0.3s'
        host.style.opacity = '0'
        setTimeout(() => host.remove(), 300)
      }
    }, 10000)
  }

  private removeDetectionBanner() {
    document.getElementById('esg-advisor-banner-host')?.remove()
  }

  /**
   * Match une URL contre un pattern glob
   */
  private matchUrl(url: string, pattern: string): boolean {
    const regex = new RegExp(
      '^' + pattern
        .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
      + '$'
    )
    return regex.test(url)
  }
}

// Demarrer la detection
const detector = new FundDetector()
detector.init()
```

**Critere de validation :** En naviguant sur un site de fonds configure, la banniere verte apparait en haut de page.

---

## Etape 2 : Content Script — Surlignage des Champs

### 2.1 Highlighter de champs

```typescript
// src/content/highlighter.ts

import type { FundField, FundStep } from '@shared/types'

class FieldHighlighter {
  private highlights: Map<string, HTMLElement> = new Map()
  private tooltips: Map<string, HTMLElement> = new Map()

  /**
   * Surligne les champs d'une etape donnee
   */
  highlightStep(step: FundStep, companyData: Record<string, unknown>) {
    this.clearHighlights()

    for (const field of step.fields) {
      const element = this.findElement(field.selector)
      if (!element) continue

      const hasAutoValue = field.source && this.resolveValue(field.source, companyData)
      const highlightType = hasAutoValue ? 'auto' : field.ai_suggest ? 'ai' : 'manual'

      this.addHighlight(element, field, highlightType)
    }
  }

  /**
   * Trouve un element par selecteur CSS (essaie plusieurs selecteurs)
   */
  private findElement(selector: string): HTMLElement | null {
    // Les selecteurs sont separes par des virgules
    const selectors = selector.split(',').map(s => s.trim())
    for (const sel of selectors) {
      try {
        const el = document.querySelector<HTMLElement>(sel)
        if (el) return el
      } catch {
        // Selecteur invalide, continuer
      }
    }
    return null
  }

  /**
   * Ajoute un surlignage et un tooltip a un element
   */
  private addHighlight(
    element: HTMLElement,
    field: FundField,
    type: 'auto' | 'ai' | 'manual'
  ) {
    const colors = {
      auto: { border: '#059669', bg: '#f0fdf4', label: 'Auto-remplissage', icon: 'check' },
      ai: { border: '#2563eb', bg: '#eff6ff', label: 'Suggestion IA', icon: 'sparkle' },
      manual: { border: '#d97706', bg: '#fffbeb', label: 'A remplir', icon: 'edit' },
    }
    const config = colors[type]

    // Creer le wrapper de surlignage
    const wrapper = document.createElement('div')
    wrapper.className = 'esg-field-highlight'
    wrapper.style.cssText = `
      position: relative;
      outline: 2px solid ${config.border};
      outline-offset: 2px;
      border-radius: 4px;
      transition: outline-color 0.2s;
    `

    // Badge indicateur
    const badge = document.createElement('div')
    badge.style.cssText = `
      position: absolute;
      top: -10px;
      right: -10px;
      background: ${config.border};
      color: white;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: -apple-system, sans-serif;
      z-index: 999999;
      pointer-events: none;
      white-space: nowrap;
    `
    badge.textContent = config.label

    // Tooltip avec aide
    const tooltip = this.createTooltip(field, type)

    // Wrapper autour de l'element
    element.style.position = 'relative'
    element.parentElement?.insertBefore(wrapper, element)
    wrapper.appendChild(element)
    wrapper.appendChild(badge)

    // Afficher tooltip au hover
    wrapper.addEventListener('mouseenter', () => {
      document.body.appendChild(tooltip)
      const rect = wrapper.getBoundingClientRect()
      tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`
      tooltip.style.left = `${rect.left + window.scrollX}px`
    })

    wrapper.addEventListener('mouseleave', () => {
      tooltip.remove()
    })

    this.highlights.set(field.selector, wrapper)
    this.tooltips.set(field.selector, tooltip)
  }

  /**
   * Cree un tooltip d'aide pour un champ
   */
  private createTooltip(field: FundField, type: 'auto' | 'ai' | 'manual'): HTMLElement {
    const host = document.createElement('div')
    host.style.cssText = `
      position: absolute;
      z-index: 2147483647;
    `

    const shadow = host.attachShadow({ mode: 'closed' })
    shadow.innerHTML = `
      <style>
        .tooltip {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          max-width: 300px;
          font-family: -apple-system, sans-serif;
          font-size: 13px;
        }
        .tooltip-header {
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 4px;
        }
        .tooltip-help {
          color: #6b7280;
          line-height: 1.4;
        }
        .tooltip-action {
          margin-top: 8px;
          display: flex;
          gap: 8px;
        }
        .tooltip-btn {
          padding: 4px 12px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: background 0.2s;
        }
        .btn-primary {
          background: #059669;
          color: white;
        }
        .btn-primary:hover { background: #047857; }
        .btn-secondary {
          background: #f3f4f6;
          color: #374151;
        }
        .btn-secondary:hover { background: #e5e7eb; }
      </style>
      <div class="tooltip">
        <div class="tooltip-header">${field.label}</div>
        <div class="tooltip-help">${field.help_text}</div>
        <div class="tooltip-action">
          ${type === 'auto' ? '<button class="tooltip-btn btn-primary" data-action="autofill">Remplir automatiquement</button>' : ''}
          ${type === 'ai' ? '<button class="tooltip-btn btn-primary" data-action="ai-suggest">Generer avec l\'IA</button>' : ''}
          <button class="tooltip-btn btn-secondary" data-action="copy">Copier la suggestion</button>
        </div>
      </div>
    `

    return host
  }

  /**
   * Resout une valeur depuis les donnees de l'entreprise
   * Ex: "entreprise.nom" → data.entreprise.nom
   */
  private resolveValue(path: string, data: Record<string, unknown>): unknown {
    return path.split('.').reduce((obj: unknown, key) => {
      if (obj && typeof obj === 'object') {
        return (obj as Record<string, unknown>)[key]
      }
      return undefined
    }, data)
  }

  /**
   * Supprime tous les surlignages
   */
  clearHighlights() {
    for (const [, wrapper] of this.highlights) {
      const child = wrapper.firstElementChild as HTMLElement
      if (child) {
        wrapper.parentElement?.insertBefore(child, wrapper)
      }
      wrapper.remove()
    }
    for (const [, tooltip] of this.tooltips) {
      tooltip.remove()
    }
    this.highlights.clear()
    this.tooltips.clear()
  }
}

export const fieldHighlighter = new FieldHighlighter()
```

**Critere de validation :** Les champs de formulaire sont surlignés avec les bonnes couleurs (vert=auto, bleu=IA, orange=manuel).

---

## Etape 3 : Side Panel — Guide Pas-a-Pas

### 3.1 Structure Side Panel

```html
<!-- src/sidepanel/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESG Advisor - Guide</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

```typescript
// src/sidepanel/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '../../assets/styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

### 3.2 App Side Panel

```vue
<!-- src/sidepanel/App.vue -->
<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- Header -->
    <header class="bg-emerald-600 text-white px-4 py-3 flex items-center gap-2 shrink-0">
      <img src="../assets/icons/icon-32.png" alt="" class="w-6 h-6">
      <h1 class="text-sm font-bold flex-1">ESG Advisor Guide</h1>
      <span v-if="fundConfig" class="text-xs bg-emerald-500 px-2 py-0.5 rounded">
        {{ fundConfig.fonds_nom }}
      </span>
    </header>

    <!-- Contenu principal -->
    <main class="flex-1 overflow-y-auto">
      <!-- Etat : pas de fonds detecte -->
      <NoFundDetected v-if="!fundConfig" />

      <!-- Etat : guide actif -->
      <template v-else>
        <!-- Barre de progression globale -->
        <ProgressBar
          :current-step="currentStep"
          :total-steps="fundConfig.steps.length"
          :progress-pct="progressPct"
        />

        <!-- Navigation par etapes -->
        <StepNavigator
          :steps="fundConfig.steps"
          :current-step="currentStep"
          @select="goToStep"
        />

        <!-- Contenu de l'etape courante -->
        <StepContent
          :step="fundConfig.steps[currentStep]"
          :company-data="companyData"
          :fund-config="fundConfig"
          @field-autofill="handleAutofill"
          @field-ai-suggest="handleAiSuggest"
          @next="nextStep"
          @prev="prevStep"
        />

        <!-- Checklist documents -->
        <DocChecklist
          v-if="currentStep === docChecklistStep"
          :required-docs="fundConfig.required_docs"
          :available-docs="companyData?.documents || []"
        />
      </template>
    </main>

    <!-- Chat IA (accordion en bas) -->
    <MiniChat
      v-if="fundConfig"
      :fund-config="fundConfig"
      :current-step="currentStep"
      class="shrink-0"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { FundSiteConfig, SyncedData } from '@shared/types'
import NoFundDetected from './components/NoFundDetected.vue'
import ProgressBar from './components/ProgressBar.vue'
import StepNavigator from './components/StepNavigator.vue'
import StepContent from './components/StepContent.vue'
import DocChecklist from './components/DocChecklist.vue'
import MiniChat from './components/MiniChat.vue'

const fundConfig = ref<FundSiteConfig | null>(null)
const companyData = ref<SyncedData | null>(null)
const currentStep = ref(0)

const progressPct = computed(() => {
  if (!fundConfig.value) return 0
  return Math.round((currentStep.value / fundConfig.value.steps.length) * 100)
})

const docChecklistStep = computed(() => {
  if (!fundConfig.value) return -1
  // L'etape "Documents" est generalement l'avant-derniere
  return fundConfig.value.steps.findIndex(s =>
    s.title.toLowerCase().includes('document')
  )
})

onMounted(async () => {
  // Charger les donnees de l'entreprise
  const data = await chrome.runtime.sendMessage({ type: 'GET_COMPANY_DATA' })
  companyData.value = data

  // Ecouter les detections de fonds
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'FUND_DETECTED' && message.payload?.config) {
      fundConfig.value = message.payload.config
      currentStep.value = 0
    }
  })
})

function goToStep(index: number) {
  currentStep.value = index
  saveProgress()
}

function nextStep() {
  if (fundConfig.value && currentStep.value < fundConfig.value.steps.length - 1) {
    currentStep.value++
    saveProgress()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function handleAutofill(payload: { selector: string; value: string }) {
  // Envoyer au content script pour remplir le champ
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'AUTOFILL_FIELD',
      payload,
    })
  }
}

async function handleAiSuggest(payload: { field_name: string; field_label: string }) {
  const response = await chrome.runtime.sendMessage({
    type: 'FIELD_SUGGESTION',
    payload: {
      fonds_id: fundConfig.value?.fonds_id,
      ...payload,
      context: fundConfig.value?.steps[currentStep.value]?.description || '',
    },
  })
  return response?.suggestion
}

async function saveProgress() {
  await chrome.runtime.sendMessage({
    type: 'SAVE_PROGRESS',
    payload: {
      application_id: '', // A gerer
      form_data: {},
      current_step: currentStep.value,
    },
  })
}
</script>
```

### 3.3 Composants du Side Panel

#### ProgressBar

```vue
<!-- src/sidepanel/components/ProgressBar.vue -->
<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <div class="flex items-center justify-between mb-1">
      <span class="text-xs font-medium text-gray-600">
        Etape {{ currentStep + 1 }} / {{ totalSteps }}
      </span>
      <span class="text-xs font-bold text-emerald-600">{{ progressPct }}%</span>
    </div>
    <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        class="h-full bg-emerald-500 rounded-full transition-all duration-500 ease-out"
        :style="{ width: progressPct + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentStep: number
  totalSteps: number
  progressPct: number
}>()
</script>
```

#### StepNavigator

```vue
<!-- src/sidepanel/components/StepNavigator.vue -->
<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <div class="flex gap-1 overflow-x-auto">
      <button
        v-for="(step, index) in steps"
        :key="index"
        @click="$emit('select', index)"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
               whitespace-nowrap transition-colors"
        :class="index === currentStep
          ? 'bg-emerald-100 text-emerald-700'
          : index < currentStep
            ? 'bg-gray-100 text-gray-600'
            : 'text-gray-400 hover:bg-gray-50'"
      >
        <!-- Numero / check -->
        <span
          class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
          :class="index < currentStep
            ? 'bg-emerald-500 text-white'
            : index === currentStep
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-200 text-gray-500'"
        >
          <svg v-if="index < currentStep" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>{{ index + 1 }}</span>
        </span>
        {{ step.title }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FundStep } from '@shared/types'

defineProps<{
  steps: FundStep[]
  currentStep: number
}>()

defineEmits<{
  select: [index: number]
}>()
</script>
```

#### StepContent

```vue
<!-- src/sidepanel/components/StepContent.vue -->
<template>
  <div class="px-4 py-4">
    <!-- Description de l'etape -->
    <div class="mb-4">
      <h2 class="text-base font-semibold text-gray-800">{{ step.title }}</h2>
      <p class="text-sm text-gray-500 mt-1">{{ step.description }}</p>
    </div>

    <!-- Liste des champs -->
    <div class="space-y-3">
      <FieldHelper
        v-for="field in step.fields"
        :key="field.selector"
        :field="field"
        :company-data="companyData"
        :suggestion="suggestions[field.selector]"
        :suggesting="suggestingFields.has(field.selector)"
        @autofill="$emit('field-autofill', $event)"
        @ai-suggest="requestSuggestion(field)"
      />
    </div>

    <!-- Conseil de l'etape -->
    <div v-if="tip" class="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
      <div class="flex gap-2">
        <svg class="w-4 h-4 text-amber-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-xs text-amber-800">{{ tip }}</p>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex gap-3 mt-6">
      <button
        v-if="step.order > 1"
        @click="$emit('prev')"
        class="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm
               font-medium hover:bg-gray-50 transition-colors"
      >
        Precedent
      </button>
      <button
        @click="$emit('next')"
        class="flex-1 bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm
               font-medium hover:bg-emerald-700 transition-colors"
      >
        {{ isLastStep ? 'Terminer' : 'Suivant' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FundStep, FundSiteConfig } from '@shared/types'
import FieldHelper from './FieldHelper.vue'

const props = defineProps<{
  step: FundStep
  companyData: Record<string, unknown> | null
  fundConfig: FundSiteConfig
}>()

const emit = defineEmits<{
  'field-autofill': [payload: { selector: string; value: string }]
  'field-ai-suggest': [payload: { field_name: string; field_label: string }]
  next: []
  prev: []
}>()

const suggestions = ref<Record<string, string>>({})
const suggestingFields = ref<Set<string>>(new Set())

const isLastStep = computed(() =>
  props.step.order === props.fundConfig.steps.length
)

const tip = computed(() => {
  if (!props.fundConfig.tips) return null
  // Chercher un tip correspondant a cette etape
  const stepKey = props.step.title.toLowerCase()
  for (const [key, value] of Object.entries(props.fundConfig.tips)) {
    if (stepKey.includes(key)) return value
  }
  return props.fundConfig.tips.general || null
})

async function requestSuggestion(field: typeof props.step.fields[0]) {
  suggestingFields.value.add(field.selector)
  try {
    const response = await emit('field-ai-suggest', {
      field_name: field.selector,
      field_label: field.label,
    })
    if (response) {
      suggestions.value[field.selector] = response
    }
  } finally {
    suggestingFields.value.delete(field.selector)
  }
}
</script>
```

#### FieldHelper

```vue
<!-- src/sidepanel/components/FieldHelper.vue -->
<template>
  <div class="bg-white rounded-lg border p-3"
       :class="borderClass">
    <div class="flex items-start gap-2">
      <!-- Icone type -->
      <div class="w-6 h-6 rounded flex items-center justify-center shrink-0 mt-0.5"
           :class="iconBgClass">
        <svg v-if="hasAutoValue" class="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <svg v-else-if="field.ai_suggest" class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <svg v-else class="w-3.5 h-3.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2
                2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h4 class="text-sm font-medium text-gray-800">{{ field.label }}</h4>
          <span v-if="field.required" class="text-red-400 text-xs">*</span>
        </div>
        <p class="text-xs text-gray-500 mt-0.5">{{ field.help_text }}</p>

        <!-- Valeur auto-remplissable -->
        <div v-if="hasAutoValue" class="mt-2 bg-emerald-50 rounded px-3 py-1.5 flex items-center gap-2">
          <span class="text-sm text-emerald-800 flex-1 truncate">{{ autoValue }}</span>
          <button
            @click="handleAutofill"
            class="text-xs text-emerald-600 hover:text-emerald-700 font-medium whitespace-nowrap"
          >
            Remplir
          </button>
        </div>

        <!-- Suggestion IA -->
        <div v-else-if="field.ai_suggest" class="mt-2">
          <div v-if="suggestion" class="bg-blue-50 rounded px-3 py-1.5">
            <p class="text-sm text-blue-800">{{ suggestion }}</p>
            <div class="flex gap-2 mt-1.5">
              <button
                @click="copyToClipboard(suggestion)"
                class="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Copier
              </button>
              <button
                @click="handleAutofill"
                class="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Inserer dans le champ
              </button>
            </div>
          </div>
          <button
            v-else
            @click="$emit('ai-suggest')"
            :disabled="suggesting"
            class="mt-1 text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span v-if="suggesting" class="w-3 h-3 border border-blue-400 border-t-transparent
                                           rounded-full animate-spin"></span>
            {{ suggesting ? 'Generation...' : 'Generer avec l\'IA' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FundField } from '@shared/types'

const props = defineProps<{
  field: FundField
  companyData: Record<string, unknown> | null
  suggestion?: string
  suggesting: boolean
}>()

const emit = defineEmits<{
  autofill: [payload: { selector: string; value: string }]
  'ai-suggest': []
}>()

const autoValue = computed(() => {
  if (!props.field.source || !props.companyData) return null
  return resolveValue(props.field.source, props.companyData)
})

const hasAutoValue = computed(() => !!autoValue.value)

const borderClass = computed(() => {
  if (hasAutoValue.value) return 'border-emerald-200'
  if (props.field.ai_suggest) return 'border-blue-200'
  return 'border-gray-200'
})

const iconBgClass = computed(() => {
  if (hasAutoValue.value) return 'bg-emerald-100'
  if (props.field.ai_suggest) return 'bg-blue-100'
  return 'bg-amber-100'
})

function resolveValue(path: string, data: Record<string, unknown>): string | null {
  const value = path.split('.').reduce((obj: unknown, key) => {
    if (obj && typeof obj === 'object') {
      return (obj as Record<string, unknown>)[key]
    }
    return undefined
  }, data)
  return value != null ? String(value) : null
}

function handleAutofill() {
  const value = autoValue.value || props.suggestion
  if (value) {
    emit('autofill', { selector: props.field.selector, value })
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}
</script>
```

#### DocChecklist

```vue
<!-- src/sidepanel/components/DocChecklist.vue -->
<template>
  <div class="px-4 py-4 border-t border-gray-200">
    <h3 class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
      <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0
              01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Documents requis
      <span class="text-xs text-gray-400">
        {{ availableCount }}/{{ requiredDocs.length }}
      </span>
    </h3>

    <div class="space-y-2">
      <div
        v-for="doc in docsWithStatus"
        :key="doc.name"
        class="flex items-start gap-2 p-2 rounded-lg"
        :class="doc.available ? 'bg-emerald-50' : 'bg-gray-50'"
      >
        <!-- Icone statut -->
        <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
             :class="doc.available ? 'bg-emerald-500' : 'bg-gray-300'">
          <svg v-if="doc.available" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else class="w-2 h-2 bg-white rounded-full"></span>
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium" :class="doc.available ? 'text-emerald-800' : 'text-gray-700'">
              {{ doc.name }}
            </span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 text-gray-500">
              {{ doc.format }}
            </span>
          </div>
          <p class="text-[11px] text-gray-500 mt-0.5">{{ doc.description }}</p>
          <p v-if="doc.available" class="text-[11px] text-emerald-600 mt-0.5">
            Disponible sur la plateforme
          </p>
          <a v-else href="http://localhost:5173/documents" target="_blank"
             class="text-[11px] text-blue-600 hover:underline mt-0.5 inline-block">
            Telecharger sur la plateforme
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RequiredDoc, DocumentSummary } from '@shared/types'

const props = defineProps<{
  requiredDocs: RequiredDoc[]
  availableDocs: DocumentSummary[]
}>()

const docsWithStatus = computed(() =>
  props.requiredDocs.map(doc => ({
    ...doc,
    available: doc.available_on_platform ||
      props.availableDocs.some(d =>
        d.nom_fichier.toLowerCase().includes(doc.type.toLowerCase()) ||
        d.type_mime?.includes(doc.format.toLowerCase())
      ),
  }))
)

const availableCount = computed(() =>
  docsWithStatus.value.filter(d => d.available).length
)
</script>
```

#### MiniChat (Assistant IA contextuel)

```vue
<!-- src/sidepanel/components/MiniChat.vue -->
<template>
  <div class="border-t border-gray-200 bg-white">
    <!-- Toggle -->
    <button
      @click="isOpen = !isOpen"
      class="w-full px-4 py-2 flex items-center gap-2 text-sm font-medium text-gray-700
             hover:bg-gray-50 transition-colors"
    >
      <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2
              2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
      Poser une question
      <svg class="w-4 h-4 ml-auto transition-transform" :class="{ 'rotate-180': isOpen }"
           fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
      </svg>
    </button>

    <!-- Chat panel -->
    <div v-if="isOpen" class="border-t border-gray-100">
      <!-- Messages -->
      <div ref="messagesRef" class="h-48 overflow-y-auto px-4 py-3 space-y-3">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[85%] rounded-lg px-3 py-2 text-sm"
            :class="msg.role === 'user'
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-100 text-gray-800'"
          >
            {{ msg.content }}
          </div>
        </div>
        <div v-if="loading" class="flex justify-start">
          <div class="bg-gray-100 rounded-lg px-4 py-2">
            <div class="flex gap-1">
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="px-4 pb-3 flex gap-2">
        <input
          v-model="input"
          @keydown.enter="sendMessage"
          placeholder="Ex: Que mettre dans ce champ ?"
          class="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
        <button
          @click="sendMessage"
          :disabled="!input.trim() || loading"
          class="bg-emerald-600 text-white rounded-lg px-3 py-1.5
                 hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>

      <!-- Suggestions rapides -->
      <div class="px-4 pb-3 flex flex-wrap gap-1.5">
        <button
          v-for="q in quickQuestions"
          :key="q"
          @click="input = q; sendMessage()"
          class="text-[11px] bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full
                 hover:bg-emerald-50 hover:text-emerald-700 transition-colors"
        >
          {{ q }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { FundSiteConfig } from '@shared/types'

const props = defineProps<{
  fundConfig: FundSiteConfig
  currentStep: number
}>()

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const isOpen = ref(false)
const input = ref('')
const messages = ref<ChatMessage[]>([])
const loading = ref(false)
const messagesRef = ref<HTMLElement>()

const quickQuestions = [
  'Que mettre dans ce champ ?',
  'Quels documents fournir ?',
  'Conseils pour cette etape',
]

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: text,
  })
  input.value = ''
  loading.value = true

  await nextTick()
  messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'FIELD_SUGGESTION',
      payload: {
        fonds_id: props.fundConfig.fonds_id,
        field_name: 'chat',
        field_label: text,
        context: `Etape ${props.currentStep + 1}: ${props.fundConfig.steps[props.currentStep]?.title}`,
      },
    })

    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response?.suggestion || 'Desole, je n\'ai pas pu generer de reponse.',
    })
  } catch {
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Erreur de communication. Verifiez votre connexion.',
    })
  } finally {
    loading.value = false
    await nextTick()
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>
```

**Critere de validation :** Le Side Panel s'ouvre, affiche les etapes, permet de naviguer, et le chat IA repond aux questions.

---

## Etape 4 : Integration Content Script ↔ Side Panel

### 4.1 Autofill handler dans le content script

```typescript
// src/content/autofill.ts

/**
 * Ecoute les messages du Side Panel pour remplir les champs
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AUTOFILL_FIELD') {
    const { selector, value } = message.payload

    // Trouver l'element
    const selectors = selector.split(',').map((s: string) => s.trim())
    let element: HTMLElement | null = null

    for (const sel of selectors) {
      try {
        element = document.querySelector<HTMLElement>(sel)
        if (element) break
      } catch { /* continuer */ }
    }

    if (!element) {
      sendResponse({ success: false, error: 'Element non trouve' })
      return
    }

    // Remplir selon le type d'element
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      // Simuler une saisie naturelle
      element.focus()
      element.value = value

      // Declencher les evenements pour que les frameworks JS detectent le changement
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))
      element.dispatchEvent(new Event('blur', { bubbles: true }))

      // Animation de confirmation
      element.style.transition = 'background-color 0.3s'
      element.style.backgroundColor = '#f0fdf4'
      setTimeout(() => {
        element!.style.backgroundColor = ''
      }, 1000)

      sendResponse({ success: true })
    } else if (element instanceof HTMLSelectElement) {
      // Pour les selects, chercher l'option correspondante
      const option = Array.from(element.options).find(
        opt => opt.value === value || opt.text.toLowerCase().includes(value.toLowerCase())
      )
      if (option) {
        element.value = option.value
        element.dispatchEvent(new Event('change', { bubbles: true }))
        sendResponse({ success: true })
      } else {
        sendResponse({ success: false, error: 'Option non trouvee' })
      }
    }
  }

  if (message.type === 'HIGHLIGHT_FIELDS') {
    // Recevoir les champs a surligner depuis le side panel
    const { step, companyData } = message.payload
    // Utiliser le highlighter
    // fieldHighlighter.highlightStep(step, companyData)
    sendResponse({ success: true })
  }
})
```

### 4.2 Mise a jour du service worker pour le side panel

```typescript
// Ajouter dans service-worker.ts

// Ouvrir le side panel quand demande
chrome.runtime.onMessage.addListener(async (message, sender) => {
  if (message.type === 'OPEN_SIDEPANEL') {
    const tab = sender.tab || (await chrome.tabs.query({ active: true, currentWindow: true }))[0]
    if (tab?.id) {
      chrome.sidePanel.open({ tabId: tab.id })
    }
  }

  if (message.type === 'GET_FUND_CONFIGS') {
    const configs = await getFundConfigs()
    return { configs }
  }
})
```

**Critere de validation :** Cliquer "Remplir" dans le Side Panel insere la valeur dans le champ correspondant sur la page web.

---

## Resume Semaine 2

| Jour | Taches | Livrable |
|------|--------|----------|
| J1 | Content script detector + banniere detection | Detection fonctionnelle |
| J2 | Highlighter de champs + styles | Surlignage visuel |
| J3 | Side Panel structure + ProgressBar + StepNavigator | Navigation par etapes |
| J4 | StepContent + FieldHelper + DocChecklist | Guide complet |
| J5 | MiniChat + Autofill integration | IA + pre-remplissage |

### Checklist de fin de semaine

- [ ] Naviguer sur un site configure declenche la banniere de detection
- [ ] Le badge de l'extension change quand un fonds est detecte
- [ ] Le Side Panel affiche les etapes de candidature
- [ ] La navigation entre etapes fonctionne (precedent/suivant)
- [ ] Les champs avec source auto affichent la valeur de la plateforme
- [ ] Le bouton "Remplir" insere la valeur dans le champ de la page
- [ ] Le bouton "Generer avec l'IA" appelle le backend et affiche la suggestion
- [ ] La checklist de documents montre les documents disponibles/manquants
- [ ] Le mini-chat IA repond aux questions contextuelles
- [ ] La progression est sauvegardee entre les sessions
