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
      borderWidth: 2,
      borderColor: '#fff',
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const, labels: { padding: 16, usePointStyle: true } },
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
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
      Répartition par source
    </h3>
    <div class="mx-auto h-64 w-64">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
