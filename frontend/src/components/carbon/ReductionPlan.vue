<script setup lang="ts">
import { computed } from 'vue'

export interface ReductionAction {
  titre: string
  reduction_kg: number
  cout: string
  delai: string
  categorie: string
}

const props = defineProps<{
  actions: ReductionAction[]
}>()

const totalReduction = computed(() =>
  props.actions.reduce((sum, a) => sum + a.reduction_kg, 0)
)

function categoryLabel(cat: string): string {
  const map: Record<string, string> = {
    quick_win: 'Quick-win',
    moyen_terme: 'Moyen terme',
    long_terme: 'Long terme',
  }
  return map[cat] || cat
}

function categoryColor(cat: string): string {
  const map: Record<string, string> = {
    quick_win: 'bg-emerald-100 text-emerald-700',
    moyen_terme: 'bg-blue-100 text-blue-700',
    long_terme: 'bg-amber-100 text-amber-700',
  }
  return map[cat] || 'bg-gray-100 text-gray-700'
}

function categoryBorder(cat: string): string {
  const map: Record<string, string> = {
    quick_win: 'border-l-emerald-400',
    moyen_terme: 'border-l-blue-400',
    long_terme: 'border-l-amber-400',
  }
  return map[cat] || 'border-l-gray-300'
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50">
          <svg class="h-5 w-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-gray-900">Plan de réduction</h3>
          <p class="text-xs text-gray-500">Actions pour diminuer vos émissions</p>
        </div>
      </div>
      <div v-if="actions.length > 0" class="rounded-lg bg-emerald-50 px-3 py-1.5">
        <span class="text-sm font-bold text-emerald-700">-{{ (totalReduction / 1000).toFixed(1) }} t</span>
        <span class="ml-1 text-xs text-emerald-600">potentiel</span>
      </div>
    </div>

    <div v-if="actions.length === 0" class="rounded-xl bg-gray-50 py-10 text-center">
      <svg class="mx-auto h-8 w-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
      <p class="mt-2 text-sm text-gray-400">Aucun plan de réduction disponible</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(action, i) in actions"
        :key="i"
        class="flex items-center justify-between rounded-xl border border-gray-100 border-l-4 bg-white px-4 py-3.5 transition-colors hover:bg-gray-50"
        :class="categoryBorder(action.categorie)"
      >
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold text-gray-900">{{ action.titre }}</p>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <span
              class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold"
              :class="categoryColor(action.categorie)"
            >
              {{ categoryLabel(action.categorie) }}
            </span>
            <span class="inline-flex items-center gap-1 text-xs text-gray-400">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ action.delai }}
            </span>
            <span v-if="action.cout" class="inline-flex items-center gap-1 text-xs text-gray-400">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75" />
              </svg>
              {{ action.cout }}
            </span>
          </div>
        </div>
        <div class="ml-4 shrink-0">
          <div class="rounded-lg bg-emerald-50 px-2.5 py-1.5 text-right">
            <span class="text-sm font-bold text-emerald-600">-{{ (action.reduction_kg / 1000).toFixed(1) }} t</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
