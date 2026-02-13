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
      backgroundColor: 'rgba(16, 185, 129, 0.2)',
      borderColor: 'rgb(16, 185, 129)',
      borderWidth: 2,
      pointBackgroundColor: 'rgb(16, 185, 129)',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 5,
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
      },
      grid: { color: 'rgba(0,0,0,0.06)' },
      angleLines: { color: 'rgba(0,0,0,0.06)' },
      pointLabels: {
        font: { size: 12, weight: 'bold' as const },
        color: '#374151',
      },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${ctx.label}: ${ctx.raw}/100`,
      },
    },
  },
}
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <h3 class="text-sm font-semibold text-gray-700">Radar ESG</h3>
    <div class="mt-2 h-64">
      <Radar :data="chartData" :options="chartOptions as any" />
    </div>
  </div>
</template>
