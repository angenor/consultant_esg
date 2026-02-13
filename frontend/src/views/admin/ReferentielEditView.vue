<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore, type Referentiel } from '../../stores/admin'
import ReferentielForm, { type ReferentielFormData } from '../../components/admin/ReferentielForm.vue'
import ScoringSimulator from '../../components/admin/ScoringSimulator.vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const isNew = computed(() => route.name === 'AdminReferentielNew')
const refId = computed(() => (isNew.value ? null : (route.params.id as string)))

const referentiel = ref<Referentiel | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const savedRefId = ref<string | null>(null)

const initialData = computed(() => {
  if (!referentiel.value) return undefined
  return {
    nom: referentiel.value.nom,
    code: referentiel.value.code,
    institution: referentiel.value.institution || '',
    description: referentiel.value.description || '',
    region: referentiel.value.region || '',
    grille_json: referentiel.value.grille_json,
  }
})

async function loadReferentiel() {
  if (isNew.value || !refId.value) return
  loading.value = true
  error.value = null
  try {
    referentiel.value = await adminStore.getReferentiel(refId.value)
    savedRefId.value = referentiel.value.id
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
  } finally {
    loading.value = false
  }
}

async function handleSubmit(data: ReferentielFormData) {
  saving.value = true
  error.value = null

  try {
    if (isNew.value) {
      const created = await adminStore.createReferentiel(data)
      savedRefId.value = created.id
      router.replace({ name: 'AdminReferentielEdit', params: { id: created.id } })
    } else if (refId.value) {
      const updatePayload: Record<string, unknown> = {}
      if (data.nom) updatePayload.nom = data.nom
      if (data.institution) updatePayload.institution = data.institution
      if (data.description) updatePayload.description = data.description
      if (data.region) updatePayload.region = data.region
      if (data.grille_json) updatePayload.grille_json = data.grille_json
      await adminStore.updateReferentiel(refId.value, updatePayload)
      referentiel.value = await adminStore.getReferentiel(refId.value)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'AdminReferentiels' })
}

onMounted(loadReferentiel)
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-6">
      <button
        @click="router.push({ name: 'AdminReferentiels' })"
        class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Retour aux référentiels
      </button>
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isNew ? 'Créer un Référentiel ESG' : `Modifier : ${referentiel?.nom || '...'}` }}
      </h1>
      <p v-if="referentiel" class="mt-1 text-sm text-gray-500">
        Code: {{ referentiel.code }} &middot;
        <span :class="referentiel.is_active ? 'text-emerald-600' : 'text-red-500'">
          {{ referentiel.is_active ? 'Actif' : 'Inactif' }}
        </span>
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700"
    >
      {{ error }}
    </div>

    <!-- Form -->
    <div v-if="!loading" class="space-y-6">
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <ReferentielForm
          :initial-data="initialData"
          :is-edit="!isNew"
          :saving="saving"
          @submit="handleSubmit"
          @cancel="handleCancel"
        />
      </div>

      <!-- Scoring Simulator -->
      <ScoringSimulator :referentiel-id="savedRefId || refId" />
    </div>
  </div>
</template>
