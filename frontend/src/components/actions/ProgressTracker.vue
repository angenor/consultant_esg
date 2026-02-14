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

const circumference = 2 * Math.PI * 40
const circleOffset = computed(() => circumference * (1 - props.pourcentage / 100))

const circleColor = computed(() => {
  if (props.pourcentage >= 75) return '#059669'
  if (props.pourcentage >= 50) return '#0d9488'
  if (props.pourcentage >= 25) return '#d97706'
  return '#f87171'
})
</script>

<template>
  <div class="relative overflow-hidden rounded-2xl border border-gray-200 bg-linear-to-br from-white via-emerald-50/30 to-teal-50/40 p-6 shadow-sm">
    <div class="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-emerald-100/30 blur-3xl" />
    <div class="absolute -bottom-12 -left-12 h-36 w-36 rounded-full bg-teal-100/20 blur-2xl" />

    <div class="relative flex flex-col items-center gap-6 sm:flex-row sm:items-center">
      <!-- Circular progress -->
      <div class="relative flex shrink-0 items-center justify-center">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#e2e8f0" stroke-width="8" />
          <circle
            cx="50" cy="50" r="40" fill="none"
            :stroke="circleColor"
            stroke-width="8" stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="circleOffset"
            class="-rotate-90 origin-center transition-all duration-700"
          />
        </svg>
        <span class="absolute text-xl font-bold text-gray-900">{{ pourcentage }}%</span>
      </div>

      <!-- Info -->
      <div class="min-w-0 flex-1 text-center sm:text-left">
        <h3 class="text-lg font-bold text-gray-900">{{ titre }}</h3>
        <p class="mt-1 text-sm text-gray-500">
          <span class="font-semibold text-gray-700">{{ nbFait }}</span> sur
          <span class="font-semibold text-gray-700">{{ nbTotal }}</span> actions complétées
        </p>

        <!-- Progress bar -->
        <div class="mt-3 h-2.5 overflow-hidden rounded-full bg-gray-200/60">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="barColor"
            :style="{ width: `${pourcentage}%` }"
          />
        </div>

        <!-- Score initial → cible -->
        <div v-if="scoreInitial != null && scoreCible != null" class="mt-4 flex items-center justify-center gap-3 text-sm sm:justify-start">
          <span class="inline-flex items-center gap-1.5 rounded-lg bg-white/80 px-3 py-1.5 font-medium text-gray-600 shadow-sm ring-1 ring-gray-200">
            <span class="h-2 w-2 rounded-full bg-gray-400" />
            {{ scoreInitial }} pts
          </span>
          <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
          <span class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 font-medium text-emerald-700 shadow-sm ring-1 ring-emerald-200">
            <span class="h-2 w-2 rounded-full bg-emerald-500" />
            {{ scoreCible }} pts
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
