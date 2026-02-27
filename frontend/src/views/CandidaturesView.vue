<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useCandidaturesStore } from '../stores/candidatures'
import CandidatureCard from '../components/candidatures/CandidatureCard.vue'
import StatusBadge from '../components/candidatures/StatusBadge.vue'

const store = useCandidaturesStore()

const filterStatus = ref('')
const searchQuery = ref('')

const STATUTS = [
  { value: '', label: 'Tous les statuts' },
  { value: 'brouillon', label: 'Brouillon' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'soumise', label: 'Soumise' },
  { value: 'acceptee', label: 'Acceptée' },
  { value: 'refusee', label: 'Refusée' },
  { value: 'abandonnee', label: 'Abandonnée' },
]

const filteredCandidatures = ref(store.candidatures)

function applyFilters() {
  let result = store.candidatures
  if (filterStatus.value) {
    result = result.filter((c) => c.status === filterStatus.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      (c) =>
        c.fonds_nom.toLowerCase().includes(q) || c.fonds_institution.toLowerCase().includes(q),
    )
  }
  filteredCandidatures.value = result
}

watch([filterStatus, searchQuery, () => store.candidatures], applyFilters)

onMounted(async () => {
  await Promise.all([store.loadCandidatures(), store.loadStats()])
  applyFilters()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Mes Candidatures</h1>
        <p v-if="store.stats" class="text-sm text-gray-500 mt-1">
          {{ store.stats.total }} candidature{{ store.stats.total > 1 ? 's' : '' }} au total
        </p>
      </div>
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouvelle candidature
      </router-link>
    </div>

    <!-- Stats cards -->
    <div v-if="store.stats && store.stats.total > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-white border rounded-xl p-3 text-center">
        <p class="text-2xl font-bold text-blue-600">{{ store.stats.en_cours + store.stats.brouillon }}</p>
        <p class="text-xs text-gray-500">En cours</p>
      </div>
      <div class="bg-white border rounded-xl p-3 text-center">
        <p class="text-2xl font-bold text-amber-600">{{ store.stats.soumise }}</p>
        <p class="text-xs text-gray-500">Soumises</p>
      </div>
      <div class="bg-white border rounded-xl p-3 text-center">
        <p class="text-2xl font-bold text-emerald-600">{{ store.stats.acceptee }}</p>
        <p class="text-xs text-gray-500">Acceptées</p>
      </div>
      <div class="bg-white border rounded-xl p-3 text-center">
        <p class="text-2xl font-bold text-gray-400">{{ store.stats.total }}</p>
        <p class="text-xs text-gray-500">Total</p>
      </div>
    </div>

    <!-- Filtres -->
    <div class="flex flex-col sm:flex-row gap-3">
      <select
        v-model="filterStatus"
        class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:ring-emerald-500"
      >
        <option v-for="s in STATUTS" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
      <div class="relative flex-1">
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher par nom de fonds..."
          class="w-full rounded-lg border border-gray-300 pl-10 pr-3 py-2 text-sm focus:border-emerald-500 focus:ring-emerald-500"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="flex justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredCandidatures.length === 0" class="text-center py-16">
      <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 class="mt-3 text-sm font-medium text-gray-900">
        {{ filterStatus || searchQuery ? 'Aucun résultat' : 'Aucune candidature' }}
      </h3>
      <p class="mt-1 text-sm text-gray-500">
        {{
          filterStatus || searchQuery
            ? 'Essayez de modifier vos filtres.'
            : 'Commencez par discuter avec le conseiller IA pour identifier les fonds adaptés.'
        }}
      </p>
      <router-link
        v-if="!filterStatus && !searchQuery"
        to="/chat"
        class="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:text-emerald-700"
      >
        Demander au conseiller IA
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>

    <!-- Liste des candidatures -->
    <div v-else class="grid gap-4">
      <CandidatureCard v-for="c in filteredCandidatures" :key="c.id" :candidature="c" />
    </div>
  </div>
</template>
