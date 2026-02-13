<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const isNew = computed(() => route.params.id === 'new')
const fondsId = computed(() => (isNew.value ? null : (route.params.id as string)))

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const form = ref({
  nom: '',
  institution: '',
  type: '',
  referentiel_id: '' as string,
  montant_min: null as number | null,
  montant_max: null as number | null,
  devise: 'USD',
  secteurs_json: '' as string,
  pays_eligibles: '' as string,
  date_limite: '',
  url_source: '',
})

async function loadFonds() {
  if (isNew.value || !fondsId.value) return
  loading.value = true
  try {
    const f = await adminStore.getFonds(fondsId.value)
    form.value = {
      nom: f.nom,
      institution: f.institution || '',
      type: f.type || '',
      referentiel_id: f.referentiel_id || '',
      montant_min: f.montant_min,
      montant_max: f.montant_max,
      devise: f.devise,
      secteurs_json: f.secteurs_json ? f.secteurs_json.join(', ') : '',
      pays_eligibles: f.pays_eligibles ? f.pays_eligibles.join(', ') : '',
      date_limite: f.date_limite || '',
      url_source: f.url_source || '',
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  error.value = null

  const payload: Record<string, unknown> = {
    nom: form.value.nom,
    institution: form.value.institution || null,
    type: form.value.type || null,
    referentiel_id: form.value.referentiel_id || null,
    montant_min: form.value.montant_min,
    montant_max: form.value.montant_max,
    devise: form.value.devise,
    secteurs_json: form.value.secteurs_json
      ? form.value.secteurs_json.split(',').map((s) => s.trim()).filter(Boolean)
      : null,
    pays_eligibles: form.value.pays_eligibles
      ? form.value.pays_eligibles.split(',').map((s) => s.trim()).filter(Boolean)
      : null,
    date_limite: form.value.date_limite || null,
    url_source: form.value.url_source || null,
  }

  try {
    if (isNew.value) {
      const created = await adminStore.createFonds(payload)
      router.replace({ name: 'AdminFondEdit', params: { id: created.id } })
    } else if (fondsId.value) {
      await adminStore.updateFonds(fondsId.value, payload)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await adminStore.loadReferentiels()
  await loadFonds()
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-6">
      <button
        @click="router.push({ name: 'AdminFonds' })"
        class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Retour aux fonds
      </button>
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isNew ? 'Nouveau Fonds Vert' : 'Modifier le Fonds' }}
      </h1>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Form -->
    <form v-if="!loading" @submit.prevent="handleSubmit" class="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
          <input v-model="form.nom" type="text" required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Institution</label>
          <input v-model="form.institution" type="text"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select v-model="form.type"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="">-- Sélectionner --</option>
            <option value="subvention">Subvention</option>
            <option value="pret_concessionnel">Prêt concessionnel</option>
            <option value="garantie">Garantie</option>
            <option value="equity">Equity</option>
            <option value="ligne_credit">Ligne de crédit</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Référentiel ESG associé</label>
          <select v-model="form.referentiel_id"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="">Aucun</option>
            <option v-for="r in adminStore.referentiels" :key="r.id" :value="r.id">{{ r.nom }}</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Montant min</label>
          <input v-model.number="form.montant_min" type="number"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Montant max</label>
          <input v-model.number="form.montant_max" type="number"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Devise</label>
          <select v-model="form.devise"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="XOF">XOF</option>
            <option value="XAF">XAF</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Secteurs (séparés par des virgules)</label>
          <input v-model="form.secteurs_json" type="text" placeholder="agriculture, énergie, transport"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Pays éligibles (séparés par des virgules)</label>
          <input v-model="form.pays_eligibles" type="text" placeholder="Sénégal, Côte d'Ivoire, Mali"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Date limite</label>
          <input v-model="form.date_limite" type="date"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">URL source</label>
          <input v-model="form.url_source" type="url" placeholder="https://..."
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3 pt-4 border-t border-gray-200">
        <button type="submit" :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50">
          {{ isNew ? 'Créer le Fonds' : 'Sauvegarder' }}
        </button>
        <button type="button" @click="router.push({ name: 'AdminFonds' })"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
          Annuler
        </button>
      </div>
    </form>
  </div>
</template>
