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
