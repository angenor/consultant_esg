<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore, type Intermediaire } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const filterFonds = ref<string>('')
const filterType = ref<string>('')
const searchQuery = ref('')

const filteredIntermediaires = computed(() => {
  let list = adminStore.intermediaires
  if (filterFonds.value) {
    list = list.filter((i) => i.fonds_id === filterFonds.value)
  }
  if (filterType.value) {
    list = list.filter((i) => i.type === filterType.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (i) =>
        i.nom.toLowerCase().includes(q) ||
        (i.pays && i.pays.toLowerCase().includes(q)),
    )
  }
  return list
})

// Group by fonds for display
const groupedByFonds = computed(() => {
  const groups: Record<string, { fonds_nom: string; items: Intermediaire[] }> = {}
  for (const inter of filteredIntermediaires.value) {
    const fonds = adminStore.fonds.find((f) => f.id === inter.fonds_id)
    const fondsNom = fonds?.nom || inter.fonds_id.slice(0, 8)
    if (!groups[inter.fonds_id]) {
      groups[inter.fonds_id] = { fonds_nom: fondsNom, items: [] }
    }
    groups[inter.fonds_id]!.items.push(inter)
  }
  return Object.values(groups).sort((a, b) => a.fonds_nom.localeCompare(b.fonds_nom))
})

const TYPE_LABELS: Record<string, string> = {
  banque_partenaire: 'Banque partenaire',
  entite_accreditee: 'Entité accréditée',
  agence_nationale: 'Agence nationale',
  bmd: 'BMD',
}

const SOUMISSION_LABELS: Record<string, string> = {
  formulaire_en_ligne: 'Formulaire en ligne',
  email: 'Email',
  dossier_physique: 'Dossier physique',
  portail_dedie: 'Portail dédié',
}

function typeLabel(type: string): string {
  return TYPE_LABELS[type] || type
}

function soumissionLabel(type: string | null): string {
  if (!type) return '-'
  return SOUMISSION_LABELS[type] || type
}

async function handleDelete(i: Intermediaire) {
  if (!confirm(`Supprimer l'intermédiaire "${i.nom}" ?`)) return
  try {
    await adminStore.deleteIntermediaire(i.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur lors de la suppression')
  }
}

onMounted(async () => {
  await Promise.all([adminStore.loadIntermediaires(), adminStore.loadFonds()])
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Intermédiaires</h1>
        <p class="mt-1 text-sm text-gray-500">
          {{ filteredIntermediaires.length }} intermédiaires
          <span v-if="groupedByFonds.length > 0">
            dans {{ groupedByFonds.length }} fonds
          </span>
        </p>
      </div>
      <button
        @click="router.push({ name: 'AdminIntermediaireEdit', params: { id: 'new' } })"
        class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouvel Intermédiaire
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <select
        v-model="filterFonds"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">Tous les fonds</option>
        <option v-for="f in adminStore.fonds" :key="f.id" :value="f.id">{{ f.nom }}</option>
      </select>
      <select
        v-model="filterType"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">Tous types</option>
        <option value="banque_partenaire">Banque partenaire</option>
        <option value="entite_accreditee">Entité accréditée</option>
        <option value="agence_nationale">Agence nationale</option>
        <option value="bmd">BMD</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher nom ou pays..."
        class="flex-1 min-w-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      />
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Grouped list -->
    <div v-if="!adminStore.loading" class="space-y-6">
      <div
        v-for="group in groupedByFonds"
        :key="group.fonds_nom"
        class="bg-white border border-gray-200 rounded-lg overflow-hidden"
      >
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h2 class="text-sm font-semibold text-gray-700">
            {{ group.fonds_nom }}
            <span class="ml-2 text-gray-400 font-normal">({{ group.items.length }})</span>
          </h2>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50/50">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nom</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Pays</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Soumission</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Délai</th>
              <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Rec.</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="inter in group.items" :key="inter.id" class="hover:bg-gray-50">
              <td class="px-4 py-2.5">
                <div class="font-medium text-gray-900 text-sm">{{ inter.nom }}</div>
                <div v-if="inter.email" class="text-xs text-gray-400">{{ inter.email }}</div>
              </td>
              <td class="px-4 py-2.5">
                <span
                  class="px-2 py-0.5 text-xs font-medium rounded-full"
                  :class="{
                    'bg-blue-100 text-blue-700': inter.type === 'banque_partenaire',
                    'bg-purple-100 text-purple-700': inter.type === 'entite_accreditee',
                    'bg-amber-100 text-amber-700': inter.type === 'agence_nationale',
                    'bg-teal-100 text-teal-700': inter.type === 'bmd',
                  }"
                >
                  {{ typeLabel(inter.type) }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-sm text-gray-600">{{ inter.pays || 'Régional' }}</td>
              <td class="px-4 py-2.5 text-sm text-gray-600">{{ soumissionLabel(inter.type_soumission) }}</td>
              <td class="px-4 py-2.5 text-sm text-gray-600">{{ inter.delai_traitement || '-' }}</td>
              <td class="px-4 py-2.5 text-center">
                <span v-if="inter.est_recommande" class="text-emerald-600" title="Recommandé">
                  <svg class="w-4 h-4 inline" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </span>
              </td>
              <td class="px-4 py-2.5 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="router.push({ name: 'AdminIntermediaireEdit', params: { id: inter.id } })"
                    class="text-sm text-emerald-700 hover:text-emerald-800 font-medium"
                  >
                    Modifier
                  </button>
                  <button
                    @click="handleDelete(inter)"
                    class="text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    Supprimer
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-if="filteredIntermediaires.length === 0"
        class="text-center py-12 text-gray-500 bg-white border border-gray-200 rounded-lg"
      >
        Aucun intermédiaire trouvé
      </div>
    </div>
  </div>
</template>
