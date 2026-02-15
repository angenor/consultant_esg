<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import { useReferentielStore } from '../stores/referentiel'
import ReferentielSelector from '../components/dashboard/ReferentielSelector.vue'
import ProgressTracker from '../components/actions/ProgressTracker.vue'
import ActionPlanTimeline from '../components/actions/ActionPlanTimeline.vue'
import type { ActionItemData } from '../components/actions/ActionItemCard.vue'

const router = useRouter()
const { get, put } = useApi()
const refStore = useReferentielStore()

const loading = ref(true)
const hasData = ref(false)
const updating = ref<string | null>(null)

// Plan data
const planTitre = ref('')
const planId = ref('')
const scoreInitial = ref<number | null>(null)
const scoreCible = ref<number | null>(null)
const items = ref<ActionItemData[]>([])

const nbTotal = computed(() => items.value.length)
const nbFait = computed(() => items.value.filter((i) => i.statut === 'fait').length)
const nbEnCours = computed(() => items.value.filter((i) => i.statut === 'en_cours').length)
const pourcentage = computed(() => (nbTotal.value > 0 ? Math.round((nbFait.value / nbTotal.value) * 100) : 0))

const impactTotal = computed(() => {
  return Math.round(items.value.reduce((sum, i) => sum + (i.impact_score_estime || 0), 0))
})

async function ensureReferentiels() {
  if (refStore.referentiels.length > 0) return
  try {
    const data = await get<any>('/api/dashboard/data')
    if (data?.referentiels) {
      refStore.setReferentiels(data.referentiels)
    }
  } catch {
    // silent — referentiels selector will just be empty
  }
}

async function loadData() {
  loading.value = true
  try {
    await ensureReferentiels()
    const code = refStore.selectedCode
    let url = '/api/action-plans/latest?type_plan=esg'
    if (code) {
      url += `&referentiel_code=${encodeURIComponent(code)}`
    }
    const data = await get<any>(url)
    if (!data || data.error) {
      hasData.value = false
      return
    }

    hasData.value = true
    planTitre.value = data.titre || 'Plan d\'action ESG'
    planId.value = data.id || ''
    scoreInitial.value = data.score_initial ?? null
    scoreCible.value = data.score_cible ?? null

    items.value = (data.items || []).map((item: any) => ({
      id: item.id,
      titre: item.titre,
      description: item.description,
      priorite: item.priorite || 'moyen_terme',
      pilier: item.pilier,
      statut: item.statut || 'a_faire',
      echeance: item.echeance,
      impact_score_estime: item.impact_score_estime,
      cout_estime: item.cout_estime,
    }))
  } catch {
    hasData.value = false
  } finally {
    loading.value = false
  }
}

async function handleToggleStatus(itemId: string, newStatus: string) {
  updating.value = itemId
  try {
    await put(`/api/action-plans/items/${itemId}`, { statut: newStatus })
    const item = items.value.find((i) => i.id === itemId)
    if (item) {
      item.statut = newStatus
    }
  } catch {
    // silent
  } finally {
    updating.value = null
  }
}

function onSelectRef(code: string | null) {
  refStore.select(code)
}

// Recharger quand le référentiel change
watch(() => refStore.selectedCode, () => {
  loadData()
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
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Pas encore de plan d'action</h2>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-gray-500">
        Rendez-vous dans le chat pour créer votre plan d'action ESG.
        L'assistant analysera vos scores et proposera des actions priorisées.
      </p>
      <button
        class="mt-8 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 hover:shadow-lg hover:shadow-emerald-200"
        @click="router.push('/chat')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Créer mon plan d'action
      </button>
    </div>

    <!-- Data -->
    <template v-else>
      <!-- Page Header -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Plan d'Action ESG</h1>
          <p class="mt-1 text-sm text-gray-500">{{ planTitre }}</p>
        </div>
        <div class="flex items-center gap-3">
          <ReferentielSelector
            :model-value="refStore.selectedCode"
            :referentiels="refStore.referentiels"
            @update:model-value="onSelectRef"
          />
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
      </div>

      <!-- Progress -->
      <ProgressTracker
        :titre="planTitre"
        :pourcentage="pourcentage"
        :nb-total="nbTotal"
        :nb-fait="nbFait"
        :score-initial="scoreInitial"
        :score-cible="scoreCible"
      />

      <!-- Stats summary -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100">
            <svg class="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500">Total</p>
            <p class="text-xl font-bold text-gray-900">{{ nbTotal }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50">
            <svg class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500">Complétées</p>
            <p class="text-xl font-bold text-emerald-600">{{ nbFait }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-50">
            <svg class="h-5 w-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500">Impact estimé</p>
            <p class="text-xl font-bold text-teal-600">+{{ impactTotal }}<span class="text-sm font-medium"> pts</span></p>
          </div>
        </div>

        <div class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
            <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500">En cours</p>
            <p class="text-xl font-bold text-blue-600">{{ nbEnCours }}</p>
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <ActionPlanTimeline :items="items" @toggle-status="handleToggleStatus" />
    </template>
  </div>
</template>
