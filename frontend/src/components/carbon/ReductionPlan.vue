<script setup lang="ts">
export interface ReductionAction {
  titre: string
  reduction_kg: number
  cout: string
  delai: string
  categorie: string
}

defineProps<{
  actions: ReductionAction[]
}>()

function categoryLabel(cat: string): string {
  const map: Record<string, string> = {
    quick_win: 'Quick-wins',
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
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
      Plan de réduction
    </h3>

    <div v-if="actions.length === 0" class="py-8 text-center text-sm text-gray-400">
      Aucun plan de réduction disponible
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(action, i) in actions"
        :key="i"
        class="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-3"
      >
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-gray-800">{{ action.titre }}</p>
          <div class="mt-1 flex items-center gap-2">
            <span
              class="inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold"
              :class="categoryColor(action.categorie)"
            >
              {{ categoryLabel(action.categorie) }}
            </span>
            <span class="text-xs text-gray-400">{{ action.delai }}</span>
          </div>
        </div>
        <div class="ml-4 text-right">
          <p class="text-sm font-semibold text-emerald-600">
            -{{ (action.reduction_kg / 1000).toFixed(1) }} t
          </p>
          <p class="text-xs text-gray-400">{{ action.cout }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
