<script setup lang="ts">
import { computed } from 'vue'
import { Radar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps<{
  scoreE: number | null
  scoreS: number | null
  scoreG: number | null
  label?: string
}>()

const chartData = computed(() => ({
  labels: ['Environnement', 'Social', 'Gouvernance'],
  datasets: [
    {
      label: props.label ?? 'Score ESG',
      data: [props.scoreE ?? 0, props.scoreS ?? 0, props.scoreG ?? 0],
      backgroundColor: 'rgba(16, 185, 129, 0.15)',
      borderColor: 'rgb(16, 185, 129)',
      borderWidth: 2,
      pointBackgroundColor: '#fff',
      pointBorderColor: 'rgb(16, 185, 129)',
      pointBorderWidth: 2,
      pointRadius: 6,
      pointHoverRadius: 8,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      beginAtZero: true,
      max: 100,
      ticks: {
        stepSize: 20,
        font: { size: 10 },
        backdropColor: 'transparent',
        color: '#94a3b8',
      },
      grid: { color: 'rgba(0,0,0,0.05)' },
      angleLines: { color: 'rgba(0,0,0,0.05)' },
      pointLabels: {
        font: { size: 12, weight: 'bold' as const },
        color: '#374151',
      },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1e293b',
      padding: 10,
      cornerRadius: 8,
      callbacks: {
        label: (ctx: any) => `${ctx.label}: ${ctx.raw}/100`,
      },
    },
  },
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50">
        <svg class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Radar ESG</h3>
        <p v-if="label" class="text-xs text-gray-500">{{ label }}</p>
      </div>
    </div>
    <div class="h-64">
      <Radar :data="chartData" :options="chartOptions as any" />
    </div>
  </div>
</template>
