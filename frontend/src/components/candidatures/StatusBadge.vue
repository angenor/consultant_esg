<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  brouillon: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Brouillon' },
  en_cours: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'En cours' },
  soumise: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Soumise' },
  acceptee: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Acceptée' },
  refusee: { bg: 'bg-red-100', text: 'text-red-700', label: 'Refusée' },
  abandonnee: { bg: 'bg-gray-100', text: 'text-gray-400', label: 'Abandonnée' },
}

const config = computed(() => STATUS_CONFIG[props.status] || STATUS_CONFIG.brouillon)
</script>

<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full"
    :class="[config.bg, config.text]"
  >
    {{ config.label }}
  </span>
</template>
