<script setup lang="ts">
import { ref } from 'vue'
import { useAdminStore, type ScorePreviewResult } from '../../stores/admin'
import SkillCodeEditor from './SkillCodeEditor.vue'

const props = defineProps<{
  referentielId: string | null
}>()

const adminStore = useAdminStore()
const jsonInput = ref('{\n  \n}')
const result = ref<ScorePreviewResult | null>(null)
const running = ref(false)
const error = ref<string | null>(null)

async function runSimulation() {
  if (!props.referentielId) return
  running.value = true
  error.value = null
  result.value = null

  try {
    const reponses = JSON.parse(jsonInput.value)
    result.value = await adminStore.previewScoring(props.referentielId, reponses)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur de simulation'
  } finally {
    running.value = false
  }
}

function niveauColor(niveau: string) {
  if (niveau === 'Excellent') return 'text-emerald-600'
  if (niveau === 'Bon') return 'text-blue-600'
  if (niveau === 'À améliorer') return 'text-amber-600'
  return 'text-red-600'
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-lg p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Simuler un scoring</h3>

    <div v-if="!referentielId" class="text-sm text-gray-500">
      Sauvegardez d'abord le référentiel pour pouvoir simuler.
    </div>

    <template v-else>
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Données test (JSON) — réponses aux critères
        </label>
        <SkillCodeEditor
          v-model="jsonInput"
          language="json"
          height="150px"
          placeholder='{ "emissions_carbone": 350, "gestion_dechets": "Tri sélectif en place" }'
        />
      </div>

      <button
        @click="runSimulation"
        :disabled="running"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
      >
        <span v-if="running" class="animate-spin">&#8635;</span>
        Simuler le scoring
      </button>

      <!-- Error -->
      <div v-if="error" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        {{ error }}
      </div>

      <!-- Result -->
      <div v-if="result" class="mt-4 border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-gray-900">
              Score Global: {{ result.score_global }}/100
            </span>
            <span :class="niveauColor(result.niveau)" class="font-semibold">
              {{ result.niveau }}
            </span>
          </div>
        </div>

        <!-- Piliers breakdown -->
        <div class="divide-y divide-gray-200">
          <div v-for="(pilier, name) in result.piliers" :key="name" class="px-4 py-3">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900 capitalize">{{ name }}</span>
              <span class="text-sm font-semibold">
                {{ pilier.score }}/100
                <span class="text-gray-400 font-normal">(poids: {{ Math.round(pilier.poids_global * 100) }}%)</span>
              </span>
            </div>
            <!-- Progress bar -->
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                class="h-2 rounded-full"
                :class="pilier.score >= 70 ? 'bg-emerald-500' : pilier.score >= 40 ? 'bg-amber-500' : 'bg-red-500'"
                :style="{ width: pilier.score + '%' }"
              ></div>
            </div>
            <!-- Criteres detail -->
            <div class="space-y-1">
              <div
                v-for="c in pilier.criteres"
                :key="c.critere_id"
                class="flex items-center justify-between text-sm"
              >
                <span class="text-gray-600">
                  <span v-if="c.status === 'conforme'" class="text-emerald-600 mr-1">&#10003;</span>
                  <span v-else-if="c.status === 'partiel'" class="text-amber-500 mr-1">&#9888;</span>
                  <span v-else class="text-red-500 mr-1">&#10007;</span>
                  {{ c.label }}
                </span>
                <span class="text-gray-500">
                  {{ c.score }}/100
                  <span v-if="c.valeur" class="text-gray-400 ml-1">({{ c.valeur }})</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
