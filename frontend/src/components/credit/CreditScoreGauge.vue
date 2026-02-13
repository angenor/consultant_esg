<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
  label?: string
}>()

// SVG semi-circular gauge
const radius = 80
const circumference = Math.PI * radius // half circle
const offset = computed(() => {
  const pct = Math.min(Math.max(props.score, 0), 100) / 100
  return circumference * (1 - pct)
})

const scoreColor = computed(() => {
  if (props.score >= 75) return '#059669'
  if (props.score >= 60) return '#0d9488'
  if (props.score >= 40) return '#d97706'
  return '#dc2626'
})

const scoreLabel = computed(() => {
  if (props.score >= 75) return 'Excellent'
  if (props.score >= 60) return 'Bon'
  if (props.score >= 40) return 'Moyen'
  return 'Faible'
})
</script>

<template>
  <div class="flex flex-col items-center">
    <svg width="200" height="120" viewBox="0 0 200 120">
      <!-- Background arc -->
      <path
        d="M 10 110 A 80 80 0 0 1 190 110"
        fill="none"
        stroke="#e2e8f0"
        stroke-width="12"
        stroke-linecap="round"
      />
      <!-- Score arc -->
      <path
        d="M 10 110 A 80 80 0 0 1 190 110"
        fill="none"
        :stroke="scoreColor"
        stroke-width="12"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        style="transition: stroke-dashoffset 0.8s ease-out"
      />
      <!-- Score text -->
      <text x="100" y="90" text-anchor="middle" class="text-3xl font-bold" fill="#1e293b" font-size="36" font-weight="700">
        {{ score }}
      </text>
      <text x="100" y="110" text-anchor="middle" fill="#94a3b8" font-size="12">/ 100</text>
    </svg>
    <span
      class="mt-1 inline-block rounded-full px-3 py-1 text-xs font-semibold"
      :style="{ backgroundColor: scoreColor + '20', color: scoreColor }"
    >
      {{ scoreLabel }}
    </span>
    <p v-if="label" class="mt-2 text-sm font-medium text-gray-600">{{ label }}</p>
  </div>
</template>
