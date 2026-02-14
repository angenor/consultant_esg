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
    <div v-else-if="!hasData || allScores.length === 0" class="mx-auto max-w-lg py-20 text-center">
      <div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-linear-to-br from-emerald-50 to-teal-50">
        <svg class="h-10 w-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Pas encore de scores ESG</h2>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-gray-500">
        Commencez par discuter avec l'assistant dans le chat pour calculer vos premiers scores ESG multi-référentiel.
      </p>
      <button
        class="mt-8 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-200"
        @click="router.push('/chat')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
        </svg>
        Calculer mes scores ESG
      </button>
    </div>

    <!-- Dashboard -->
    <template v-else>
      <!-- Header -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Tableau de Bord</h1>
          <p class="mt-1 text-sm text-gray-500">{{ entrepriseNom }}</p>
        </div>
        <div class="flex items-center gap-3">
          <ReferentielSelector
            v-model="selectedRef"
            :referentiels="referentiels"
          />
          <button
            class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-600 shadow-sm transition-colors hover:bg-gray-50"
            @click="loadData"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Alerts -->
      <div v-if="filteredAlerts.length > 0" class="space-y-2">
        <div
          v-for="(alert, idx) in filteredAlerts"
          :key="idx"
          class="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
        >
          <div class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-amber-100">
            <svg class="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <p class="text-sm text-amber-800">
            <strong>{{ alert.referentiel }}</strong> : critère "{{ alert.critere }}" non atteint
            ({{ alert.score }}/100, minimum requis : {{ alert.minimum }})
          </p>
        </div>
      </div>

      <!-- Score Cards E/S/G + Global -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <ScoreCard label="Environnement" :score="currentScoreE" color="emerald" icon="leaf" />
        <ScoreCard label="Social" :score="currentScoreS" color="blue" icon="users" />
        <ScoreCard label="Gouvernance" :score="currentScoreG" color="purple" icon="building" />
        <ScoreCard
          label="Score Global"
          :score="currentScoreGlobal"
          color="amber"
          size="lg"
          icon="star"
        />
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
