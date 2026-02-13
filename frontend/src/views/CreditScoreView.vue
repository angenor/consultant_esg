<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import CreditScoreGauge from '../components/credit/CreditScoreGauge.vue'
import ScoreBreakdown from '../components/credit/ScoreBreakdown.vue'
import ShareScoreButton from '../components/credit/ShareScoreButton.vue'
import type { ScoreFactor } from '../components/credit/ScoreBreakdown.vue'

const router = useRouter()
const { get } = useApi()

const loading = ref(true)
const hasData = ref(false)

const scoreCombine = ref(0)
const scoreSolvabilite = ref(0)
const scoreImpactVert = ref(0)
const facteursPositifs = ref<ScoreFactor[]>([])
const facteursNegatifs = ref<ScoreFactor[]>([])
const recommandations = ref<string[]>([])
const entrepriseId = ref('')

async function loadData() {
  loading.value = true
  try {
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

    const facteurs = data.facteurs_json || {}
    facteursPositifs.value = (facteurs.facteurs_positifs || []).map((f: any) => ({
      label: f.facteur || f.label,
      impact: f.impact ?? 0,
    }))
    facteursNegatifs.value = (facteurs.facteurs_negatifs || []).map((f: any) => ({
      label: f.facteur || f.label,
      impact: f.impact ?? 0,
    }))
    recommandations.value = facteurs.recommandations || data.recommandations || []
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
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-800">Pas encore de score crédit vert</h2>
      <p class="mt-2 text-sm text-gray-500">
        Rendez-vous dans le chat pour calculer votre score de crédit vert.
        L'assistant collectera vos données financières et ESG.
      </p>
      <button
        class="mt-6 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700"
        @click="router.push('/chat')"
      >
        Calculer mon score
      </button>
    </div>

    <!-- Data -->
    <template v-else>
      <!-- Gauge -->
      <div class="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <h3 class="mb-6 text-center text-sm font-semibold uppercase tracking-wide text-gray-500">
          Score Crédit Vert Combiné
        </h3>
        <CreditScoreGauge :score="scoreCombine" />
      </div>

      <!-- Breakdown -->
      <ScoreBreakdown
        :solvabilite="scoreSolvabilite"
        :impact-vert="scoreImpactVert"
        :facteurs-positifs="facteursPositifs"
        :facteurs-negatifs="facteursNegatifs"
      />

      <!-- Recommendations -->
      <div v-if="recommandations.length > 0" class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
          Recommandations
        </h3>
        <ul class="space-y-2">
          <li v-for="(r, i) in recommandations" :key="i" class="flex items-start gap-2 text-sm text-gray-700">
            <span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
              {{ i + 1 }}
            </span>
            {{ r }}
          </li>
        </ul>
      </div>

      <!-- Share -->
      <ShareScoreButton v-if="entrepriseId" :entreprise-id="entrepriseId" />
    </template>
  </div>
</template>
