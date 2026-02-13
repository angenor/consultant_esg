<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import ReferentielSelector from '../components/dashboard/ReferentielSelector.vue'
import type { ReferentielOption } from '../components/dashboard/ReferentielSelector.vue'
import ScoreCard from '../components/dashboard/ScoreCard.vue'
import ScoreComparison from '../components/dashboard/ScoreComparison.vue'
import type { ScoreEntry } from '../components/dashboard/ScoreComparison.vue'
import RadarChart from '../components/dashboard/RadarChart.vue'
import ScoreHistory from '../components/dashboard/ScoreHistory.vue'
import type { HistoryPoint } from '../components/dashboard/ScoreHistory.vue'
import FundsMatchList from '../components/dashboard/FundsMatchList.vue'
import type { FundMatch } from '../components/dashboard/FundsMatchList.vue'
import ActionPlanSummary from '../components/dashboard/ActionPlanSummary.vue'
import type { ActionSummary } from '../components/dashboard/ActionPlanSummary.vue'

const router = useRouter()
const { get } = useApi()

const loading = ref(true)
const hasData = ref(false)

// Data
const entrepriseNom = ref('')
const referentiels = ref<ReferentielOption[]>([])
const selectedRef = ref<string | null>(null)
const scoreEntries = ref<ScoreEntry[]>([])
const allScores = ref<any[]>([])
const scoreHistory = ref<HistoryPoint[]>([])
const fondsRecommandes = ref<FundMatch[]>([])
const actionPlan = ref<ActionSummary | null>(null)
const alerts = ref<any[]>([])

// Computed: score filtré par référentiel sélectionné
const currentScore = computed(() => {
  if (!selectedRef.value) {
    // Prendre le premier score disponible
    return allScores.value[0] ?? null
  }
  return allScores.value.find((s: any) => s.referentiel_code === selectedRef.value) ?? null
})

const currentScoreE = computed(() => currentScore.value?.score_e ?? null)
const currentScoreS = computed(() => currentScore.value?.score_s ?? null)
const currentScoreG = computed(() => currentScore.value?.score_g ?? null)
const currentScoreGlobal = computed(() => currentScore.value?.score_global ?? null)
const currentRefLabel = computed(() => {
  if (!currentScore.value) return ''
  return currentScore.value.referentiel_nom ?? ''
})

// Alertes filtrées
const filteredAlerts = computed(() => {
  if (!selectedRef.value) return alerts.value
  return alerts.value.filter((a: any) => a.referentiel_code === selectedRef.value)
})

async function loadData() {
  loading.value = true
  try {
    const data = await get<any>('/api/dashboard/data')
    if (!data) {
      hasData.value = false
      return
    }

    hasData.value = true
    entrepriseNom.value = data.entreprise?.nom ?? ''
    referentiels.value = data.referentiels ?? []
    allScores.value = data.scores_par_referentiel ?? []
    scoreEntries.value = (data.scores_par_referentiel ?? []).map((s: any) => ({
      referentiel_nom: s.referentiel_nom,
      referentiel_code: s.referentiel_code,
      score_global: s.score_global,
      niveau: s.niveau,
    }))
    scoreHistory.value = data.score_history ?? []
    fondsRecommandes.value = data.fonds_recommandes ?? []
    actionPlan.value = data.action_plan ?? null
    alerts.value = data.alerts ?? []

    // Auto-sélectionner le premier référentiel si des scores existent
    if (allScores.value.length > 0 && !selectedRef.value) {
      selectedRef.value = allScores.value[0].referentiel_code
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
    <div v-else-if="!hasData || allScores.length === 0" class="mx-auto max-w-md py-16 text-center">
      <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
        <svg class="h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-800">Pas encore de scores ESG</h2>
      <p class="mt-2 text-sm text-gray-500">
        Commencez par discuter avec l'assistant dans le chat pour calculer vos premiers scores ESG multi-référentiel.
      </p>
      <button
        class="mt-6 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700"
        @click="router.push('/chat')"
      >
        Calculer mes scores ESG
      </button>
    </div>

    <!-- Dashboard -->
    <template v-else>
      <!-- Header -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Tableau de Bord</h1>
          <p class="mt-0.5 text-sm text-gray-500">{{ entrepriseNom }}</p>
        </div>
        <ReferentielSelector
          v-model="selectedRef"
          :referentiels="referentiels"
        />
      </div>

      <!-- Score Cards E/S/G + Global -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <ScoreCard label="Environnement" :score="currentScoreE" color="emerald" />
        <ScoreCard label="Social" :score="currentScoreS" color="blue" />
        <ScoreCard label="Gouvernance" :score="currentScoreG" color="purple" />
        <ScoreCard
          label="Score Global"
          :score="currentScoreGlobal"
          color="amber"
          size="lg"
        />
      </div>

      <!-- Alerts -->
      <div v-if="filteredAlerts.length > 0" class="space-y-2">
        <div
          v-for="(alert, idx) in filteredAlerts"
          :key="idx"
          class="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3"
        >
          <svg class="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          <p class="text-sm text-amber-800">
            <strong>{{ alert.referentiel }}</strong> : critère "{{ alert.critere }}" non atteint
            ({{ alert.score }}/100, minimum requis : {{ alert.minimum }})
          </p>
        </div>
      </div>

      <!-- Comparison + Radar -->
      <div class="grid gap-6 lg:grid-cols-2">
        <ScoreComparison :scores="scoreEntries" :selected-code="selectedRef" />
        <RadarChart
          :score-e="currentScoreE"
          :score-s="currentScoreS"
          :score-g="currentScoreG"
          :label="currentRefLabel"
        />
      </div>

      <!-- History -->
      <ScoreHistory :history="scoreHistory" :selected-code="selectedRef" />

      <!-- Fonds + Action Plan -->
      <div class="grid gap-6 lg:grid-cols-2">
        <FundsMatchList :fonds="fondsRecommandes" />
        <ActionPlanSummary :plan="actionPlan" />
      </div>
    </template>
  </div>
</template>
