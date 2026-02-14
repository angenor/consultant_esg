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

function barBg(score: number): string {
  if (score >= 75) return 'bg-emerald-50'
  if (score >= 60) return 'bg-teal-50'
  if (score >= 40) return 'bg-amber-50'
  return 'bg-red-50'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Score bars -->
    <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div class="mb-5 flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50">
          <svg class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-gray-900">Détail des scores</h3>
          <p class="text-xs text-gray-500">Répartition par composante</p>
        </div>
      </div>

      <div class="space-y-5">
        <!-- Solvabilité -->
        <div>
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">Solvabilité financière</span>
            <span class="rounded-md px-2 py-0.5 text-xs font-bold" :class="[barBg(solvabilite), solvabilite >= 60 ? 'text-emerald-700' : solvabilite >= 40 ? 'text-amber-700' : 'text-red-700']">
              {{ solvabilite }} pts
            </span>
          </div>
          <div class="h-2.5 overflow-hidden rounded-full bg-gray-100">
            <div class="h-full rounded-full transition-all duration-700 ease-out" :class="barColor(solvabilite)" :style="{ width: barWidth(solvabilite) }" />
          </div>
        </div>

        <!-- Impact vert -->
        <div>
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">Impact vert (ESG)</span>
            <span class="rounded-md px-2 py-0.5 text-xs font-bold" :class="[barBg(impactVert), impactVert >= 60 ? 'text-emerald-700' : impactVert >= 40 ? 'text-amber-700' : 'text-red-700']">
              {{ impactVert }} pts
            </span>
          </div>
          <div class="h-2.5 overflow-hidden rounded-full bg-gray-100">
            <div class="h-full rounded-full transition-all duration-700 ease-out" :class="barColor(impactVert)" :style="{ width: barWidth(impactVert) }" />
          </div>
        </div>
      </div>
    </div>

    <!-- Factors -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <!-- Positive -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h4 class="mb-4 flex items-center gap-2.5 text-sm font-semibold text-gray-900">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-sm font-bold text-emerald-600">+</span>
          Facteurs positifs
        </h4>
        <ul v-if="facteursPositifs.length > 0" class="space-y-2.5">
          <li v-for="f in facteursPositifs" :key="f.label" class="flex items-center justify-between rounded-lg bg-emerald-50/50 px-3 py-2 text-sm">
            <span class="text-gray-700">{{ f.label }}</span>
            <span class="font-bold text-emerald-600">+{{ f.impact }}</span>
          </li>
        </ul>
        <p v-else class="rounded-lg bg-gray-50 p-3 text-center text-sm text-gray-400">Aucun facteur positif</p>
      </div>

      <!-- Negative -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h4 class="mb-4 flex items-center gap-2.5 text-sm font-semibold text-gray-900">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-red-100 text-sm font-bold text-red-500">-</span>
          Facteurs négatifs
        </h4>
        <ul v-if="facteursNegatifs.length > 0" class="space-y-2.5">
          <li v-for="f in facteursNegatifs" :key="f.label" class="flex items-center justify-between rounded-lg bg-red-50/50 px-3 py-2 text-sm">
            <span class="text-gray-700">{{ f.label }}</span>
            <span class="font-bold text-red-500">{{ f.impact }}</span>
          </li>
        </ul>
        <p v-else class="rounded-lg bg-gray-50 p-3 text-center text-sm text-gray-400">Aucun facteur négatif</p>
      </div>
    </div>
  </div>
</template>
