<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore, type Fonds } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const filterStatus = ref<string>('')
const searchQuery = ref('')

const filteredFonds = computed(() => {
  let list = adminStore.fonds
  if (filterStatus.value === 'active') {
    list = list.filter((f) => f.is_active)
  } else if (filterStatus.value === 'inactive') {
    list = list.filter((f) => !f.is_active)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter((f) => f.nom.toLowerCase().includes(q))
  }
  return list
})

function formatMontant(val: number | null) {
  if (val === null || val === undefined) return '-'
  return new Intl.NumberFormat('fr-FR').format(val)
}

function getReferentielNom(refId: string | null) {
  if (!refId) return '-'
  const ref = adminStore.referentiels.find((r) => r.id === refId)
  return ref ? ref.nom : refId.slice(0, 8) + '...'
}

async function handleDelete(f: Fonds) {
  if (!confirm(`Supprimer le fonds "${f.nom}" ?`)) return
  try {
    await adminStore.deleteFonds(f.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur lors de la suppression')
  }
}

onMounted(async () => {
  await Promise.all([adminStore.loadFonds(), adminStore.loadReferentiels()])
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Fonds Verts</h1>
        <p class="mt-1 text-sm text-gray-500">{{ filteredFonds.length }} fonds</p>
      </div>
      <button
        @click="router.push({ name: 'AdminFondEdit', params: { id: 'new' } })"
        class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouveau Fonds
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <select
        v-model="filterStatus"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">Tous statuts</option>
        <option value="active">Actifs</option>
        <option value="inactive">Inactifs</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher..."
        class="flex-1 min-w-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      />
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Table -->
    <div v-if="!adminStore.loading" class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nom</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Institution</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Montants</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Référentiel</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="f in filteredFonds" :key="f.id" class="hover:bg-gray-50">
            <td class="px-4 py-3">
              <div class="font-medium text-gray-900">{{ f.nom }}</div>
              <div v-if="f.type" class="text-xs text-gray-500">{{ f.type }}</div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ f.institution || '-' }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">
              <span v-if="f.montant_min || f.montant_max">
                {{ formatMontant(f.montant_min) }} - {{ formatMontant(f.montant_max) }} {{ f.devise }}
              </span>
              <span v-else>-</span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ getReferentielNom(f.referentiel_id) }}</td>
            <td class="px-4 py-3">
              <span
                :class="f.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'"
                class="px-2 py-0.5 text-xs font-medium rounded-full"
              >
                {{ f.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-2">
                <button
                  @click="router.push({ name: 'AdminFondEdit', params: { id: f.id } })"
                  class="text-sm text-emerald-700 hover:text-emerald-800 font-medium"
                >
                  Modifier
                </button>
                <button
                  @click="handleDelete(f)"
                  class="text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  Supprimer
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="filteredFonds.length === 0"
        class="text-center py-12 text-gray-500"
      >
        Aucun fonds trouvé
      </div>
    </div>
  </div>
</template>
