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
      backgroundColor: ['#059669', '#94a3b8'],
      borderRadius: 6,
      barThickness: 48,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: { legend: { display: false } },
  scales: {
    x: {
      beginAtZero: true,
      grid: { color: '#f1f5f9' },
      ticks: { color: '#94a3b8', callback: (v: any) => `${v} t` },
    },
    y: {
      grid: { display: false },
      ticks: { color: '#374151', font: { weight: 'bold' as const } },
    },
  },
}

const isBelow = computed(() => props.entrepriseKg <= props.moyenneSecteurKg)
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
      Comparaison sectorielle
    </h3>
    <div class="h-40">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div class="mt-3 text-center">
      <span
        class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
        :class="isBelow ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
      >
        {{ isBelow ? 'En dessous de la moyenne sectorielle' : 'Au-dessus de la moyenne sectorielle' }}
      </span>
    </div>
  </div>
</template>
