<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

export interface HistoryPoint {
  referentiel_code: string | null
  referentiel_nom: string
  score_global: number | null
  created_at: string
}

const props = defineProps<{
  history: HistoryPoint[]
  selectedCode: string | null
}>()

const COLORS = [
  { border: 'rgb(16, 185, 129)', bg: 'rgba(16, 185, 129, 0.08)' },
  { border: 'rgb(59, 130, 246)', bg: 'rgba(59, 130, 246, 0.08)' },
  { border: 'rgb(168, 85, 247)', bg: 'rgba(168, 85, 247, 0.08)' },
  { border: 'rgb(245, 158, 11)', bg: 'rgba(245, 158, 11, 0.08)' },
  { border: 'rgb(239, 68, 68)', bg: 'rgba(239, 68, 68, 0.08)' },
]

const chartData = computed(() => {
  const groups: Record<string, { nom: string; points: { date: string; score: number }[] }> = {}

  for (const h of props.history) {
    const key = h.referentiel_code ?? h.referentiel_nom
    if (props.selectedCode && h.referentiel_code !== props.selectedCode) continue
    if (!groups[key]) groups[key] = { nom: h.referentiel_nom, points: [] }
    if (h.score_global !== null) {
      groups[key].points.push({
        date: new Date(h.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
        score: h.score_global,
      })
    }
  }

  const allDates = [...new Set(Object.values(groups).flatMap((g) => g.points.map((p) => p.date)))]

  const datasets = Object.entries(groups).map(([_key, group], idx) => {
    const color = COLORS[idx % COLORS.length]!
    return {
      label: group.nom,
      data: allDates.map((d) => group.points.find((p) => p.date === d)?.score ?? null),
      borderColor: color.border,
      backgroundColor: color.bg,
      fill: Object.keys(groups).length === 1,
      tension: 0.4,
      pointRadius: 5,
      pointBorderWidth: 2,
      pointBackgroundColor: '#fff',
      pointHoverRadius: 7,
      spanGaps: true,
    }
  })

  return { labels: allDates, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      ticks: { stepSize: 20, color: '#94a3b8', font: { size: 11 } },
      grid: { color: '#f1f5f9' },
      border: { display: false },
    },
    x: {
      grid: { display: false },
      ticks: { color: '#94a3b8', font: { size: 11 } },
      border: { display: false },
    },
  },
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: { boxWidth: 12, padding: 16, font: { size: 11 }, usePointStyle: true },
    },
    tooltip: {
      backgroundColor: '#1e293b',
      padding: 10,
      cornerRadius: 8,
      callbacks: {
        label: (ctx: any) => `${ctx.dataset.label}: ${ctx.raw}/100`,
      },
    },
  },
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
        <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Évolution des Scores</h3>
        <p class="text-xs text-gray-500">Historique de vos évaluations ESG</p>
      </div>
    </div>

    <div v-if="history.length === 0" class="rounded-xl bg-gray-50 py-10 text-center">
      <svg class="mx-auto h-8 w-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
      <p class="mt-2 text-sm text-gray-400">Pas encore d'historique</p>
    </div>

    <div v-else class="h-72">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
