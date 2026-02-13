<script setup lang="ts">
import { ref, watch } from 'vue'
import type { GrilleESG, PilierData, CritereData } from '../../stores/admin'

const props = defineProps<{
  modelValue: GrilleESG
}>()

const emit = defineEmits<{
  'update:modelValue': [value: GrilleESG]
}>()

interface EditableCritere extends CritereData {
  _expanded: boolean
}

interface EditablePilier {
  name: string
  poids_global: number
  criteres: EditableCritere[]
}

const methode = ref(props.modelValue.methode_aggregation || 'weighted_average')
const piliers = ref<EditablePilier[]>([])

function loadFromGrille(g: GrilleESG) {
  methode.value = g.methode_aggregation || 'weighted_average'
  piliers.value = Object.entries(g.piliers || {}).map(([name, data]) => ({
    name,
    poids_global: data.poids_global,
    criteres: (data.criteres || []).map((c) => ({ ...c, _expanded: false })),
  }))
}

loadFromGrille(props.modelValue)

watch(
  () => props.modelValue,
  (newVal) => loadFromGrille(newVal),
  { deep: true },
)

function emitUpdate() {
  const piliersObj: Record<string, PilierData> = {}
  for (const p of piliers.value) {
    piliersObj[p.name] = {
      poids_global: p.poids_global,
      criteres: p.criteres.map(({ _expanded, ...rest }) => rest),
    }
  }
  emit('update:modelValue', {
    methode_aggregation: methode.value,
    piliers: piliersObj,
  })
}

function addPilier() {
  const name = prompt('Nom du pilier (ex: environnement)')
  if (!name) return
  piliers.value.push({ name: name.toLowerCase(), poids_global: 0, criteres: [] })
  emitUpdate()
}

function removePilier(index: number) {
  if (!confirm('Supprimer ce pilier et tous ses critères ?')) return
  piliers.value.splice(index, 1)
  emitUpdate()
}

function addCritere(pilierIndex: number) {
  piliers.value[pilierIndex]?.criteres.push({
    id: '',
    label: '',
    poids: 0,
    type: 'qualitatif',
    options: [{ label: '', score: 100 }],
    question_collecte: '',
    _expanded: true,
  })
  emitUpdate()
}

function removeCritere(pilierIndex: number, critereIndex: number) {
  piliers.value[pilierIndex]?.criteres.splice(critereIndex, 1)
  emitUpdate()
}

function addOption(critere: EditableCritere) {
  if (!critere.options) critere.options = []
  critere.options.push({ label: '', score: 0 })
  emitUpdate()
}

function removeOption(critere: EditableCritere, index: number) {
  critere.options?.splice(index, 1)
  emitUpdate()
}

function switchType(critere: EditableCritere) {
  if (critere.type === 'quantitatif') {
    critere.seuils = { excellent: { max: 50, score: 100 }, bon: { max: 200, score: 70 }, moyen: { max: 500, score: 40 }, faible: { min: 500, score: 10 } }
    critere.unite = ''
    delete critere.options
  } else {
    critere.options = [{ label: '', score: 100 }]
    delete critere.seuils
    delete critere.unite
  }
  emitUpdate()
}

function totalPoidsGlobal() {
  return piliers.value.reduce((s, p) => s + (Number(p.poids_global) || 0), 0)
}

function totalPoidsCriteres(pilier: EditablePilier) {
  return pilier.criteres.reduce((s, c) => s + (Number(c.poids) || 0), 0)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Methode -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Méthode d'agrégation</label>
      <select
        v-model="methode"
        @change="emitUpdate()"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full max-w-xs focus:ring-2 focus:ring-emerald-500"
      >
        <option value="weighted_average">Moyenne pondérée</option>
        <option value="minimum_thresholds">Seuils minimum</option>
      </select>
    </div>

    <!-- Piliers -->
    <div
      v-for="(pilier, pi) in piliers"
      :key="pi"
      class="border border-gray-300 rounded-lg overflow-hidden"
    >
      <!-- Pilier header -->
      <div class="bg-gray-50 px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <h3 class="font-semibold text-gray-900 capitalize">{{ pilier.name }}</h3>
          <div class="flex items-center gap-2 text-sm">
            <label class="text-gray-500">Poids global:</label>
            <input
              v-model.number="pilier.poids_global"
              type="number"
              step="0.05"
              min="0"
              max="1"
              class="w-20 border border-gray-300 rounded px-2 py-1 text-sm text-center"
              @change="emitUpdate()"
            />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="addCritere(pi)"
            class="text-sm text-emerald-700 hover:text-emerald-800 font-medium"
          >
            + Critère
          </button>
          <button
            @click="removePilier(pi)"
            class="text-sm text-red-600 hover:text-red-700"
          >
            Supprimer
          </button>
        </div>
      </div>

      <!-- Criteres -->
      <div class="divide-y divide-gray-200">
        <div
          v-for="(critere, ci) in pilier.criteres"
          :key="ci"
          class="px-4 py-3"
        >
          <!-- Critere summary -->
          <div class="flex items-center justify-between">
            <div
              class="flex items-center gap-3 flex-1 cursor-pointer"
              @click="critere._expanded = !critere._expanded"
            >
              <svg
                class="w-4 h-4 text-gray-400 transition-transform"
                :class="{ 'rotate-90': critere._expanded }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <span class="text-sm font-medium text-gray-900">
                {{ critere.label || '(nouveau critère)' }}
              </span>
              <span class="text-xs text-gray-500">{{ critere.id }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full"
                :class="critere.type === 'quantitatif'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-purple-100 text-purple-700'"
              >
                {{ critere.type }}
              </span>
              <span class="text-xs text-gray-500">poids: {{ critere.poids }}</span>
            </div>
            <button
              @click="removeCritere(pi, ci)"
              class="text-sm text-red-600 hover:text-red-700"
            >
              Supprimer
            </button>
          </div>

          <!-- Critere details (expanded) -->
          <div v-if="critere._expanded" class="mt-3 ml-7 space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">ID</label>
                <input
                  v-model="critere.id"
                  type="text"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  placeholder="ex: emissions_carbone"
                  @input="emitUpdate()"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Label</label>
                <input
                  v-model="critere.label"
                  type="text"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  placeholder="ex: Émissions de GES"
                  @input="emitUpdate()"
                />
              </div>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Poids</label>
                <input
                  v-model.number="critere.poids"
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  @change="emitUpdate()"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Type</label>
                <select
                  v-model="critere.type"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  @change="switchType(critere); emitUpdate()"
                >
                  <option value="quantitatif">Quantitatif</option>
                  <option value="qualitatif">Qualitatif</option>
                </select>
              </div>
              <div v-if="critere.type === 'quantitatif'">
                <label class="block text-xs font-medium text-gray-600 mb-1">Unité</label>
                <input
                  v-model="critere.unite"
                  type="text"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  placeholder="ex: tCO2e/an"
                  @input="emitUpdate()"
                />
              </div>
            </div>

            <!-- Quantitatif: Seuils -->
            <div v-if="critere.type === 'quantitatif' && critere.seuils" class="space-y-2">
              <label class="block text-xs font-medium text-gray-600">Seuils</label>
              <div
                v-for="niveau in ['excellent', 'bon', 'moyen', 'faible']"
                :key="niveau"
                class="flex items-center gap-2 text-sm"
              >
                <span class="w-20 capitalize text-gray-600">{{ niveau }}:</span>
                <template v-if="critere.seuils[niveau]">
                  <label class="text-xs text-gray-500">max:</label>
                  <input
                    v-model.number="critere.seuils[niveau].max"
                    type="number"
                    class="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                    @change="emitUpdate()"
                  />
                  <label class="text-xs text-gray-500">min:</label>
                  <input
                    v-model.number="critere.seuils[niveau].min"
                    type="number"
                    class="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                    @change="emitUpdate()"
                  />
                  <label class="text-xs text-gray-500">score:</label>
                  <input
                    v-model.number="critere.seuils[niveau].score"
                    type="number"
                    class="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                    @change="emitUpdate()"
                  />
                </template>
              </div>
            </div>

            <!-- Qualitatif: Options -->
            <div v-if="critere.type === 'qualitatif' && critere.options" class="space-y-2">
              <label class="block text-xs font-medium text-gray-600">Options</label>
              <div
                v-for="(opt, oi) in critere.options"
                :key="oi"
                class="flex items-center gap-2"
              >
                <input
                  v-model="opt.label"
                  type="text"
                  class="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
                  placeholder="Label de l'option"
                  @input="emitUpdate()"
                />
                <input
                  v-model.number="opt.score"
                  type="number"
                  class="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                  @change="emitUpdate()"
                />
                <button
                  @click="removeOption(critere, oi)"
                  class="text-red-500 hover:text-red-700 text-sm"
                >
                  x
                </button>
              </div>
              <button
                @click="addOption(critere)"
                class="text-sm text-emerald-700 hover:text-emerald-800"
              >
                + Option
              </button>
            </div>

            <!-- Question de collecte -->
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Question de collecte</label>
              <input
                v-model="critere.question_collecte"
                type="text"
                class="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="Question posée à l'entreprise"
                @input="emitUpdate()"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Poids total criteres -->
      <div class="bg-gray-50 px-4 py-2 text-sm flex items-center gap-2">
        <span class="text-gray-500">Somme poids critères:</span>
        <span
          :class="Math.abs(totalPoidsCriteres(pilier) - 1) < 0.01
            ? 'text-emerald-600 font-semibold'
            : 'text-red-600 font-semibold'"
        >
          {{ totalPoidsCriteres(pilier).toFixed(2) }}
        </span>
        <span v-if="Math.abs(totalPoidsCriteres(pilier) - 1) < 0.01" class="text-emerald-600">&#10003;</span>
        <span v-else class="text-red-600">&#10007; (doit être 1.00)</span>
      </div>
    </div>

    <!-- Add pilier -->
    <button
      @click="addPilier()"
      class="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-sm text-gray-500 hover:border-emerald-500 hover:text-emerald-600"
    >
      + Ajouter un pilier
    </button>

    <!-- Poids global total -->
    <div class="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm flex items-center gap-2">
      <span class="font-medium text-gray-700">Somme poids globaux:</span>
      <span
        :class="Math.abs(totalPoidsGlobal() - 1) < 0.01
          ? 'text-emerald-600 font-semibold'
          : 'text-red-600 font-semibold'"
      >
        {{ totalPoidsGlobal().toFixed(2) }}
      </span>
      <span v-if="Math.abs(totalPoidsGlobal() - 1) < 0.01" class="text-emerald-600">&#10003;</span>
      <span v-else class="text-red-600">&#10007; (doit être 1.00)</span>
    </div>
  </div>
</template>
