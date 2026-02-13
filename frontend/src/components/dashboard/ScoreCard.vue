<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'

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

// Animated score counter
const displayScore = ref(0)
let animFrame = 0

function animateScore(target: number) {
  cancelAnimationFrame(animFrame)
  const start = displayScore.value
  const diff = target - start
  if (diff === 0) return
  const duration = 600
  const startTime = performance.now()

  function step(now: number) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    // ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    displayScore.value = Math.round(start + diff * eased)
    if (progress < 1) {
      animFrame = requestAnimationFrame(step)
    }
  }
  animFrame = requestAnimationFrame(step)
}

watch(() => props.score, (val) => {
  if (val !== null) animateScore(val)
}, { immediate: true })

onMounted(() => {
  if (props.score !== null) {
    displayScore.value = 0
    animateScore(props.score)
  }
})
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
        class="font-bold"
        :class="[isLarge ? 'text-4xl' : 'text-3xl', colorClasses.text]"
      >
        {{ displayScore }}
      </span>
      <span v-else class="text-2xl font-bold text-gray-300">&mdash;</span>
      <span class="text-sm text-gray-400">/{{ max }}</span>
    </div>
    <!-- Mini bar -->
    <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="colorClasses.bg"
        :style="{ width: pct + '%' }"
      />
    </div>
  </div>
</template>
