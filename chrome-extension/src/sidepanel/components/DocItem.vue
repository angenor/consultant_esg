<template>
  <div class="flex items-start gap-2 p-2 rounded-lg" :class="bgClass">
    <!-- Icone statut -->
    <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
         :class="iconClass">
      <!-- Ready -->
      <svg v-if="doc.status === 'ready'" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
      </svg>
      <!-- Generating spinner -->
      <span v-else-if="doc.status === 'generating'"
            class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
      <!-- Missing -->
      <span v-else class="w-2 h-2 bg-white rounded-full"></span>
    </div>

    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium" :class="textClass">{{ doc.name }}</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 text-gray-500">
          {{ doc.format }}
        </span>
      </div>
      <p class="text-[11px] text-gray-500 mt-0.5">{{ doc.description }}</p>

      <!-- Disponible -->
      <p v-if="doc.status === 'ready' && !doc.warnings.length"
         class="text-[11px] text-emerald-600 mt-0.5">
        Disponible sur la plateforme
      </p>

      <!-- Actions si manquant -->
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
        <span class="text-[11px] text-amber-600">Generation en cours...</span>
      </div>

      <!-- Validation warnings -->
      <div v-if="doc.warnings.length" class="mt-1">
        <p v-for="w in doc.warnings" :key="w" class="text-[11px] text-amber-600">
          ⚠ {{ w }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DocWithStatus } from '@shared/types'

const props = defineProps<{
  doc: DocWithStatus
}>()

defineEmits<{
  generate: []
  upload: []
}>()

const bgClass = computed(() => {
  if (props.doc.status === 'ready') return 'bg-emerald-50'
  if (props.doc.status === 'generating') return 'bg-amber-50'
  return 'bg-gray-50'
})

const iconClass = computed(() => {
  if (props.doc.status === 'ready') return 'bg-emerald-500'
  if (props.doc.status === 'generating') return 'bg-amber-400'
  return 'bg-gray-300'
})

const textClass = computed(() => {
  if (props.doc.status === 'ready') return 'text-emerald-800'
  return 'text-gray-700'
})
</script>
