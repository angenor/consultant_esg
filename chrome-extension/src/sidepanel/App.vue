<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- Header -->
    <header class="bg-emerald-600 text-white px-4 py-3 flex items-center gap-2 shrink-0">
      <img src="../../assets/icons/icon-32.png" alt="" class="w-6 h-6">
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
import { ref, computed, onMounted } from 'vue'
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
      application_id: '',
      form_data: {},
      current_step: currentStep.value,
    },
  })
}
</script>
