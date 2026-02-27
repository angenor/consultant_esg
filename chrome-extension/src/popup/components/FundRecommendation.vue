<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3 space-y-2">
    <!-- Header: nom + compatibilité -->
    <div class="flex items-start gap-2">
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-medium text-gray-800 truncate">{{ fonds.nom }}</h4>
        <p class="text-xs text-gray-500">
          {{ fonds.institution }} · {{ formatMontant(fonds.montant_min, fonds.montant_max, fonds.devise) }}
        </p>
      </div>
      <!-- Score de compatibilité avec tooltip -->
      <div v-if="fonds.compatibility_score != null"
           class="shrink-0 text-right relative"
           @mouseenter="showTooltip = true"
           @mouseleave="showTooltip = false">
        <div class="text-xs font-bold cursor-help" :class="compatibilityColor">
          {{ fonds.compatibility_score }}%
        </div>
        <div class="text-[10px] text-gray-400">compatible</div>
        <!-- Tooltip explicatif -->
        <div v-if="showTooltip && fonds.compatibility_details"
             class="absolute right-0 top-full mt-1 z-50 bg-gray-800 text-white text-[10px]
                    rounded-lg p-2.5 shadow-lg w-48 leading-relaxed">
          <div class="font-medium mb-1">{{ fonds.compatibility_score }}% compatible :</div>
          <div class="space-y-0.5">
            <div :class="fonds.compatibility_details.pays_eligible ? 'text-emerald-300' : 'text-gray-400'">
              {{ fonds.compatibility_details.pays_eligible ? '✓' : '✗' }} Pays éligible
            </div>
            <div :class="fonds.compatibility_details.secteur_match ? 'text-emerald-300' : 'text-gray-400'">
              {{ fonds.compatibility_details.secteur_match ? '✓' : '✗' }} Secteur correspondant
            </div>
            <div :class="fonds.compatibility_details.score_esg_ok ? 'text-emerald-300' : 'text-gray-400'">
              {{ fonds.compatibility_details.score_esg_ok ? '✓' : '✗' }} Score ESG suffisant
            </div>
            <div :class="fonds.compatibility_details.montant_accessible ? 'text-emerald-300' : 'text-gray-400'">
              {{ fonds.compatibility_details.montant_accessible ? '✓' : '✗' }} Montant accessible
            </div>
            <div v-if="fonds.compatibility_details.bonus_date_limite" class="text-blue-300">
              + Date limite proche
            </div>
            <div v-if="fonds.compatibility_details.bonus_mode_direct" class="text-blue-300">
              + Accès direct
            </div>
            <div v-if="fonds.compatibility_details.malus_esg_trop_bas" class="text-red-300">
              − Score ESG trop éloigné
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tags: type + mode d'accès -->
    <div class="flex flex-wrap gap-1">
      <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
            :class="typeClasses">
        {{ typeLabel }}
      </span>
      <span v-if="fonds.mode_acces"
            class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium">
        {{ modeAccesLabel }}
      </span>
      <span v-if="fonds.score_esg_minimum"
            class="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600 font-medium">
        ESG min {{ fonds.score_esg_minimum }}/100
      </span>
    </div>

    <!-- Délai si disponible -->
    <p v-if="fonds.acces_details?.delai_estime"
       class="text-[10px] text-gray-400">
      Délai : {{ fonds.acces_details.delai_estime }}
      <span v-if="fonds.acces_details.periodicite"> · {{ fonds.acces_details.periodicite }}</span>
    </p>

    <!-- Actions -->
    <div class="flex gap-2">
      <button v-if="existingApplication"
        @click="$emit('resume-application', existingApplication)"
        class="flex-1 text-xs bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg
               hover:bg-blue-100 transition-colors font-medium text-center flex items-center justify-center gap-1">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Reprendre ({{ existingApplication.progress_pct }}%)
      </button>
      <button v-else
        @click="$emit('start-application', fonds)"
        class="flex-1 text-xs bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg
               hover:bg-emerald-100 transition-colors font-medium text-center">
        Postuler
      </button>
      <a v-if="fonds.url_source"
         :href="fonds.url_source"
         target="_blank"
         class="text-xs text-gray-400 hover:text-gray-600 px-2 py-1.5 rounded-lg
                hover:bg-gray-50 transition-colors flex items-center"
         title="Voir le site du fonds">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FondsVert, FundApplication } from '@shared/types'

const props = defineProps<{
  fonds: FondsVert
  existingApplication?: FundApplication | null
}>()

const showTooltip = ref(false)

defineEmits<{
  'start-application': [fonds: FondsVert]
  'resume-application': [app: FundApplication]
}>()

const compatibilityColor = computed(() => {
  const score = props.fonds.compatibility_score ?? 0
  if (score >= 70) return 'text-emerald-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-red-500'
})

const TYPE_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  pret: { bg: 'bg-blue-50', text: 'text-blue-700', label: 'Prêt' },
  subvention: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Subvention' },
  garantie: { bg: 'bg-purple-50', text: 'text-purple-700', label: 'Garantie' },
}

const typeConfig = computed(() => TYPE_CONFIG[props.fonds.type] || TYPE_CONFIG.pret)
const typeClasses = computed(() => `${typeConfig.value.bg} ${typeConfig.value.text}`)
const typeLabel = computed(() => typeConfig.value.label)

const MODE_ACCES_LABELS: Record<string, string> = {
  banque_partenaire: 'Via banque',
  appel_propositions: 'Appel à propositions',
  entite_accreditee: 'Via entité accréditée',
  direct: 'Accès direct',
  garantie_bancaire: 'Garantie bancaire',
  banque_multilaterale: 'Via banque multilatérale',
}

const modeAccesLabel = computed(() =>
  MODE_ACCES_LABELS[props.fonds.mode_acces || ''] || props.fonds.mode_acces || '',
)

function formatMontant(min: number | null, max: number | null, devise: string): string {
  const fmt = (n: number) => {
    if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}Md`
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
    return n.toString()
  }

  if (min && max) return `${fmt(min)} - ${fmt(max)} ${devise}`
  if (min) return `Min ${fmt(min)} ${devise}`
  if (max) return `Max ${fmt(max)} ${devise}`
  return devise
}
</script>
