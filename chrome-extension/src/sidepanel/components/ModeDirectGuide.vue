<template>
  <div class="px-4 py-3 bg-emerald-50 border-b border-emerald-100">
    <div class="flex items-center gap-2 mb-2">
      <span class="bg-emerald-100 text-emerald-700 text-xs px-2 py-1 rounded-full font-medium">
        Accès direct
      </span>
    </div>
    <p class="text-xs text-gray-600 mb-2">
      Ce fonds accepte les candidatures directes. Suivez les étapes ci-dessous pour compléter votre dossier.
    </p>
    <!-- Progression linéaire -->
    <div class="flex items-center gap-1">
      <div v-for="(step, i) in steps" :key="i"
           class="flex-1 h-1.5 rounded-full transition-colors"
           :class="i < currentStep ? 'bg-emerald-500' : i === currentStep ? 'bg-emerald-300' : 'bg-gray-200'">
      </div>
    </div>
    <p class="text-[10px] text-gray-400 mt-1">
      Étape {{ currentStep + 1 }} sur {{ steps.length }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { FundStep } from '@shared/types'

defineProps<{
  steps: FundStep[]
  currentStep: number
}>()
</script>
