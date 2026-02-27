<template>
  <div class="px-4 py-3 bg-blue-50 border-b border-blue-100">
    <div class="flex items-center gap-2 mb-2">
      <span class="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-medium">
        {{ modeLabel }}
      </span>
      <span class="text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
        Intermédiaire requis
      </span>
    </div>

    <!-- Phases du parcours -->
    <div class="space-y-2">
      <!-- Phase 1 : Contact intermédiaire -->
      <div class="flex items-start gap-2">
        <div class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
             :class="phase >= 1 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'">
          1
        </div>
        <div>
          <p class="text-xs font-medium" :class="phase >= 1 ? 'text-blue-700' : 'text-gray-400'">
            Identification & contact intermédiaire
          </p>
          <p v-if="phase === 0" class="text-[10px] text-gray-400">En attente</p>
          <p v-else-if="phase === 1" class="text-[10px] text-blue-500">En cours</p>
          <p v-else class="text-[10px] text-emerald-500">Complété</p>
        </div>
      </div>

      <!-- Phase 2 : Préparation dossier -->
      <div class="flex items-start gap-2">
        <div class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
             :class="phase >= 2 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'">
          2
        </div>
        <div>
          <p class="text-xs font-medium" :class="phase >= 2 ? 'text-blue-700' : 'text-gray-400'">
            Préparation du dossier
          </p>
          <p v-if="phase < 2" class="text-[10px] text-gray-400">En attente</p>
          <p v-else-if="phase === 2" class="text-[10px] text-blue-500">En cours</p>
          <p v-else class="text-[10px] text-emerald-500">Complété</p>
        </div>
      </div>

      <!-- Phase 3 : Soumission -->
      <div class="flex items-start gap-2">
        <div class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
             :class="phase >= 3 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'">
          3
        </div>
        <div>
          <p class="text-xs font-medium" :class="phase >= 3 ? 'text-blue-700' : 'text-gray-400'">
            Soumission via l'intermédiaire
          </p>
          <p v-if="phase < 3" class="text-[10px] text-gray-400">En attente</p>
          <p v-else class="text-[10px] text-blue-500">En cours</p>
        </div>
      </div>
    </div>

    <!-- Intermédiaires disponibles -->
    <div v-if="intermediaires.length > 0" class="mt-3 bg-white rounded-lg p-2">
      <p class="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Contacts</p>
      <div v-for="inter in intermediaires" :key="inter.nom" class="text-xs text-gray-600 py-0.5">
        <span class="font-medium">{{ inter.nom }}</span>
        <span class="text-gray-400"> · {{ inter.type }}</span>
        <a v-if="inter.contact" :href="inter.contact" target="_blank"
           class="text-blue-500 hover:underline ml-1">Contact</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modeAcces: string
  preStepCompleted: boolean[]
  currentStep: number
  totalSteps: number
  intermediaires?: { nom: string; type: string; pays: string; contact: string | null }[]
}>()

const MODE_LABELS: Record<string, string> = {
  banque_partenaire: 'Via banque partenaire',
  entite_accreditee: 'Via entité accréditée',
  garantie_bancaire: 'Garantie bancaire',
  banque_multilaterale: 'Via banque multilatérale',
}

const modeLabel = computed(() => MODE_LABELS[props.modeAcces] || props.modeAcces)

const intermediaires = computed(() => props.intermediaires || [])

// Phase courante basée sur la progression des pré-étapes et étapes
const phase = computed(() => {
  const allPreDone = props.preStepCompleted.length > 0 && props.preStepCompleted.every(Boolean)
  if (!allPreDone) return 1
  if (props.currentStep < props.totalSteps - 1) return 2
  return 3
})
</script>
