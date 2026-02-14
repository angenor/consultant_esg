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
    <svg width="240" height="140" viewBox="0 0 240 140">
      <!-- Background arc -->
      <path
        d="M 20 130 A 100 100 0 0 1 220 130"
        fill="none"
        stroke="#e2e8f0"
        stroke-width="14"
        stroke-linecap="round"
      />
      <!-- Score arc -->
      <path
        d="M 20 130 A 100 100 0 0 1 220 130"
        fill="none"
        :stroke="scoreColor"
        stroke-width="14"
        stroke-linecap="round"
        :stroke-dasharray="Math.PI * 100"
        :stroke-dashoffset="Math.PI * 100 * (1 - Math.min(Math.max(score, 0), 100) / 100)"
        class="gauge-arc"
      />
      <!-- Score text -->
      <text x="120" y="105" text-anchor="middle" fill="#111827" font-size="44" font-weight="800">
        {{ score }}
      </text>
      <text x="120" y="128" text-anchor="middle" fill="#9ca3af" font-size="13" font-weight="500">sur 100</text>
    </svg>
    <span
      class="mt-2 inline-block rounded-full px-4 py-1.5 text-xs font-bold tracking-wide uppercase"
      :style="{ backgroundColor: scoreColor + '15', color: scoreColor }"
    >
      {{ scoreLabel }}
    </span>
    <p v-if="label" class="mt-2 text-sm font-medium text-gray-600">{{ label }}</p>
  </div>
</template>

<style scoped>
.gauge-arc {
  transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
