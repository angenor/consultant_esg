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
    <div v-else-if="!hasData" class="mx-auto max-w-md py-16 text-center">
      <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
        <svg class="h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-800">Pas encore de bilan carbone</h2>
      <p class="mt-2 text-sm text-gray-500">
        Rendez-vous dans le chat pour calculer votre empreinte carbone.
        L'assistant vous guidera dans la collecte des données.
      </p>
      <button
        class="mt-6 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700"
        @click="router.push('/chat')"
      >
        Calculer mon empreinte
      </button>
    </div>

    <!-- Data -->
    <template v-else>
      <CarbonSummary :total-kg="totalKg" :variation="variation" :periode="periode" />

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CarbonBySource v-if="Object.keys(sources).length > 0" :sources="sources" />
        <SectorComparison
          v-if="benchmarkMoyenne > 0"
          :entreprise-kg="totalKg"
          :moyenne-secteur-kg="benchmarkMoyenne"
          :secteur="benchmarkSecteur"
        />
      </div>

      <CarbonEvolution
        v-if="evolutionDates.length > 0"
        :dates="evolutionDates"
        :values="evolutionValues"
      />

      <ReductionPlan :actions="reductionActions" />
    </template>
  </div>
</template>
