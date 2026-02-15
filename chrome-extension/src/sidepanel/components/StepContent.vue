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
import type { FundStep, FundSiteConfig, FundField } from '@shared/types'
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
  const stepKey = props.step.title.toLowerCase()
  for (const [key, value] of Object.entries(props.fundConfig.tips)) {
    if (stepKey.includes(key)) return value
  }
  return props.fundConfig.tips.general || null
})

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
