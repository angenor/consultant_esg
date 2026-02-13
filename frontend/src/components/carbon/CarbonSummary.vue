<script setup lang="ts">
defineProps<{
  totalKg: number
  variation: number | null
  periode: string
}>()
</script>

<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
    <!-- Empreinte totale -->
    <div class="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm">
      <p class="text-xs font-medium uppercase tracking-wide text-gray-500">Empreinte totale</p>
      <p class="mt-2 text-3xl font-bold text-gray-900">
        {{ (totalKg / 1000).toFixed(1) }}
      </p>
      <p class="text-sm text-gray-500">tCO₂eq / {{ periode }}</p>
    </div>

    <!-- Variation -->
    <div class="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm">
      <p class="text-xs font-medium uppercase tracking-wide text-gray-500">Variation vs N-1</p>
      <p
        class="mt-2 text-3xl font-bold"
        :class="variation !== null && variation < 0 ? 'text-emerald-600' : variation !== null && variation > 0 ? 'text-red-500' : 'text-gray-400'"
      >
        <template v-if="variation !== null">
          {{ variation > 0 ? '+' : '' }}{{ variation.toFixed(1) }}%
        </template>
        <template v-else>—</template>
      </p>
      <p class="text-sm text-gray-500">par rapport à l'année précédente</p>
    </div>

    <!-- Par employé -->
    <div class="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm">
      <p class="text-xs font-medium uppercase tracking-wide text-gray-500">Par employé</p>
      <p class="mt-2 text-3xl font-bold text-gray-900">
        {{ totalKg > 0 ? (totalKg / 1000).toFixed(1) : '—' }}
      </p>
      <p class="text-sm text-gray-500">tCO₂eq / personne</p>
    </div>
  </div>
</template>
