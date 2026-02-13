<script setup lang="ts">
import { computed } from 'vue'
import type { ActionItemData } from './ActionItemCard.vue'
import ActionItemCard from './ActionItemCard.vue'

const props = defineProps<{
  items: ActionItemData[]
}>()

const emit = defineEmits<{
  toggleStatus: [id: string, newStatus: string]
}>()

const grouped = computed(() => {
  const groups: Record<string, ActionItemData[]> = {
    quick_win: [],
    moyen_terme: [],
    long_terme: [],
  }
  for (const item of props.items) {
    const cat = item.priorite || 'moyen_terme'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return groups
})

const categoryMeta: Record<string, { label: string; sublabel: string; color: string }> = {
  quick_win: { label: 'Quick-wins', sublabel: '< 3 mois', color: 'border-emerald-400' },
  moyen_terme: { label: 'Moyen terme', sublabel: '3-12 mois', color: 'border-blue-400' },
  long_terme: { label: 'Long terme', sublabel: '> 12 mois', color: 'border-amber-400' },
}
</script>

<template>
  <div class="space-y-8">
    <div v-for="(cat, key) in categoryMeta" :key="key">
      <div v-if="grouped[key] && grouped[key].length > 0" class="relative">
        <!-- Category header -->
        <div class="mb-3 flex items-center gap-3">
          <div class="h-0.5 w-6 rounded" :class="cat.color.replace('border-', 'bg-')" />
          <h3 class="text-sm font-semibold text-gray-700">
            {{ cat.label }}
            <span class="ml-1 text-xs font-normal text-gray-400">{{ cat.sublabel }}</span>
          </h3>
          <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
            {{ grouped[key].length }}
          </span>
        </div>

        <!-- Timeline items -->
        <div class="space-y-3 border-l-2 pl-4" :class="cat.color">
          <ActionItemCard
            v-for="item in grouped[key]"
            :key="item.id"
            :item="item"
            @toggle-status="(id, status) => emit('toggleStatus', id, status)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
