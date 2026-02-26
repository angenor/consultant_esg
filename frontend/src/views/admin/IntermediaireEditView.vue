<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const isNew = computed(() => route.params.id === 'new')
const intermediaireld = computed(() => (isNew.value ? null : (route.params.id as string)))

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const form = ref({
  fonds_id: '' as string,
  nom: '',
  type: '',
  pays: '',
  ville: '',
  email: '',
  telephone: '',
  adresse: '',
  site_web: '',
  url_formulaire: '',
  type_soumission: '',
  instructions_soumission: '',
  delai_traitement: '',
  est_recommande: false,
  notes: '',
})

async function loadIntermediaire() {
  if (isNew.value || !intermediaireld.value) return
  loading.value = true
  try {
    const i = await adminStore.getIntermediaire(intermediaireld.value)
    form.value = {
      fonds_id: i.fonds_id,
      nom: i.nom,
      type: i.type,
      pays: i.pays || '',
      ville: i.ville || '',
      email: i.email || '',
      telephone: i.telephone || '',
      adresse: i.adresse || '',
      site_web: i.site_web || '',
      url_formulaire: i.url_formulaire || '',
      type_soumission: i.type_soumission || '',
      instructions_soumission: i.instructions_soumission || '',
      delai_traitement: i.delai_traitement || '',
      est_recommande: i.est_recommande,
      notes: i.notes || '',
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
    fonds_id: form.value.fonds_id || null,
    nom: form.value.nom,
    type: form.value.type,
    pays: form.value.pays || null,
    ville: form.value.ville || null,
    email: form.value.email || null,
    telephone: form.value.telephone || null,
    adresse: form.value.adresse || null,
    site_web: form.value.site_web || null,
    url_formulaire: form.value.url_formulaire || null,
    type_soumission: form.value.type_soumission || null,
    instructions_soumission: form.value.instructions_soumission || null,
    delai_traitement: form.value.delai_traitement || null,
    est_recommande: form.value.est_recommande,
    notes: form.value.notes || null,
  }

  try {
    if (isNew.value) {
      const created = await adminStore.createIntermediaire(payload)
      router.replace({ name: 'AdminIntermediaireEdit', params: { id: created.id } })
    } else if (intermediaireld.value) {
      await adminStore.updateIntermediaire(intermediaireld.value, payload)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await adminStore.loadFonds()
  await loadIntermediaire()
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-6">
      <button
        @click="router.push({ name: 'AdminIntermediaires' })"
        class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Retour aux intermédiaires
      </button>
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isNew ? 'Nouvel Intermédiaire' : 'Modifier l\'Intermédiaire' }}
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

      <!-- Fonds + Nom -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fonds vert *</label>
          <select v-model="form.fonds_id" required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="">-- Sélectionner --</option>
            <option v-for="f in adminStore.fonds" :key="f.id" :value="f.id">{{ f.nom }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
          <input v-model="form.nom" type="text" required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <!-- Type + Pays + Ville -->
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type *</label>
          <select v-model="form.type" required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="">-- Sélectionner --</option>
            <option value="banque_partenaire">Banque partenaire</option>
            <option value="entite_accreditee">Entité accréditée</option>
            <option value="agence_nationale">Agence nationale</option>
            <option value="bmd">BMD</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Pays</label>
          <input v-model="form.pays" type="text" placeholder="Côte d'Ivoire"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Ville</label>
          <input v-model="form.ville" type="text" placeholder="Abidjan"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <!-- Contact -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="form.email" type="email" placeholder="contact@example.com"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
          <input v-model="form.telephone" type="text" placeholder="+225 27 20 ..."
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Site web</label>
        <input v-model="form.site_web" type="url" placeholder="https://..."
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
      </div>

      <!-- Soumission -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type de soumission</label>
          <select v-model="form.type_soumission"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500">
            <option value="">-- Non spécifié --</option>
            <option value="formulaire_en_ligne">Formulaire en ligne</option>
            <option value="email">Email</option>
            <option value="dossier_physique">Dossier physique</option>
            <option value="portail_dedie">Portail dédié</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">URL formulaire</label>
          <input v-model="form.url_formulaire" type="url" placeholder="https://..."
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Instructions de soumission</label>
        <textarea v-model="form.instructions_soumission" rows="2"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"></textarea>
      </div>

      <!-- Délai + Recommandé -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Délai de traitement</label>
          <input v-model="form.delai_traitement" type="text" placeholder="4-6 semaines"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div class="flex items-end">
          <label class="flex items-center gap-2 text-sm text-gray-700 pb-2">
            <input v-model="form.est_recommande" type="checkbox"
              class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
            Intermédiaire recommandé
          </label>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
        <textarea v-model="form.adresse" rows="2"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea v-model="form.notes" rows="2"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"></textarea>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3 pt-4 border-t border-gray-200">
        <button type="submit" :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50">
          {{ isNew ? 'Créer l\'Intermédiaire' : 'Sauvegarder' }}
        </button>
        <button type="button" @click="router.push({ name: 'AdminIntermediaires' })"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
          Annuler
        </button>
      </div>
    </form>
  </div>
</template>
