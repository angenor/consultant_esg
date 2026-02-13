<script setup lang="ts">
export interface ScoreFactor {
  label: string
  impact: number
}

defineProps<{
  solvabilite: number
  impactVert: number
  facteursPositifs: ScoreFactor[]
  facteursNegatifs: ScoreFactor[]
}>()

function barWidth(score: number): string {
  return `${Math.min(Math.max(score, 0), 100)}%`
}

function barColor(score: number): string {
  if (score >= 75) return 'bg-emerald-500'
  if (score >= 60) return 'bg-teal-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Score bars -->
    <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">Détail des scores</h3>

      <div class="space-y-4">
        <!-- Solvabilité -->
        <div>
          <div class="mb-1 flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">Solvabilité financière</span>
            <span class="text-sm font-bold text-gray-900">{{ solvabilite }}/100</span>
          </div>
          <div class="h-3 rounded-full bg-gray-100">
            <div class="h-3 rounded-full transition-all duration-500" :class="barColor(solvabilite)" :style="{ width: barWidth(solvabilite) }" />
          </div>
        </div>

        <!-- Impact vert -->
        <div>
          <div class="mb-1 flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">Impact vert (ESG)</span>
            <span class="text-sm font-bold text-gray-900">{{ impactVert }}/100</span>
          </div>
          <div class="h-3 rounded-full bg-gray-100">
            <div class="h-3 rounded-full transition-all duration-500" :class="barColor(impactVert)" :style="{ width: barWidth(impactVert) }" />
          </div>
        </div>
      </div>
    </div>

    <!-- Factors -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <!-- Positive -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h4 class="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-700">
          <span class="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-xs">+</span>
          Facteurs positifs
        </h4>
        <ul v-if="facteursPositifs.length > 0" class="space-y-2">
          <li v-for="f in facteursPositifs" :key="f.label" class="flex items-center justify-between text-sm">
            <span class="text-gray-700">{{ f.label }}</span>
            <span class="font-semibold text-emerald-600">+{{ f.impact }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-400">Aucun facteur positif</p>
      </div>

      <!-- Negative -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h4 class="mb-3 flex items-center gap-2 text-sm font-semibold text-red-600">
          <span class="flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-xs">-</span>
          Facteurs négatifs
        </h4>
        <ul v-if="facteursNegatifs.length > 0" class="space-y-2">
          <li v-for="f in facteursNegatifs" :key="f.label" class="flex items-center justify-between text-sm">
            <span class="text-gray-700">{{ f.label }}</span>
            <span class="font-semibold text-red-500">{{ f.impact }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-400">Aucun facteur négatif</p>
      </div>
    </div>
  </div>
</template>
