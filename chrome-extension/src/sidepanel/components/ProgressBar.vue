<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <div class="flex items-center justify-between mb-1">
      <span class="text-xs font-medium text-gray-600">
        Etape {{ currentStep + 1 }} / {{ totalSteps }}
      </span>
      <span class="text-xs font-bold text-emerald-600">{{ progressPct }}%</span>
    </div>
    <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        class="h-full bg-emerald-500 rounded-full transition-all duration-500 ease-out"
        :style="{ width: progressPct + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentStep: number
  totalSteps: number
  progressPct: number
}>()
</script>
