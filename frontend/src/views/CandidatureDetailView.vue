<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCandidaturesStore } from '../stores/candidatures'
import StatusBadge from '../components/candidatures/StatusBadge.vue'
import CandidatureTimeline from '../components/candidatures/CandidatureTimeline.vue'
import DocumentsList from '../components/candidatures/DocumentsList.vue'

const route = useRoute()
const router = useRouter()
const store = useCandidaturesStore()

const showStatusModal = ref(false)
const newStatus = ref('')

const STATUTS = [
  { value: 'brouillon', label: 'Brouillon' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'soumise', label: 'Soumise' },
  { value: 'acceptee', label: 'Acceptée' },
  { value: 'refusee', label: 'Refusée' },
  { value: 'abandonnee', label: 'Abandonnée' },
]

const candidature = computed(() => store.currentDetail)

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function timeSince(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days < 7) return `${days} jour${days > 1 ? 's' : ''}`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks} semaine${weeks > 1 ? 's' : ''}`
  const months = Math.floor(days / 30)
  return `${months} mois`
}

async function changeStatus() {
  if (!candidature.value || !newStatus.value) return
  await store.updateCandidature(candidature.value.id, { status: newStatus.value })
  showStatusModal.value = false
  await store.getCandidature(candidature.value.id)
}

function handleTimelineAction(action: { type: string; label: string }) {
  if (!candidature.value) return
  if (action.type === 'open_extension' && candidature.value.url_candidature) {
    window.open(candidature.value.url_candidature, '_blank')
  } else if (action.type === 'view_dossier') {
    // Scroll to documents section
    document.getElementById('documents-section')?.scrollIntoView({ behavior: 'smooth' })
  } else if (action.type === 'view_score') {
    router.push('/dashboard')
  }
}

onMounted(() => {
  const id = route.params.id as string
  if (id) store.getCandidature(id)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="store.loadingDetail" class="flex justify-center py-20">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
    </div>

    <!-- Not found -->
    <div v-else-if="!candidature" class="text-center py-20">
      <p class="text-gray-500">Candidature introuvable.</p>
      <router-link to="/candidatures" class="mt-2 inline-block text-sm text-emerald-600 hover:underline">
        Retour aux candidatures
      </router-link>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center gap-3">
        <router-link
          to="/candidatures"
          class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </router-link>
        <div class="flex-1 min-w-0">
          <h1 class="text-xl font-bold text-gray-900 truncate">{{ candidature.fonds_nom }}</h1>
          <p class="text-sm text-gray-500">{{ candidature.fonds_institution }}</p>
        </div>
        <button
          @click="showStatusModal = true; newStatus = candidature.status"
          class="text-sm text-gray-500 hover:text-gray-700 border rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
        >
          Modifier statut
        </button>
      </div>

      <!-- Info cards -->
      <div class="grid sm:grid-cols-2 gap-4">
        <!-- Infos générales -->
        <div class="bg-white border rounded-xl p-5">
          <h2 class="font-semibold text-gray-900 mb-3">Informations générales</h2>
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between">
              <dt class="text-gray-500">Fonds</dt>
              <dd class="text-gray-900 font-medium">{{ candidature.fonds_nom }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Institution</dt>
              <dd class="text-gray-900">{{ candidature.fonds_institution || '-' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Démarrée le</dt>
              <dd class="text-gray-900">{{ formatDate(candidature.started_at) }}</dd>
            </div>
            <div v-if="candidature.submitted_at" class="flex justify-between">
              <dt class="text-gray-500">Soumise le</dt>
              <dd class="text-gray-900">{{ formatDate(candidature.submitted_at) }}</dd>
            </div>
            <div v-if="candidature.notes" class="pt-2 border-t">
              <dt class="text-gray-500 mb-1">Notes</dt>
              <dd class="text-gray-700 text-xs">{{ candidature.notes }}</dd>
            </div>
          </dl>
        </div>

        <!-- Statut et progression -->
        <div class="bg-white border rounded-xl p-5">
          <h2 class="font-semibold text-gray-900 mb-3">Statut</h2>
          <div class="flex items-center gap-3 mb-4">
            <StatusBadge :status="candidature.status" />
            <span class="text-sm text-gray-500">Depuis {{ timeSince(candidature.started_at) }}</span>
          </div>
          <!-- Barre de progression -->
          <div>
            <div class="flex justify-between text-sm mb-2">
              <span class="text-gray-500">Progression</span>
              <span class="font-semibold text-gray-900">{{ Math.round(candidature.progress_pct) }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
              <div
                class="h-3 rounded-full transition-all duration-700"
                :class="candidature.progress_pct >= 100 ? 'bg-emerald-500' : 'bg-blue-500'"
                :style="{ width: candidature.progress_pct + '%' }"
              />
            </div>
            <p v-if="candidature.total_steps" class="text-xs text-gray-400 mt-1">
              Étape {{ candidature.current_step }} sur {{ candidature.total_steps }}
            </p>
          </div>
          <!-- Bouton ouvrir extension -->
          <a
            v-if="candidature.url_candidature && ['brouillon', 'en_cours'].includes(candidature.status)"
            :href="candidature.url_candidature"
            target="_blank"
            class="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-600 hover:text-emerald-700"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Ouvrir le formulaire (extension)
          </a>
        </div>
      </div>

      <!-- Timeline -->
      <div class="bg-white border rounded-xl p-5">
        <h2 class="font-semibold text-gray-900 mb-4">Timeline du processus</h2>
        <CandidatureTimeline
          v-if="candidature.timeline.length > 0"
          :steps="candidature.timeline"
          @action="handleTimelineAction"
        />
        <p v-else class="text-sm text-gray-400 text-center py-4">
          Aucune étape définie pour cette candidature.
        </p>
      </div>

      <!-- Documents -->
      <div id="documents-section" class="bg-white border rounded-xl p-5">
        <div class="flex justify-between items-center mb-4">
          <h2 class="font-semibold text-gray-900">Documents du dossier</h2>
          <span v-if="candidature.documents.length > 0" class="text-xs text-gray-400">
            {{ candidature.documents.length }} document{{ candidature.documents.length > 1 ? 's' : '' }}
          </span>
        </div>
        <DocumentsList :documents="candidature.documents" />
      </div>

      <!-- Historique -->
      <div class="bg-white border rounded-xl p-5">
        <h2 class="font-semibold text-gray-900 mb-4">Historique</h2>
        <div v-if="candidature.history.length > 0" class="space-y-3">
          <div v-for="(entry, i) in candidature.history" :key="i" class="flex gap-3 text-sm">
            <span class="text-gray-400 shrink-0 w-20">{{ entry.date }}</span>
            <span class="text-gray-700">{{ entry.action }}</span>
          </div>
        </div>
        <p v-else class="text-sm text-gray-400 text-center py-4">Aucun historique disponible.</p>
      </div>
    </template>

    <!-- Modal changement de statut -->
    <div
      v-if="showStatusModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="showStatusModal = false"
    >
      <div class="max-w-sm w-full rounded-2xl bg-white p-6 shadow-xl mx-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Modifier le statut</h3>
        <select
          v-model="newStatus"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm mb-4 focus:border-emerald-500 focus:ring-emerald-500"
        >
          <option v-for="s in STATUTS" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <div class="flex justify-end gap-3">
          <button
            @click="showStatusModal = false"
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Annuler
          </button>
          <button
            @click="changeStatus"
            class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700"
          >
            Confirmer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
