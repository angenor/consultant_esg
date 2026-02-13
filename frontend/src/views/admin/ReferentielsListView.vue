<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore, type Referentiel } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const filterRegion = ref<string>('')
const filterStatus = ref<string>('')
const searchQuery = ref('')

const filteredReferentiels = computed(() => {
  let list = adminStore.referentiels

  if (filterRegion.value) {
    list = list.filter((r) => r.region === filterRegion.value)
  }
  if (filterStatus.value === 'active') {
    list = list.filter((r) => r.is_active)
  } else if (filterStatus.value === 'inactive') {
    list = list.filter((r) => !r.is_active)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (r) => r.nom.toLowerCase().includes(q) || r.code.toLowerCase().includes(q),
    )
  }
  return list
})

const regions = computed(() => {
  const set = new Set(adminStore.referentiels.map((r) => r.region).filter((v): v is string => !!v))
  return Array.from(set).sort()
})

function getPilierWeights(ref: Referentiel) {
  const piliers = ref.grille_json?.piliers
  if (!piliers) return []
  return Object.entries(piliers).map(([name, data]) => ({
    name: name.charAt(0).toUpperCase(),
    poids: Math.round((data.poids_global || 0) * 100),
  }))
}

function getCriteresCount(ref: Referentiel) {
  const piliers = ref.grille_json?.piliers
  if (!piliers) return 0
  return Object.values(piliers).reduce((sum, p) => sum + (p.criteres?.length || 0), 0)
}

function getMethodeLabel(ref: Referentiel) {
  const m = ref.grille_json?.methode_aggregation
  if (m === 'weighted_average') return 'Moyenne pondérée'
  if (m === 'minimum_thresholds') return 'Seuils minimum'
  return m || '-'
}

async function handleToggle(ref: Referentiel) {
  await adminStore.toggleReferentiel(ref.id)
}

async function handleDelete(ref: Referentiel) {
  if (!confirm(`Supprimer le référentiel "${ref.nom}" ?`)) return
  try {
    await adminStore.deleteReferentiel(ref.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur lors de la suppression')
  }
}

onMounted(() => adminStore.loadReferentiels())
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Référentiels ESG</h1>
        <p class="mt-1 text-sm text-gray-500">
          {{ filteredReferentiels.length }} référentiel(s)
        </p>
      </div>
      <button
        @click="router.push({ name: 'AdminReferentielNew' })"
        class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouveau Référentiel
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <select
        v-model="filterRegion"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      >
        <option value="">Toutes régions</option>
        <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
      </select>
      <select
        v-model="filterStatus"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      >
        <option value="">Tous statuts</option>
        <option value="active">Actifs</option>
        <option value="inactive">Inactifs</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher..."
        class="flex-1 min-w-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      />
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Error -->
    <div
      v-if="adminStore.error"
      class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700"
    >
      {{ adminStore.error }}
    </div>

    <!-- List -->
    <div v-if="!adminStore.loading" class="space-y-4">
      <div
        v-for="ref in filteredReferentiels"
        :key="ref.id"
        class="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <h3 class="text-lg font-semibold text-gray-900">{{ ref.nom }}</h3>
              <span
                :class="ref.is_active
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-red-100 text-red-700'"
                class="px-2 py-0.5 text-xs font-medium rounded-full"
              >
                {{ ref.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
              <span v-if="ref.institution">
                <strong>Institution:</strong> {{ ref.institution }}
              </span>
              <span v-if="ref.region">
                <strong>Région:</strong> {{ ref.region }}
              </span>
              <span>
                <strong>Méthode:</strong> {{ getMethodeLabel(ref) }}
              </span>
            </div>
            <div class="mt-2 flex items-center gap-4 text-sm">
              <span
                v-for="p in getPilierWeights(ref)"
                :key="p.name"
                class="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-gray-700"
              >
                {{ p.name }}: {{ p.poids }}%
              </span>
              <span class="text-gray-500">{{ getCriteresCount(ref) }} critères</span>
            </div>
            <p v-if="ref.description" class="mt-2 text-sm text-gray-600 line-clamp-2">
              {{ ref.description }}
            </p>
          </div>
          <div class="flex items-center gap-2 ml-4">
            <button
              @click="router.push({ name: 'AdminReferentielEdit', params: { id: ref.id } })"
              class="px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100"
            >
              Modifier
            </button>
            <button
              @click="handleToggle(ref)"
              :class="ref.is_active
                ? 'text-amber-700 bg-amber-50 hover:bg-amber-100'
                : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100'"
              class="px-3 py-1.5 text-sm font-medium rounded-lg"
            >
              {{ ref.is_active ? 'Désactiver' : 'Activer' }}
            </button>
            <button
              @click="handleDelete(ref)"
              class="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100"
            >
              Supprimer
            </button>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="filteredReferentiels.length === 0 && !adminStore.loading"
        class="text-center py-12 text-gray-500"
      >
        <p class="text-lg">Aucun référentiel trouvé</p>
        <p class="text-sm mt-1">Ajustez vos filtres ou créez un nouveau référentiel</p>
      </div>
    </div>
  </div>
</template>
