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
  { border: 'rgb(16, 185, 129)', bg: 'rgba(16, 185, 129, 0.1)' },
  { border: 'rgb(59, 130, 246)', bg: 'rgba(59, 130, 246, 0.1)' },
  { border: 'rgb(168, 85, 247)', bg: 'rgba(168, 85, 247, 0.1)' },
  { border: 'rgb(245, 158, 11)', bg: 'rgba(245, 158, 11, 0.1)' },
  { border: 'rgb(239, 68, 68)', bg: 'rgba(239, 68, 68, 0.1)' },
]

const chartData = computed(() => {
  // Grouper par referentiel
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

  // Toutes les dates uniques
  const allDates = [...new Set(Object.values(groups).flatMap((g) => g.points.map((p) => p.date)))]

  const datasets = Object.entries(groups).map(([_key, group], idx) => {
    const color = COLORS[idx % COLORS.length]!
    return {
      label: group.nom,
      data: allDates.map((d) => group.points.find((p) => p.date === d)?.score ?? null),
      borderColor: color.border,
      backgroundColor: color.bg,
      fill: Object.keys(groups).length === 1,
      tension: 0.3,
      pointRadius: 4,
      pointBorderWidth: 2,
      pointBackgroundColor: '#fff',
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
      ticks: { stepSize: 20 },
      grid: { color: 'rgba(0,0,0,0.04)' },
    },
    x: {
      grid: { display: false },
    },
  },
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: { boxWidth: 12, padding: 16, font: { size: 11 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${ctx.dataset.label}: ${ctx.raw}/100`,
      },
    },
  },
}
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <h3 class="text-sm font-semibold text-gray-700">Évolution des Scores</h3>
    <div v-if="history.length === 0" class="flex h-48 items-center justify-center text-sm text-gray-400">
      Pas encore d'historique
    </div>
    <div v-else class="mt-2 h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
