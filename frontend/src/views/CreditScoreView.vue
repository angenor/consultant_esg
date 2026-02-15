<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import { useReferentielStore } from '../stores/referentiel'
import ReferentielSelector from '../components/dashboard/ReferentielSelector.vue'
import CreditScoreGauge from '../components/credit/CreditScoreGauge.vue'
import ScoreBreakdown from '../components/credit/ScoreBreakdown.vue'
import ShareScoreButton from '../components/credit/ShareScoreButton.vue'
import type { ScoreFactor } from '../components/credit/ScoreBreakdown.vue'

const router = useRouter()
const { get, post } = useApi()
const refStore = useReferentielStore()

const loading = ref(true)
const hasData = ref(false)
const recalculating = ref(false)

const scoreCombine = ref(0)
const scoreSolvabilite = ref(0)
const scoreImpactVert = ref(0)
const facteursPositifs = ref<ScoreFactor[]>([])
const facteursNegatifs = ref<ScoreFactor[]>([])
const recommandations = ref<string[]>([])
const entrepriseId = ref('')

function applyFacteurs(facteurs: any, recs?: string[]) {
  facteursPositifs.value = (facteurs.facteurs_positifs || []).map((f: any) => ({
    label: f.facteur || f.label,
    impact: f.impact ?? 0,
  }))
  facteursNegatifs.value = (facteurs.facteurs_negatifs || []).map((f: any) => ({
    label: f.facteur || f.label,
    impact: f.impact ?? 0,
  }))
  recommandations.value = recs || facteurs.recommandations || []
}

async function ensureReferentiels() {
  if (refStore.referentiels.length > 0) return
  try {
    const data = await get<any>('/api/dashboard/data')
    if (data?.referentiels) {
      refStore.setReferentiels(data.referentiels)
    }
  } catch {
    // silent
  }
}

async function loadData() {
  loading.value = true
  try {
    await ensureReferentiels()
    const data = await get<any>('/api/credit-score/latest')
    if (!data || data.error) {
      hasData.value = false
      return
    }

    hasData.value = true
    scoreCombine.value = Math.round(data.score_combine || 0)
    scoreSolvabilite.value = Math.round(data.score_solvabilite || 0)
    scoreImpactVert.value = Math.round(data.score_impact_vert || 0)
    entrepriseId.value = data.entreprise_id || ''
    applyFacteurs(data.facteurs_json || {}, data.recommandations)
  } catch {
    hasData.value = false
  } finally {
    loading.value = false
  }
}

async function recalculate() {
  recalculating.value = true
  try {
    const code = refStore.selectedCode
    let url = '/api/credit-score/recalculate'
    if (code) {
      url += `?referentiel_code=${encodeURIComponent(code)}`
    }
    const data = await post<any>(url, {})
    if (!data || data.error) return

    scoreCombine.value = Math.round(data.score_combine || 0)
    scoreSolvabilite.value = Math.round(data.score_solvabilite || 0)
    scoreImpactVert.value = Math.round(data.score_impact_vert || 0)
    applyFacteurs(data.facteurs || {}, data.recommandations)
  } catch {
    // silent
  } finally {
    recalculating.value = false
  }
}

function onSelectRef(code: string | null) {
  refStore.select(code)
}

watch(() => refStore.selectedCode, () => {
  if (hasData.value) {
    recalculate()
  }
})

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
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Pas encore de score crédit vert</h2>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-gray-500">
        Rendez-vous dans le chat pour calculer votre score de crédit vert.
        L'assistant collectera vos données financières et ESG pour évaluer votre profil.
      </p>
      <button
        class="mt-8 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-200"
        @click="router.push('/chat')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
        </svg>
        Calculer mon score
      </button>
    </div>

    <!-- Data -->
    <template v-else>
      <!-- Page Header -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Score Crédit Vert</h1>
          <p class="mt-1 text-sm text-gray-500">Votre évaluation combinée solvabilité + impact ESG</p>
        </div>
        <div class="flex items-center gap-3">
          <ReferentielSelector
            :model-value="refStore.selectedCode"
            :referentiels="refStore.referentiels"
            @update:model-value="onSelectRef"
          />
          <button
            class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-600 shadow-sm transition-colors hover:bg-gray-50"
            :disabled="recalculating"
            @click="recalculate"
          >
            <svg class="h-4 w-4" :class="{ 'animate-spin': recalculating }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
            </svg>
            Actualiser
          </button>
        </div>
      </div>

      <!-- Hero Gauge -->
      <div class="relative overflow-hidden rounded-2xl border border-gray-200 bg-linear-to-br from-white via-emerald-50/30 to-teal-50/40 p-8 shadow-sm">
        <div class="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-emerald-100/30 blur-3xl" />
        <div class="absolute -bottom-12 -left-12 h-36 w-36 rounded-full bg-teal-100/20 blur-2xl" />
        <div class="relative">
          <h3 class="mb-6 text-center text-xs font-semibold uppercase tracking-widest text-gray-400">
            Score Combiné
          </h3>
          <CreditScoreGauge :score="scoreCombine" />
        </div>
      </div>

      <!-- Sub-score stat cards -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50">
            <svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-gray-500">Solvabilité financière</p>
            <div class="mt-1 flex items-baseline gap-1.5">
              <span class="text-2xl font-bold text-gray-900">{{ scoreSolvabilite }}</span>
              <span class="text-sm text-gray-400">/ 100</span>
            </div>
          </div>
          <div class="h-10 w-10 shrink-0">
            <svg viewBox="0 0 36 36" class="h-full w-full -rotate-90">
              <circle cx="18" cy="18" r="14" fill="none" stroke="#e2e8f0" stroke-width="4" />
              <circle
                cx="18" cy="18" r="14" fill="none"
                :stroke="scoreSolvabilite >= 60 ? '#3b82f6' : scoreSolvabilite >= 40 ? '#f59e0b' : '#ef4444'"
                stroke-width="4" stroke-linecap="round"
                :stroke-dasharray="87.96"
                :stroke-dashoffset="87.96 * (1 - scoreSolvabilite / 100)"
                style="transition: stroke-dashoffset 0.8s ease-out"
              />
            </svg>
          </div>
        </div>

        <div class="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
            <svg class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-gray-500">Impact vert (ESG)</p>
            <div class="mt-1 flex items-baseline gap-1.5">
              <span class="text-2xl font-bold text-gray-900">{{ scoreImpactVert }}</span>
              <span class="text-sm text-gray-400">/ 100</span>
            </div>
          </div>
          <div class="h-10 w-10 shrink-0">
            <svg viewBox="0 0 36 36" class="h-full w-full -rotate-90">
              <circle cx="18" cy="18" r="14" fill="none" stroke="#e2e8f0" stroke-width="4" />
              <circle
                cx="18" cy="18" r="14" fill="none"
                :stroke="scoreImpactVert >= 60 ? '#059669' : scoreImpactVert >= 40 ? '#f59e0b' : '#ef4444'"
                stroke-width="4" stroke-linecap="round"
                :stroke-dasharray="87.96"
                :stroke-dashoffset="87.96 * (1 - scoreImpactVert / 100)"
                style="transition: stroke-dashoffset 0.8s ease-out"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- Breakdown -->
      <ScoreBreakdown
        :solvabilite="scoreSolvabilite"
        :impact-vert="scoreImpactVert"
        :facteurs-positifs="facteursPositifs"
        :facteurs-negatifs="facteursNegatifs"
      />

      <!-- Recommendations -->
      <div v-if="recommandations.length > 0" class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div class="mb-5 flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50">
            <svg class="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-gray-900">Recommandations</h3>
            <p class="text-xs text-gray-500">Actions suggérées pour améliorer votre score</p>
          </div>
        </div>
        <div class="space-y-3">
          <div
            v-for="(r, i) in recommandations" :key="i"
            class="flex items-start gap-3 rounded-xl bg-gray-50 p-4 transition-colors hover:bg-emerald-50/50"
          >
            <span class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">
              {{ i + 1 }}
            </span>
            <p class="text-sm leading-relaxed text-gray-700">{{ r }}</p>
          </div>
        </div>
      </div>

      <!-- Share -->
      <ShareScoreButton v-if="entrepriseId" :entreprise-id="entrepriseId" />
    </template>
  </div>
</template>
