<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3">
    <div class="flex items-center gap-2">
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-medium text-gray-800 truncate">{{ fonds.nom }}</h4>
        <p class="text-xs text-gray-500">
          {{ fonds.institution }} · {{ formatMontant(fonds.montant_min, fonds.montant_max, fonds.devise) }}
        </p>
      </div>
      <a v-if="fonds.url_source"
         :href="fonds.url_source"
         target="_blank"
         class="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-lg
                hover:bg-emerald-100 transition-colors whitespace-nowrap">
        Postuler
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FondsVert } from '@shared/types'

defineProps<{
  fonds: FondsVert
}>()

function formatMontant(min: number | null, max: number | null, devise: string): string {
  const fmt = (n: number) => {
    if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}Md`
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
    return n.toString()
  }

  if (min && max) return `${fmt(min)} - ${fmt(max)} ${devise}`
  if (min) return `Min ${fmt(min)} ${devise}`
  if (max) return `Max ${fmt(max)} ${devise}`
  return devise
}
</script>
