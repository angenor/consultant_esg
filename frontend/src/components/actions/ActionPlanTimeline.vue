<script setup lang="ts">
import { computed } from 'vue'
import type { ActionItemData } from './ActionItemCard.vue'
import ActionItemCard from './ActionItemCard.vue'

const props = withDefaults(defineProps<{
  items: ActionItemData[]
  unitImpact?: string
}>(), {
  unitImpact: 'pts ESG',
})

const emit = defineEmits<{
  toggleStatus: [id: string, newStatus: string]
}>()

// Normalise les valeurs de priorité inconnues vers les clés attendues
const normalizePriorite = (p: string): string => {
  const map: Record<string, string> = {
    haute: 'quick_win',
    moyenne: 'moyen_terme',
    basse: 'long_terme',
  }
  return map[p] || p
}

const grouped = computed(() => {
  const groups: Record<string, ActionItemData[]> = {
    quick_win: [],
    moyen_terme: [],
    long_terme: [],
  }
  for (const item of props.items) {
    const cat = normalizePriorite(item.priorite || 'moyen_terme')
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return groups
})

const categoryMeta: Record<string, { label: string; sublabel: string; color: string; iconBg: string; iconColor: string }> = {
  quick_win: { label: 'Quick-wins', sublabel: '< 3 mois', color: 'border-emerald-300', iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600' },
  moyen_terme: { label: 'Moyen terme', sublabel: '3-12 mois', color: 'border-blue-300', iconBg: 'bg-blue-100', iconColor: 'text-blue-600' },
  long_terme: { label: 'Long terme', sublabel: '> 12 mois', color: 'border-amber-300', iconBg: 'bg-amber-100', iconColor: 'text-amber-600' },
}

function completedCount(key: string): number {
  return (grouped.value[key] || []).filter(i => i.statut === 'fait').length
}
</script>

<template>
  <div class="space-y-8">
    <div v-for="(cat, key) in categoryMeta" :key="key">
      <div v-if="grouped[key] && grouped[key].length > 0">
        <!-- Category header -->
        <div class="mb-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="h-1 w-8 rounded-full" :class="cat.iconBg.replace('bg-', 'bg-').replace('100', '400')" :style="{ backgroundColor: cat.iconColor === 'text-emerald-600' ? '#34d399' : cat.iconColor === 'text-blue-600' ? '#60a5fa' : '#fbbf24' }" />
            <h3 class="text-sm font-bold text-gray-900">
              {{ cat.label }}
            </h3>
            <span class="text-xs text-gray-400">{{ cat.sublabel }}</span>
          </div>
          <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="[cat.iconBg, cat.iconColor]">
            {{ completedCount(key) }}/{{ grouped[key].length }}
          </span>
        </div>

        <!-- Timeline items -->
        <div class="space-y-3 border-l-2 pl-5" :class="cat.color">
          <ActionItemCard
            v-for="item in grouped[key]"
            :key="item.id"
            :item="item"
            :unit-impact="unitImpact"
            @toggle-status="(id, status) => emit('toggleStatus', id, status)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
