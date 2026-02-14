<script setup lang="ts">
import { computed } from 'vue'

export interface ScoreEntry {
  referentiel_nom: string
  referentiel_code: string | null
  score_global: number | null
  niveau: string
}

const props = defineProps<{
  scores: ScoreEntry[]
  selectedCode: string | null
}>()

function barColor(score: number | null): string {
  if (score === null) return 'bg-gray-300'
  if (score >= 80) return 'bg-emerald-500'
  if (score >= 60) return 'bg-teal-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

function niveauBadge(niveau: string): string {
  if (niveau === 'Excellent') return 'bg-emerald-100 text-emerald-700'
  if (niveau === 'Bon') return 'bg-teal-100 text-teal-700'
  if (niveau === 'À améliorer') return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}

const sortedScores = computed(() =>
  [...props.scores].sort((a, b) => (b.score_global ?? 0) - (a.score_global ?? 0))
)
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50">
        <svg class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Comparaison Multi-Référentiel</h3>
        <p class="text-xs text-gray-500">Scores par cadre de référence</p>
      </div>
    </div>

    <div v-if="sortedScores.length === 0" class="rounded-xl bg-gray-50 py-8 text-center text-sm text-gray-400">
      Aucun score disponible
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="s in sortedScores"
        :key="s.referentiel_code ?? s.referentiel_nom"
        class="rounded-xl p-3 transition-colors"
        :class="selectedCode && s.referentiel_code === selectedCode ? 'bg-emerald-50 ring-1 ring-emerald-200' : 'hover:bg-gray-50'"
      >
        <div class="flex items-center justify-between text-sm">
          <span class="font-semibold text-gray-800">{{ s.referentiel_nom }}</span>
          <div class="flex items-center gap-2">
            <span
              class="rounded-md px-2 py-0.5 text-[11px] font-semibold"
              :class="niveauBadge(s.niveau)"
            >
              {{ s.niveau }}
            </span>
            <span class="min-w-[3rem] text-right font-bold text-gray-900">
              {{ s.score_global !== null ? Math.round(s.score_global) : '—' }}
            </span>
          </div>
        </div>
        <div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="barColor(s.score_global)"
            :style="{ width: (s.score_global ?? 0) + '%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
