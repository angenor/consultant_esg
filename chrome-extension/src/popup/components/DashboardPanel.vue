<template>
  <div class="p-4 space-y-4">
    <!-- Carte Entreprise -->
    <div v-if="data?.entreprise" class="bg-white rounded-xl border border-gray-200 p-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
          <span class="text-emerald-700 font-bold text-sm">
            {{ data.entreprise.nom.substring(0, 2).toUpperCase() }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-800 text-sm truncate">
            {{ data.entreprise.nom }}
          </h3>
          <p class="text-xs text-gray-500">
            {{ data.entreprise.secteur || 'Secteur non defini' }} · {{ data.entreprise.pays }}
          </p>
        </div>
        <div v-if="selectedScore" class="text-right">
          <div class="text-lg font-bold" :class="scoreColor">
            {{ selectedScore.score_global }}/100
          </div>
          <div class="text-xs text-gray-500">{{ t('esg_score') }}</div>
        </div>
      </div>

      <!-- Selecteur de referentiel + sous-scores -->
      <div v-if="availableReferentiels.length > 0" class="mt-3 pt-3 border-t border-gray-100">
        <!-- Selecteur -->
        <div class="flex items-center gap-2 mb-2">
          <label class="text-xs text-gray-500">Referentiel :</label>
          <select
            v-model="selectedReferentiel"
            class="text-xs border border-gray-200 rounded-md px-2 py-1 bg-white
                   outline-none focus:border-emerald-500 flex-1"
          >
            <option
              v-for="ref in availableReferentiels"
              :key="ref.code"
              :value="ref.code"
            >
              {{ ref.label }}
            </option>
          </select>
        </div>

        <!-- Sous-scores E / S / G -->
        <div v-if="selectedScore" class="flex gap-2">
          <div class="flex-1 bg-emerald-50 rounded-lg px-2 py-1.5 text-center">
            <div class="text-xs font-bold text-emerald-700">{{ selectedScore.score_e ?? '-' }}</div>
            <div class="text-[10px] text-emerald-600">Env.</div>
          </div>
          <div class="flex-1 bg-blue-50 rounded-lg px-2 py-1.5 text-center">
            <div class="text-xs font-bold text-blue-700">{{ selectedScore.score_s ?? '-' }}</div>
            <div class="text-[10px] text-blue-600">Social</div>
          </div>
          <div class="flex-1 bg-amber-50 rounded-lg px-2 py-1.5 text-center">
            <div class="text-xs font-bold text-amber-700">{{ selectedScore.score_g ?? '-' }}</div>
            <div class="text-[10px] text-amber-600">Gouv.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pas d'entreprise -->
    <div v-else class="bg-amber-50 rounded-xl border border-amber-200 p-4 text-center">
      <p class="text-sm text-amber-700">{{ t('no_company') }}</p>
      <a href="http://localhost:5173/dashboard" target="_blank"
         class="text-xs text-amber-600 hover:underline mt-1 inline-block">
        {{ t('configure_company') }}
      </a>
    </div>

    <!-- Candidatures en cours -->
    <section>
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-800 text-sm">{{ t('applications_title') }}</h3>
        <span class="text-xs text-gray-400">{{ activeApplications.length }}</span>
      </div>

      <div v-if="activeApplications.length === 0"
           class="bg-white rounded-xl border border-dashed border-gray-300 p-4 text-center">
        <p class="text-sm text-gray-500">{{ t('no_applications') }}</p>
        <p class="text-xs text-gray-400 mt-1">
          {{ t('no_applications_hint') }}
        </p>
      </div>

      <div v-else class="space-y-2">
        <ApplicationCard
          v-for="app in activeApplications"
          :key="app.id"
          :application="app"
          @click="$emit('select-application', app)"
        />
      </div>
    </section>

    <!-- Fonds recommandes -->
    <section v-if="data?.fonds_recommandes?.length">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-800 text-sm">{{ t('funds_recommended') }}</h3>
        <select
          v-model="sortMode"
          class="text-[10px] border border-gray-200 rounded-md px-1.5 py-0.5 bg-white
                 outline-none focus:border-emerald-500 text-gray-600"
        >
          <option value="compatibility">Compatibilité</option>
          <option value="montant">Montant</option>
          <option value="date_limite">Date limite</option>
        </select>
      </div>
      <div class="space-y-2">
        <FundRecommendation
          v-for="fonds in sortedRecommendations"
          :key="fonds.id"
          :fonds="fonds"
          :existing-application="getExistingApplication(fonds.id)"
          @start-application="handleStartApplication"
          @resume-application="$emit('select-application', $event)"
        />
      </div>
    </section>

    <!-- Modal confirmation candidature -->
    <div v-if="pendingFonds" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-4 m-4 max-w-sm w-full">
        <h3 class="font-semibold text-gray-800">Commencer la candidature ?</h3>
        <p class="text-sm text-gray-500 mt-1">
          {{ pendingFonds.nom }} — {{ pendingFonds.institution || '' }}
        </p>
        <!-- Avertissement mode d'acces intermediaire -->
        <div v-if="pendingFonds.mode_acces && !isDirectAccess(pendingFonds.mode_acces)"
             class="mt-2 bg-amber-50 rounded-lg p-2 text-xs text-amber-700">
          <span class="font-medium">{{ pendingModeAccesLabel }}</span> —
          Ce fonds necessite un intermediaire.
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="pendingFonds = null"
                  class="flex-1 text-sm px-3 py-2 rounded-lg border border-gray-200
                         text-gray-600 hover:bg-gray-50 transition-colors">
            Annuler
          </button>
          <button @click="confirmApplication"
                  class="flex-1 text-sm px-3 py-2 rounded-lg bg-emerald-600 text-white
                         hover:bg-emerald-700 transition-colors font-medium">
            Postuler
          </button>
        </div>
      </div>
    </div>

    <!-- Toast feedback -->
    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" />

    <!-- Derniere synchro -->
    <div class="flex items-center justify-between text-xs text-gray-400 pt-2">
      <span v-if="data?.last_synced">
        Maj : {{ formatRelativeTime(data.last_synced) }}
      </span>
      <button
        @click="$emit('refresh')"
        :disabled="loading"
        class="text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
      >
        <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }"
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11
                11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ t('sync_refresh') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SyncedData, ESGScore, FundApplication, FondsVert } from '@shared/types'
import { t } from '@shared/i18n'
import { useApplications } from '@shared/stores/applications'
import ApplicationCard from './ApplicationCard.vue'
import FundRecommendation from './FundRecommendation.vue'
import Toast from './Toast.vue'

const REFERENTIEL_LABELS: Record<string, string> = {
  bceao_fd_2024: 'BCEAO Finance Durable',
  gcf_standards: 'Green Climate Fund',
  ifc_standards: 'IFC Standards',
}

const props = defineProps<{
  data: SyncedData | null
  loading: boolean
}>()

const emit = defineEmits<{
  refresh: []
  'select-application': [app: FundApplication]
}>()

const { createApplication } = useApplications()

// --- Modal de confirmation ---
const pendingFonds = ref<FondsVert | null>(null)

const MODE_ACCES_LABELS: Record<string, string> = {
  banque_partenaire: 'Via banque partenaire',
  appel_propositions: 'Appel a propositions',
  entite_accreditee: 'Via entite accreditee',
  direct: 'Acces direct',
  garantie_bancaire: 'Garantie bancaire',
  banque_multilaterale: 'Via banque multilaterale',
}

function isDirectAccess(mode: string | null): boolean {
  return !mode || mode === 'direct' || mode === 'appel_propositions'
}

const pendingModeAccesLabel = computed(() =>
  MODE_ACCES_LABELS[pendingFonds.value?.mode_acces || ''] || pendingFonds.value?.mode_acces || '',
)

function handleStartApplication(fonds: FondsVert) {
  pendingFonds.value = fonds
}

async function confirmApplication() {
  if (!pendingFonds.value) return

  const fonds = pendingFonds.value
  pendingFonds.value = null

  const { application: app, isDuplicate } = await createApplication({
    fonds_id: fonds.id,
    fonds_nom: fonds.nom,
    fonds_institution: fonds.institution || '',
    url_candidature: fonds.url_source || undefined,
  })

  if (isDuplicate) {
    showToast('Candidature deja en cours pour ce fonds', 'warning')
    emit('refresh')
    return
  }

  if (!app) {
    showToast('Erreur lors de la creation', 'warning')
    return
  }

  emit('refresh')

  // Workflow adapte selon mode_acces
  if (isDirectAccess(fonds.mode_acces)) {
    // Mode direct / appel a propositions : ouvrir le site + side panel
    if (fonds.url_source) {
      chrome.tabs.create({ url: fonds.url_source })
    }
    chrome.runtime.sendMessage({
      type: 'OPEN_SIDEPANEL',
      payload: { applicationId: app.id },
    })
    showToast(`Candidature demarree pour ${fonds.nom}`, 'success')
  } else if (['banque_partenaire', 'entite_accreditee', 'banque_multilaterale'].includes(fonds.mode_acces || '')) {
    // Mode intermediaire
    const intermediaireUrl = fonds.acces_details?.intermediaire as string | undefined
    if (intermediaireUrl) {
      chrome.tabs.create({ url: intermediaireUrl })
    }
    showToast(`Contactez l'intermediaire pour ${fonds.nom}`, 'info')
  } else if (fonds.mode_acces === 'garantie_bancaire') {
    showToast('Consultez votre banque pour la garantie', 'info')
  } else {
    showToast(`Candidature demarree pour ${fonds.nom}`, 'success')
  }
}

// --- Toast feedback ---
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'warning' | 'info'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string, type: 'success' | 'warning' | 'info' = 'success') {
  toastMessage.value = msg
  toastType.value = type
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 3000)
}

function getExistingApplication(fondsId: string): FundApplication | null {
  return activeApplications.value.find(a => a.fonds_id === fondsId) || null
}

const sortMode = ref<'compatibility' | 'montant' | 'date_limite'>('compatibility')

const sortedRecommendations = computed(() => {
  const fonds = props.data?.fonds_recommandes?.slice(0, 5) || []
  if (sortMode.value === 'compatibility') {
    return [...fonds].sort((a, b) => (b.compatibility_score ?? 0) - (a.compatibility_score ?? 0))
  }
  if (sortMode.value === 'montant') {
    return [...fonds].sort((a, b) => (b.montant_max ?? 0) - (a.montant_max ?? 0))
  }
  if (sortMode.value === 'date_limite') {
    return [...fonds].sort((a, b) => {
      if (!a.date_limite) return 1
      if (!b.date_limite) return -1
      return new Date(a.date_limite).getTime() - new Date(b.date_limite).getTime()
    })
  }
  return fonds
})

const selectedReferentiel = ref<string>('')

// Referentiels disponibles (dedupliques, le plus recent par referentiel)
const availableReferentiels = computed(() => {
  if (!props.data?.scores?.length) return []
  const seen = new Map<string, ESGScore>()
  for (const score of props.data.scores) {
    const existing = seen.get(score.referentiel_code)
    if (!existing || new Date(score.created_at) > new Date(existing.created_at)) {
      seen.set(score.referentiel_code, score)
    }
  }
  return Array.from(seen.keys()).map(code => ({
    code,
    label: REFERENTIEL_LABELS[code] || code,
  }))
})

// Auto-selectionner le premier referentiel quand les donnees arrivent
watch(availableReferentiels, (refs) => {
  if (refs.length > 0 && !selectedReferentiel.value) {
    selectedReferentiel.value = refs[0].code
  }
}, { immediate: true })

// Score pour le referentiel selectionne (le plus recent)
const selectedScore = computed<ESGScore | null>(() => {
  if (!props.data?.scores?.length || !selectedReferentiel.value) return null
  const matching = props.data.scores
    .filter(s => s.referentiel_code === selectedReferentiel.value)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  return matching[0] || null
})

const scoreColor = computed(() => {
  const score = selectedScore.value?.score_global
  if (!score) return 'text-gray-400'
  if (score >= 70) return 'text-emerald-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-red-600'
})

const activeApplications = computed(() => {
  if (!props.data?.applications) return []
  return props.data.applications.filter(
    app => ['brouillon', 'en_cours'].includes(app.status)
  )
})

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return "a l'instant"
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `il y a ${hours}h`
  const days = Math.floor(hours / 24)
  return `il y a ${days}j`
}
</script>
