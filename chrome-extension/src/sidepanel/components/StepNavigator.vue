<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <div class="flex gap-1 overflow-x-auto">
      <!-- Pré-étapes (mode intermédiaire) -->
      <button
        v-for="(preStep, index) in preSteps"
        :key="'pre-' + index"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
               whitespace-nowrap transition-colors"
        :class="preStepCompleted?.[index]
          ? 'bg-emerald-50 text-emerald-600'
          : 'bg-amber-50 text-amber-600'"
      >
        <span
          class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
          :class="preStepCompleted?.[index]
            ? 'bg-emerald-500 text-white'
            : 'bg-amber-200 text-amber-700'"
        >
          <svg v-if="preStepCompleted?.[index]" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>P{{ index + 1 }}</span>
        </span>
        {{ preStep.title }}
      </button>

      <!-- Séparateur si pré-étapes -->
      <div v-if="preSteps.length > 0" class="w-px bg-gray-200 mx-1 self-stretch"></div>

      <!-- Étapes de formulaire -->
      <button
        v-for="(step, index) in steps"
        :key="index"
        @click="$emit('select', index)"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
               whitespace-nowrap transition-colors"
        :class="index === currentStep
          ? 'bg-emerald-100 text-emerald-700'
          : index < currentStep
            ? 'bg-gray-100 text-gray-600'
            : 'text-gray-400 hover:bg-gray-50'"
      >
        <!-- Numero / check -->
        <span
          class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
          :class="index < currentStep
            ? 'bg-emerald-500 text-white'
            : index === currentStep
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-200 text-gray-500'"
        >
          <svg v-if="index < currentStep" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>{{ index + 1 }}</span>
        </span>
        {{ step.title }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FundStep } from '@shared/types'
import type { PreStep } from '@shared/access-mode-config'

defineProps<{
  steps: FundStep[]
  currentStep: number
  preSteps?: PreStep[]
  preStepCompleted?: boolean[]
}>()

defineEmits<{
  select: [index: number]
}>()
</script>
