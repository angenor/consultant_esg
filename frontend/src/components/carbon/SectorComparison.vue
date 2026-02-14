<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{
  entrepriseKg: number
  moyenneSecteurKg: number
  secteur: string
}>()

const chartData = computed(() => ({
  labels: ['Mon entreprise', `Moyenne ${props.secteur}`],
  datasets: [
    {
      data: [props.entrepriseKg / 1000, props.moyenneSecteurKg / 1000],
      backgroundColor: [isBelow.value ? '#059669' : '#f59e0b', '#cbd5e1'],
      borderRadius: 8,
      barThickness: 40,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1e293b',
      padding: 10,
      cornerRadius: 8,
      callbacks: {
        label: (ctx: any) => ` ${ctx.parsed.x.toFixed(1)} tCO₂eq`,
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      grid: { color: '#f1f5f9' },
      ticks: { color: '#94a3b8', callback: (v: any) => `${v} t` },
      border: { display: false },
    },
    y: {
      grid: { display: false },
      ticks: { color: '#374151', font: { weight: 'bold' as const, size: 12 } },
      border: { display: false },
    },
  },
}

const isBelow = computed(() => props.entrepriseKg <= props.moyenneSecteurKg)
const diffPct = computed(() => {
  if (props.moyenneSecteurKg === 0) return 0
  return Math.abs(((props.entrepriseKg - props.moyenneSecteurKg) / props.moyenneSecteurKg) * 100)
})
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg" :class="isBelow ? 'bg-emerald-50' : 'bg-amber-50'">
        <svg class="h-5 w-5" :class="isBelow ? 'text-emerald-600' : 'text-amber-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5-4.5L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Comparaison sectorielle</h3>
        <p class="text-xs text-gray-500">Votre position par rapport au secteur {{ secteur }}</p>
      </div>
    </div>

    <div class="h-36">
      <Bar :data="chartData" :options="chartOptions" />
    </div>

    <div class="mt-4 flex items-center justify-center gap-2">
      <div
        class="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold"
        :class="isBelow ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
      >
        <svg v-if="isBelow" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        {{ isBelow ? `${diffPct.toFixed(0)}% en dessous` : `${diffPct.toFixed(0)}% au-dessus` }} de la moyenne
      </div>
    </div>
  </div>
</template>
