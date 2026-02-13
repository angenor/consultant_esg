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
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <h3 class="text-sm font-semibold text-gray-700">Comparaison Multi-Référentiel</h3>
    <div v-if="sortedScores.length === 0" class="mt-4 text-center text-sm text-gray-400">
      Aucun score disponible
    </div>
    <div v-else class="mt-4 space-y-3">
      <div
        v-for="s in sortedScores"
        :key="s.referentiel_code ?? s.referentiel_nom"
        class="group rounded-lg p-2 transition-colors"
        :class="selectedCode && s.referentiel_code === selectedCode ? 'bg-emerald-50 ring-1 ring-emerald-200' : 'hover:bg-gray-50'"
      >
        <div class="flex items-center justify-between text-sm">
          <span class="font-medium text-gray-700">{{ s.referentiel_nom }}</span>
          <div class="flex items-center gap-2">
            <span
              class="rounded-full px-2 py-0.5 text-xs font-medium"
              :class="niveauBadge(s.niveau)"
            >
              {{ s.niveau }}
            </span>
            <span class="min-w-[3rem] text-right font-bold text-gray-800">
              {{ s.score_global !== null ? Math.round(s.score_global) : '—' }}/100
            </span>
          </div>
        </div>
        <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-gray-100">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="barColor(s.score_global)"
            :style="{ width: (s.score_global ?? 0) + '%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
