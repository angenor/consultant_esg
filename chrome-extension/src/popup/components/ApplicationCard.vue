<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3 hover:border-emerald-300
              transition-colors cursor-pointer" @click="openApplication">
    <div class="flex items-start gap-2">
      <div class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold"
           :class="statusClasses">
        {{ application.progress_pct }}%
      </div>
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-medium text-gray-800 truncate">
          {{ application.fonds_nom }}
        </h4>
        <p class="text-xs text-gray-500 truncate">{{ application.fonds_institution }}</p>
        <!-- Barre de progression -->
        <div class="mt-1.5 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
               :class="progressBarColor"
               :style="{ width: application.progress_pct + '%' }">
          </div>
        </div>
      </div>
      <span class="text-xs px-2 py-0.5 rounded-full" :class="statusBadgeClasses">
        {{ statusLabel }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FundApplication } from '@shared/types'
import { APPLICATION_STATUSES } from '@shared/constants'

const props = defineProps<{
  application: FundApplication
}>()

const statusConfig = computed(() => APPLICATION_STATUSES[props.application.status])
const statusLabel = computed(() => statusConfig.value?.label || props.application.status)

const statusClasses = computed(() => {
  const color = statusConfig.value?.color || 'gray'
  return {
    [`bg-${color}-100`]: true,
    [`text-${color}-700`]: true,
  }
})

const progressBarColor = computed(() => {
  const pct = props.application.progress_pct
  if (pct >= 75) return 'bg-emerald-500'
  if (pct >= 50) return 'bg-blue-500'
  if (pct >= 25) return 'bg-amber-500'
  return 'bg-gray-400'
})

const statusBadgeClasses = computed(() => {
  const color = statusConfig.value?.color || 'gray'
  return `bg-${color}-100 text-${color}-700`
})

function openApplication() {
  if (props.application.url_candidature) {
    chrome.tabs.create({ url: props.application.url_candidature })
  }
}
</script>
