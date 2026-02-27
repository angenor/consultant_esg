<template>
  <div class="px-4 py-3 bg-white border-b border-gray-100">
    <div class="flex items-center justify-between mb-1">
      <span class="text-xs font-medium text-gray-600">Progression globale</span>
      <span class="text-xs font-bold" :class="progressColor">{{ progressPct }}%</span>
    </div>

    <!-- Barre composite -->
    <div class="w-full bg-gray-200 rounded-full h-2 flex overflow-hidden">
      <!-- Pre-etapes (bleu) -->
      <div v-if="preStepCount > 0"
           class="bg-blue-400 h-2 transition-all"
           :style="{ width: `${preStepWidth}%` }" />
      <!-- Documents (amber) -->
      <div v-if="docTotal > 0"
           class="bg-amber-400 h-2 transition-all"
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
      <span v-if="docTotal > 0" class="flex items-center gap-1 text-[10px] text-gray-500">
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

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  currentStep: number
  totalSteps: number
  progressPct: number
  preStepDone?: number
  preStepCount?: number
  docReady?: number
  docTotal?: number
}>(), {
  preStepDone: 0,
  preStepCount: 0,
  docReady: 0,
  docTotal: 0,
})

const totalItems = computed(() =>
  (props.preStepCount) + (props.docTotal) + props.totalSteps
)

const preStepWidth = computed(() => {
  if (totalItems.value === 0) return 0
  return ((props.preStepDone) / totalItems.value) * 100
})

const docWidth = computed(() => {
  if (totalItems.value === 0) return 0
  return ((props.docReady) / totalItems.value) * 100
})

const stepWidth = computed(() => {
  if (totalItems.value === 0) return 0
  return (props.currentStep / totalItems.value) * 100
})

const progressColor = computed(() => {
  if (props.progressPct >= 80) return 'text-emerald-600'
  if (props.progressPct >= 40) return 'text-amber-600'
  return 'text-gray-600'
})
</script>
