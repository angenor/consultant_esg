<template>
  <div class="px-4 py-4">
    <!-- Description de l'etape -->
    <div class="mb-4">
      <h2 class="text-base font-semibold text-gray-800">{{ step.title }}</h2>
      <p class="text-sm text-gray-500 mt-1">{{ step.description }}</p>
    </div>

    <!-- Bouton remplissage automatique global -->
    <div v-if="autoFillableCount > 0" class="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <div class="flex-1">
          <p class="text-sm font-medium text-emerald-800">
            {{ t('autofill_count', String(autoFillableCount)) }}
          </p>
          <p class="text-xs text-emerald-600">
            {{ t('autofill_source') }}
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
          {{ batchFilling ? t('autofill_filling') : t('autofill_all') }}
        </button>
      </div>
      <div v-if="batchResult" class="mt-2 text-xs text-emerald-700">
        {{ t('autofill_result', String(batchResult.filled)) }}
        <span v-if="batchResult.failed.length"> · {{ t('autofill_failures', String(batchResult.failed.length)) }}</span>
      </div>
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
        {{ t('previous') }}
      </button>
      <button
        @click="$emit('next')"
        class="flex-1 bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm
               font-medium hover:bg-emerald-700 transition-colors"
      >
        {{ isLastStep ? t('finish') : t('next') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FundStep, FundSiteConfig, FundField } from '@shared/types'
import { DataMapper } from '@shared/data-mapper'
import { t } from '@shared/i18n'
import FieldHelper from './FieldHelper.vue'

const props = defineProps<{
  step: FundStep
  companyData: Record<string, unknown> | null
  fundConfig: FundSiteConfig
}>()

const emit = defineEmits<{
  'field-autofill': [payload: { selector: string; value: string }]
  'field-ai-suggest': [payload: { field_name: string; field_label: string }]
  'batch-autofill': [mappings: Record<string, string>]
  next: []
  prev: []
}>()

const suggestions = ref<Record<string, string>>({})
const suggestingFields = ref<Set<string>>(new Set())
const batchFilling = ref(false)
const batchResult = ref<{ filled: number; failed: string[] } | null>(null)

const isLastStep = computed(() =>
  props.step.order === props.fundConfig.steps.length
)

const tip = computed(() => {
  if (!props.fundConfig.tips) return null
  const stepKey = props.step.title.toLowerCase()
  for (const [key, value] of Object.entries(props.fundConfig.tips)) {
    if (stepKey.includes(key)) return value
  }
  return props.fundConfig.tips.general || null
})

const autoFillableCount = computed(() => {
  if (!props.companyData) return 0
  const mapper = new DataMapper(props.companyData as never)
  return props.step.fields.filter(f => f.source && mapper.resolve(f.source)).length
})

async function handleBatchAutofill() {
  if (!props.companyData) return
  batchFilling.value = true
  batchResult.value = null

  const mapper = new DataMapper(props.companyData as never)
  const mappings = mapper.mapStep(props.step.fields)

  // Envoyer au content script via le tab actif
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (tab?.id) {
    const result = await chrome.tabs.sendMessage(tab.id, {
      type: 'BATCH_AUTOFILL',
      payload: { mappings },
    })
    batchResult.value = result || { filled: 0, failed: [] }
  }

  batchFilling.value = false
}

async function requestSuggestion(field: FundField) {
  suggestingFields.value.add(field.selector)
  try {
    const suggestion = await emit('field-ai-suggest' as never, {
      field_name: field.selector,
      field_label: field.label,
    })
    if (suggestion) {
      suggestions.value[field.selector] = suggestion as string
    }
  } finally {
    suggestingFields.value.delete(field.selector)
  }
}
</script>
