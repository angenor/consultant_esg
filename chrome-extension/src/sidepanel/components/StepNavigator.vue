<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <div class="flex gap-1 overflow-x-auto">
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

defineProps<{
  steps: FundStep[]
  currentStep: number
}>()

defineEmits<{
  select: [index: number]
}>()
</script>
