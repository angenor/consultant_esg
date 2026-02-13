<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'
import ProgressTracker from '../components/actions/ProgressTracker.vue'
import ActionPlanTimeline from '../components/actions/ActionPlanTimeline.vue'
import type { ActionItemData } from '../components/actions/ActionItemCard.vue'

const router = useRouter()
const { get, put } = useApi()

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
const pourcentage = computed(() => (nbTotal.value > 0 ? Math.round((nbFait.value / nbTotal.value) * 100) : 0))

const coutTotal = computed(() => {
  return items.value.reduce((sum, i) => sum + ((i as any).cout_estime || 0), 0)
})

const impactTotal = computed(() => {
  return items.value.reduce((sum, i) => sum + (i.impact_score_estime || 0), 0)
})

async function loadData() {
  loading.value = true
  try {
    const data = await get<any>('/api/action-plans/latest')
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
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-800">Pas encore de plan d'action</h2>
      <p class="mt-2 text-sm text-gray-500">
        Rendez-vous dans le chat pour créer votre plan d'action ESG.
        L'assistant analysera vos scores et proposera des actions priorisées.
      </p>
      <button
        class="mt-6 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700"
        @click="router.push('/chat')"
      >
        Créer mon plan d'action
      </button>
    </div>

    <!-- Data -->
    <template v-else>
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
        <div class="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
          <p class="text-xs font-medium uppercase text-gray-500">Total actions</p>
          <p class="mt-1 text-xl font-bold text-gray-900">{{ nbTotal }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
          <p class="text-xs font-medium uppercase text-gray-500">Complétées</p>
          <p class="mt-1 text-xl font-bold text-emerald-600">{{ nbFait }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
          <p class="text-xs font-medium uppercase text-gray-500">Impact estimé</p>
          <p class="mt-1 text-xl font-bold text-teal-600">+{{ impactTotal }} pts</p>
        </div>
        <div v-if="coutTotal > 0" class="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
          <p class="text-xs font-medium uppercase text-gray-500">Coût estimé</p>
          <p class="mt-1 text-xl font-bold text-gray-700">{{ (coutTotal / 1_000_000).toFixed(1) }}M</p>
        </div>
      </div>

      <!-- Timeline -->
      <ActionPlanTimeline :items="items" @toggle-status="handleToggleStatus" />
    </template>
  </div>
</template>
