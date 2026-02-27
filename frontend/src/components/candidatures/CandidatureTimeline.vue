<script setup lang="ts">
import type { TimelineStep } from '../../stores/candidatures'

defineProps<{
  steps: TimelineStep[]
}>()

defineEmits<{
  action: [action: { type: string; label: string }]
}>()

function stepIconClasses(status: string) {
  switch (status) {
    case 'done':
      return 'bg-emerald-500 border-emerald-500'
    case 'current':
      return 'bg-blue-500 border-blue-500 ring-4 ring-blue-100'
    default:
      return 'bg-white border-gray-300'
  }
}

function stepTextClasses(status: string) {
  switch (status) {
    case 'done':
      return 'text-gray-500'
    case 'current':
      return 'text-gray-900 font-semibold'
    default:
      return 'text-gray-400'
  }
}
</script>

<template>
  <div class="relative">
    <!-- Ligne verticale -->
    <div class="absolute left-[15px] top-2 bottom-2 w-0.5 bg-gray-200" />

    <div v-for="(step, index) in steps" :key="index" class="relative pl-10 pb-6 last:pb-0">
      <!-- Icône de statut -->
      <div class="absolute left-[9px] top-1 w-3.5 h-3.5 rounded-full border-2 z-10" :class="stepIconClasses(step.status)">
        <!-- Checkmark for done -->
        <svg v-if="step.status === 'done'" class="w-2.5 h-2.5 text-white -mt-px -ml-px" viewBox="0 0 12 12" fill="none">
          <path d="M3 6l2.5 2.5L9 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>

      <!-- Contenu -->
      <div
        class="border rounded-lg p-3 transition-colors"
        :class="step.status === 'current' ? 'border-blue-200 bg-blue-50' : 'bg-white'"
      >
        <div class="flex justify-between items-start gap-2">
          <h4 class="text-sm" :class="stepTextClasses(step.status)">
            {{ step.title }}
          </h4>
          <span class="text-xs text-gray-400 shrink-0">
            {{ step.date || step.estimated || '' }}
          </span>
        </div>

        <p v-if="step.description" class="text-xs text-gray-500 mt-1">
          {{ step.description }}
        </p>

        <!-- Actions -->
        <div v-if="step.actions && step.actions.length > 0" class="mt-2 flex gap-2">
          <button
            v-for="action in step.actions"
            :key="action.type"
            @click.stop="$emit('action', action)"
            class="text-xs text-emerald-600 hover:text-emerald-700 hover:underline font-medium"
          >
            {{ action.label }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
