<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <!-- Badge mode d'accès -->
    <div class="flex items-center gap-2 mb-2">
      <span class="text-xs px-2 py-1 rounded-full font-medium"
            :class="badgeClasses">
        {{ modeConfig.label }}
      </span>
      <span v-if="modeConfig.requires_intermediary"
            class="text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
        Intermédiaire requis
      </span>
    </div>

    <!-- Description du mode -->
    <p class="text-xs text-gray-500 mb-3">{{ modeConfig.description }}</p>

    <!-- Intermédiaires connus -->
    <div v-if="intermediaires.length > 0" class="mb-3">
      <h4 class="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
        Intermédiaires
      </h4>
      <div v-for="inter in intermediaires" :key="inter.nom"
           class="flex items-center gap-2 text-xs text-gray-600 py-1">
        <svg class="w-3 h-3 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span>{{ inter.nom }}</span>
        <span class="text-[10px] text-gray-400">{{ inter.type }} · {{ inter.pays }}</span>
        <a v-if="inter.contact" :href="inter.contact" target="_blank"
           class="text-blue-500 hover:text-blue-700 ml-auto">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>

    <!-- Pré-étapes (si mode intermédiaire) -->
    <div v-if="modeConfig.preSteps.length > 0" class="space-y-2">
      <h4 class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
        Étapes préalables
      </h4>
      <div v-for="(preStep, i) in modeConfig.preSteps" :key="i"
           class="flex items-start gap-2 p-2 rounded-lg transition-colors"
           :class="preStepCompleted[i] ? 'bg-emerald-50' : 'bg-gray-50'">
        <button @click="togglePreStep(i)"
                class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors"
                :class="preStepCompleted[i]
                  ? 'bg-emerald-500 border-emerald-500'
                  : 'border-gray-300 hover:border-emerald-400'">
          <svg v-if="preStepCompleted[i]" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </button>
        <div>
          <p class="text-xs font-medium" :class="preStepCompleted[i] ? 'text-emerald-700 line-through' : 'text-gray-700'">
            {{ preStep.title }}
          </p>
          <p class="text-[11px] text-gray-500">{{ preStep.description }}</p>
        </div>
      </div>

      <!-- Résumé pré-étapes -->
      <div class="text-[10px] text-gray-400 text-right">
        {{ completedCount }}/{{ modeConfig.preSteps.length }} complétées
      </div>
    </div>

    <!-- Conseil spécifique au mode -->
    <div v-if="currentTip" class="mt-3 bg-blue-50 rounded-lg p-2">
      <div class="flex gap-1.5">
        <svg class="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-[11px] text-blue-700">{{ currentTip }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getAccessModeConfig } from '@shared/access-mode-config'

const props = defineProps<{
  modeAcces: string | null | undefined
  intermediaires?: { nom: string; type: string; pays: string; contact: string | null }[]
}>()

const emit = defineEmits<{
  'pre-steps-change': [completed: boolean[]]
}>()

const modeConfig = computed(() => getAccessModeConfig(props.modeAcces))

const preStepCompleted = ref<boolean[]>([])

// Réinitialiser quand le mode change
watch(
  () => props.modeAcces,
  () => {
    preStepCompleted.value = new Array(modeConfig.value.preSteps.length).fill(false)
  },
  { immediate: true },
)

const completedCount = computed(() =>
  preStepCompleted.value.filter(Boolean).length
)

const intermediaires = computed(() => props.intermediaires || [])

// Rotation des tips
const tipIndex = ref(0)
const currentTip = computed(() => {
  const tips = modeConfig.value.tips
  if (!tips.length) return null
  return tips[tipIndex.value % tips.length]
})

// Changer de tip toutes les 15 secondes
let tipInterval: ReturnType<typeof setInterval> | null = null
watch(
  () => modeConfig.value.tips.length,
  (len) => {
    if (tipInterval) clearInterval(tipInterval)
    tipIndex.value = 0
    if (len > 1) {
      tipInterval = setInterval(() => {
        tipIndex.value = (tipIndex.value + 1) % len
      }, 15000)
    }
  },
  { immediate: true },
)

function togglePreStep(index: number) {
  preStepCompleted.value[index] = !preStepCompleted.value[index]
  emit('pre-steps-change', [...preStepCompleted.value])
}

const COLOR_MAP: Record<string, { bg: string; text: string }> = {
  emerald: { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  blue: { bg: 'bg-blue-100', text: 'text-blue-700' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-700' },
  amber: { bg: 'bg-amber-100', text: 'text-amber-700' },
  indigo: { bg: 'bg-indigo-100', text: 'text-indigo-700' },
  cyan: { bg: 'bg-cyan-100', text: 'text-cyan-700' },
}

const badgeClasses = computed(() => {
  const c = COLOR_MAP[modeConfig.value.color] || COLOR_MAP.emerald
  return `${c.bg} ${c.text}`
})
</script>
