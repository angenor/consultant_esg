<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import CarbonSummary from '../components/carbon/CarbonSummary.vue'
import CarbonBySource from '../components/carbon/CarbonBySource.vue'
import CarbonEvolution from '../components/carbon/CarbonEvolution.vue'
import SectorComparison from '../components/carbon/SectorComparison.vue'
import ReductionPlan from '../components/carbon/ReductionPlan.vue'
import type { ReductionAction } from '../components/carbon/ReductionPlan.vue'

const router = useRouter()
const { get } = useApi()

const loading = ref(true)
const hasData = ref(false)

// Carbon data
const totalKg = ref(0)
const variation = ref<number | null>(null)
const periode = ref('an')
const sources = ref<Record<string, number>>({})
const evolutionDates = ref<string[]>([])
const evolutionValues = ref<number[]>([])
const benchmarkSecteur = ref('')
const benchmarkMoyenne = ref(0)
const reductionActions = ref<ReductionAction[]>([])

async function loadData() {
  loading.value = true
  try {
    const data = await get<any>('/api/carbon/latest')
    if (!data || data.error) {
      hasData.value = false
      return
    }

    hasData.value = true
    totalKg.value = (data.total_tco2e || 0) * 1000
    const details = data.details_json || {}
    variation.value = details.variation ?? null
    periode.value = details.periode || 'an'

    // Sources for pie chart
    const s: Record<string, number> = {}
    if (data.energie > 0) s['Énergie'] = data.energie
    if (data.transport > 0) s['Transport'] = data.transport
    if (data.dechets > 0) s['Déchets'] = data.dechets
    if (data.achats > 0) s['Achats'] = data.achats
    sources.value = s

    // Evolution
    if (details.evolution) {
      evolutionDates.value = details.evolution.map((e: any) => e.date || e.mois)
      evolutionValues.value = details.evolution.map((e: any) => e.total || e.valeur)
    }

    // Benchmark
    if (details.benchmark) {
      benchmarkSecteur.value = details.benchmark.secteur || ''
      benchmarkMoyenne.value = (details.benchmark.moyenne_tco2e || 0) * 1000
    }

    // Reduction plan
    if (details.plan_reduction) {
      reductionActions.value = details.plan_reduction
    }
  } catch {
    hasData.value = false
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
    </div>

    <!-- No data -->
    <div v-else-if="!hasData" class="mx-auto max-w-lg py-20 text-center">
      <div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-linear-to-br from-emerald-50 to-teal-50">
        <svg class="h-10 w-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Pas encore de bilan carbone</h2>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-gray-500">
        Rendez-vous dans le chat pour calculer votre empreinte carbone.
        L'assistant vous guidera dans la collecte des données.
      </p>
      <button
        class="mt-8 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-200"
        @click="router.push('/chat')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
        </svg>
        Calculer mon empreinte
      </button>
    </div>

    <!-- Data -->
    <template v-else>
      <!-- Page Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Bilan Carbone</h1>
          <p class="mt-1 text-sm text-gray-500">Empreinte carbone et plan de réduction</p>
        </div>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-600 shadow-sm transition-colors hover:bg-gray-50"
          @click="loadData"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
          </svg>
          Actualiser
        </button>
      </div>

      <!-- Summary cards -->
      <CarbonSummary :total-kg="totalKg" :variation="variation" :periode="periode" />

      <!-- Charts grid -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CarbonBySource v-if="Object.keys(sources).length > 0" :sources="sources" />
        <SectorComparison
          v-if="benchmarkMoyenne > 0"
          :entreprise-kg="totalKg"
          :moyenne-secteur-kg="benchmarkMoyenne"
          :secteur="benchmarkSecteur"
        />
      </div>

      <!-- Evolution -->
      <CarbonEvolution
        v-if="evolutionDates.length > 0"
        :dates="evolutionDates"
        :values="evolutionValues"
      />

      <!-- Reduction plan -->
      <ReductionPlan :actions="reductionActions" />
    </template>
  </div>
</template>
