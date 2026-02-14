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
    <div class="relative overflow-hidden rounded-2xl border border-gray-200 bg-linear-to-br from-white via-emerald-50/30 to-teal-50/40 p-6 shadow-sm">
      <div class="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-emerald-100/30 blur-2xl" />
      <div class="relative">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100">
            <svg class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
            </svg>
          </div>
          <p class="text-xs font-medium text-gray-500">Empreinte totale</p>
        </div>
        <div class="mt-3 flex items-baseline gap-1.5">
          <span class="text-3xl font-bold text-gray-900">{{ (totalKg / 1000).toFixed(1) }}</span>
          <span class="text-sm font-medium text-gray-400">tCO₂eq / {{ periode }}</span>
        </div>
      </div>
    </div>

    <!-- Variation -->
    <div class="flex items-center gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
        :class="variation !== null && variation < 0 ? 'bg-emerald-100' : variation !== null && variation > 0 ? 'bg-red-100' : 'bg-gray-100'"
      >
        <svg
          v-if="variation !== null && variation < 0"
          class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6L9 12.75l4.286-4.286a11.948 11.948 0 014.306 6.43l.776 2.898m0 0l3.182-5.511m-3.182 5.51l-5.511-3.181" />
        </svg>
        <svg
          v-else-if="variation !== null && variation > 0"
          class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
        </svg>
        <svg v-else class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15" />
        </svg>
      </div>
      <div>
        <p class="text-xs font-medium text-gray-500">Variation vs N-1</p>
        <div class="mt-1 flex items-baseline gap-1.5">
          <span
            class="text-2xl font-bold"
            :class="variation !== null && variation < 0 ? 'text-emerald-600' : variation !== null && variation > 0 ? 'text-red-500' : 'text-gray-400'"
          >
            <template v-if="variation !== null">{{ variation > 0 ? '+' : '' }}{{ variation.toFixed(1) }}%</template>
            <template v-else>&mdash;</template>
          </span>
        </div>
      </div>
    </div>

    <!-- Par employé -->
    <div class="flex items-center gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100">
        <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
      </div>
      <div>
        <p class="text-xs font-medium text-gray-500">Par employe</p>
        <div class="mt-1 flex items-baseline gap-1.5">
          <span class="text-2xl font-bold text-gray-900">
            {{ totalKg > 0 ? (totalKg / 1000).toFixed(1) : '—' }}
          </span>
          <span class="text-sm font-medium text-gray-400">tCO₂eq</span>
        </div>
      </div>
    </div>
  </div>
</template>
