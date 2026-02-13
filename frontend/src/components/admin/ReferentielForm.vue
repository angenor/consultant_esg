<script setup lang="ts">
import { ref, watch } from 'vue'
import type { GrilleESG } from '../../stores/admin'
import GrilleEditor from './GrilleEditor.vue'

export interface ReferentielFormData {
  nom: string
  code: string
  institution: string
  description: string
  region: string
  grille_json: GrilleESG
}

const props = defineProps<{
  initialData?: ReferentielFormData
  isEdit: boolean
  saving: boolean
}>()

const emit = defineEmits<{
  submit: [data: ReferentielFormData]
  cancel: []
}>()

const defaultGrille: GrilleESG = {
  methode_aggregation: 'weighted_average',
  piliers: {
    environnement: { poids_global: 0.4, criteres: [] },
    social: { poids_global: 0.3, criteres: [] },
    gouvernance: { poids_global: 0.3, criteres: [] },
  },
}

const form = ref<ReferentielFormData>({
  nom: props.initialData?.nom || '',
  code: props.initialData?.code || '',
  institution: props.initialData?.institution || '',
  description: props.initialData?.description || '',
  region: props.initialData?.region || '',
  grille_json: props.initialData?.grille_json || { ...defaultGrille },
})

watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      form.value = {
        nom: newData.nom || '',
        code: newData.code || '',
        institution: newData.institution || '',
        description: newData.description || '',
        region: newData.region || '',
        grille_json: newData.grille_json || { ...defaultGrille },
      }
    }
  },
)

function autoCode() {
  if (!props.isEdit && form.value.nom) {
    form.value.code = form.value.nom
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, '')
  }
}

function handleSubmit() {
  emit('submit', { ...form.value })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- Basic fields -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
        <input
          v-model="form.nom"
          type="text"
          required
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="BCEAO Finance Durable 2024"
          @input="autoCode()"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Code technique *</label>
        <input
          v-model="form.code"
          type="text"
          required
          :disabled="isEdit"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100"
          placeholder="bceao_fd_2024"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Institution</label>
        <input
          v-model="form.institution"
          type="text"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="BCEAO"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Région</label>
        <select
          v-model="form.region"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
        >
          <option value="">-- Sélectionner --</option>
          <option value="UEMOA">UEMOA</option>
          <option value="CEMAC">CEMAC</option>
          <option value="Afrique de l'Ouest">Afrique de l'Ouest</option>
          <option value="Afrique Centrale">Afrique Centrale</option>
          <option value="International">International</option>
        </select>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
      <textarea
        v-model="form.description"
        rows="3"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
        placeholder="Description du référentiel..."
      ></textarea>
    </div>

    <!-- Grille Editor -->
    <div>
      <h3 class="text-lg font-semibold text-gray-900 mb-3">Grille ESG</h3>
      <GrilleEditor v-model="form.grille_json" />
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-3 pt-4 border-t border-gray-200">
      <button
        type="submit"
        :disabled="saving"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
      >
        <span v-if="saving" class="animate-spin">&#8635;</span>
        {{ isEdit ? 'Sauvegarder' : 'Créer le Référentiel' }}
      </button>
      <button
        type="button"
        @click="emit('cancel')"
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
      >
        Annuler
      </button>
    </div>
  </form>
</template>
