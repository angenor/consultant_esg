<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  score: number | null
  max?: number
  color?: 'emerald' | 'blue' | 'purple' | 'amber'
  size?: 'sm' | 'lg'
}>()

const max = computed(() => props.max ?? 100)

const pct = computed(() => {
  if (props.score === null) return 0
  return Math.round((props.score / max.value) * 100)
})

const colorClasses = computed(() => {
  const c = props.color ?? 'emerald'
  return {
    emerald: { text: 'text-emerald-600', bg: 'bg-emerald-500', ring: 'ring-emerald-100' },
    blue: { text: 'text-blue-600', bg: 'bg-blue-500', ring: 'ring-blue-100' },
    purple: { text: 'text-purple-600', bg: 'bg-purple-500', ring: 'ring-purple-100' },
    amber: { text: 'text-amber-600', bg: 'bg-amber-500', ring: 'ring-amber-100' },
  }[c]
})

const isLarge = computed(() => props.size === 'lg')
</script>

<template>
  <div
    class="rounded-xl border bg-white shadow-sm transition-shadow hover:shadow-md"
    :class="[isLarge ? 'border-emerald-200 p-5' : 'border-gray-200 p-4']"
  >
    <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ label }}</p>
    <div class="mt-2 flex items-baseline gap-1">
      <span
        v-if="score !== null"
        class="text-3xl font-bold"
        :class="[isLarge ? 'text-4xl' : 'text-3xl', colorClasses.text]"
      >
        {{ Math.round(score) }}
      </span>
      <span v-else class="text-2xl font-bold text-gray-300">—</span>
      <span class="text-sm text-gray-400">/{{ max }}</span>
    </div>
    <!-- Mini bar -->
    <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
      <div
        class="h-full rounded-full transition-all duration-500"
        :class="colorClasses.bg"
        :style="{ width: pct + '%' }"
      />
    </div>
  </div>
</template>
