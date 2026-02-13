<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  titre: string
  pourcentage: number
  nbTotal: number
  nbFait: number
  scoreInitial?: number | null
  scoreCible?: number | null
}>()

const barColor = computed(() => {
  if (props.pourcentage >= 75) return 'bg-emerald-500'
  if (props.pourcentage >= 50) return 'bg-teal-500'
  if (props.pourcentage >= 25) return 'bg-amber-500'
  return 'bg-red-400'
})
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h3 class="text-base font-semibold text-gray-800">{{ titre }}</h3>
        <p class="mt-0.5 text-xs text-gray-500">{{ nbFait }}/{{ nbTotal }} actions complétées</p>
      </div>
      <span class="text-2xl font-bold text-gray-900">{{ pourcentage }}%</span>
    </div>

    <!-- Progress bar -->
    <div class="h-4 overflow-hidden rounded-full bg-gray-100">
      <div
        class="h-4 rounded-full transition-all duration-700"
        :class="barColor"
        :style="{ width: `${pourcentage}%` }"
      />
    </div>

    <!-- Score initial → cible -->
    <div v-if="scoreInitial != null && scoreCible != null" class="mt-4 flex items-center justify-center gap-3 text-sm">
      <span class="rounded-lg bg-gray-100 px-3 py-1 font-medium text-gray-600">
        Score initial : {{ scoreInitial }}
      </span>
      <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
      <span class="rounded-lg bg-emerald-100 px-3 py-1 font-medium text-emerald-700">
        Cible : {{ scoreCible }}
      </span>
    </div>
  </div>
</template>
