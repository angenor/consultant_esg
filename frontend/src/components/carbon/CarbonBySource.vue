<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  sources: Record<string, number>
}>()

const COLORS = ['#059669', '#0ea5e9', '#8b5cf6', '#d97706', '#ec4899', '#64748b']

const total = computed(() => Object.values(props.sources).reduce((a, b) => a + b, 0))

const chartData = computed(() => ({
  labels: Object.keys(props.sources),
  datasets: [
    {
      data: Object.values(props.sources),
      backgroundColor: COLORS.slice(0, Object.keys(props.sources).length),
      borderWidth: 3,
      borderColor: '#fff',
      hoverBorderWidth: 0,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '55%',
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const val = ctx.parsed
          const pct = total.value > 0 ? ((val / total.value) * 100).toFixed(1) : '0'
          return ` ${ctx.label}: ${val.toFixed(0)} kg CO₂ (${pct}%)`
        },
      },
    },
  },
}

const sortedSources = computed(() => {
  return Object.entries(props.sources)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value], i) => ({
      label,
      value,
      pct: total.value > 0 ? ((value / total.value) * 100).toFixed(0) : '0',
      color: COLORS[i] || COLORS[COLORS.length - 1],
    }))
})
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50">
        <svg class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Répartition par source</h3>
        <p class="text-xs text-gray-500">Détail des émissions par catégorie</p>
      </div>
    </div>

    <div class="flex flex-col items-center gap-6 sm:flex-row">
      <div class="h-48 w-48 shrink-0">
        <Pie :data="chartData" :options="chartOptions" />
      </div>
      <div class="flex-1 space-y-2.5">
        <div
          v-for="src in sortedSources" :key="src.label"
          class="flex items-center gap-3"
        >
          <span class="h-3 w-3 shrink-0 rounded-full" :style="{ backgroundColor: src.color }" />
          <span class="flex-1 text-sm text-gray-700">{{ src.label }}</span>
          <span class="text-sm font-semibold text-gray-900">{{ src.pct }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>
