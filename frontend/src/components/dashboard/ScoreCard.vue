<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps<{
  label: string
  score: number | null
  max?: number
  color?: 'emerald' | 'blue' | 'purple' | 'amber'
  size?: 'sm' | 'lg'
  icon?: 'leaf' | 'users' | 'building' | 'star'
}>()

const max = computed(() => props.max ?? 100)

const pct = computed(() => {
  if (props.score === null) return 0
  return Math.round((props.score / max.value) * 100)
})

const colorClasses = computed(() => {
  const c = props.color ?? 'emerald'
  return {
    emerald: { text: 'text-emerald-600', bg: 'bg-emerald-500', iconBg: 'bg-emerald-100', iconText: 'text-emerald-600' },
    blue: { text: 'text-blue-600', bg: 'bg-blue-500', iconBg: 'bg-blue-100', iconText: 'text-blue-600' },
    purple: { text: 'text-purple-600', bg: 'bg-purple-500', iconBg: 'bg-purple-100', iconText: 'text-purple-600' },
    amber: { text: 'text-amber-600', bg: 'bg-amber-500', iconBg: 'bg-amber-100', iconText: 'text-amber-600' },
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
    class="rounded-2xl border bg-white shadow-sm transition-shadow hover:shadow-md"
    :class="[isLarge ? 'border-amber-200 p-5' : 'border-gray-200 p-4']"
  >
    <div class="flex items-center gap-2.5">
      <div
        v-if="icon"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        :class="[colorClasses.iconBg]"
      >
        <!-- leaf -->
        <svg v-if="icon === 'leaf'" class="h-4 w-4" :class="colorClasses.iconText" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
        </svg>
        <!-- users -->
        <svg v-else-if="icon === 'users'" class="h-4 w-4" :class="colorClasses.iconText" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
        <!-- building -->
        <svg v-else-if="icon === 'building'" class="h-4 w-4" :class="colorClasses.iconText" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
        </svg>
        <!-- star -->
        <svg v-else-if="icon === 'star'" class="h-4 w-4" :class="colorClasses.iconText" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
        </svg>
      </div>
      <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ label }}</p>
    </div>
    <div class="mt-3 flex items-baseline gap-1.5">
      <span
        v-if="score !== null"
        class="font-bold"
        :class="[isLarge ? 'text-4xl' : 'text-3xl', colorClasses.text]"
      >
        {{ displayScore }}
      </span>
      <span v-else class="text-2xl font-bold text-gray-300">&mdash;</span>
      <span class="text-sm font-medium text-gray-400">/{{ max }}</span>
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
