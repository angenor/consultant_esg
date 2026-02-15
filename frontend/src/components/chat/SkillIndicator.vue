<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  status: 'running' | 'done'
  result?: Record<string, unknown>
}>()

const skillLabels: Record<string, { running: string; done: string }> = {
  get_company_profile: { running: 'Chargement du profil...', done: 'Profil chargé' },
  update_company_profile: { running: 'Mise à jour du profil...', done: 'Profil mis à jour' },
  list_referentiels: { running: 'Chargement des référentiels...', done: 'Référentiels chargés' },
  analyze_document: { running: 'Analyse du document...', done: 'Document analysé' },
  calculate_esg_score: { running: 'Calcul du score ESG...', done: 'Score ESG calculé' },
  search_green_funds: { running: 'Recherche de fonds verts...', done: 'Fonds verts trouvés' },
  calculate_carbon: { running: "Calcul de l'empreinte carbone...", done: 'Empreinte calculée' },
  generate_report_section: { running: 'Génération de la section...', done: 'Section générée' },
  assemble_pdf: { running: 'Génération du rapport PDF...', done: 'Rapport PDF généré' },
  search_knowledge_base: { running: 'Recherche dans la base...', done: 'Recherche terminée' },
  manage_action_plan: { running: "Création du plan d'action...", done: "Plan d'action créé" },
  generate_reduction_plan: { running: 'Génération du plan carbone...', done: 'Plan carbone généré' },
  calculate_credit_score: { running: 'Calcul du score crédit...', done: 'Score crédit calculé' },
  get_action_plans: { running: "Chargement des plans d'action...", done: "Plans d'action chargés" },
  simulate_funding: { running: 'Simulation du financement...', done: 'Simulation terminée' },
  get_sector_benchmark: { running: 'Chargement du benchmark...', done: 'Benchmark chargé' },
}

const label = computed(() => {
  const labels = skillLabels[props.name]
  if (!labels) {
    return props.status === 'running' ? `${props.name} en cours...` : `${props.name} terminé`
  }
  return labels[props.status]
})

const downloadUrl = computed(() => {
  if (props.status !== 'done' || !props.result) return null
  const url = props.result.download_url as string | undefined
  return url || null
})

const downloadLabel = computed(() => {
  if (!props.result) return ''
  const msg = props.result.message as string | undefined
  return msg || 'Télécharger le PDF'
})

const fileSizeKb = computed(() => {
  if (!props.result) return null
  return props.result.size_kb as number | undefined
})
</script>

<template>
  <div class="my-1.5">
    <div class="flex items-center gap-2 text-sm">
      <!-- Spinner if running -->
      <svg
        v-if="status === 'running'"
        class="h-4 w-4 animate-spin text-emerald-500"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <!-- Check if done -->
      <svg
        v-else
        class="h-4 w-4 text-emerald-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20 6 9 17 4 12" />
      </svg>

      <span :class="status === 'running' ? 'text-gray-500' : 'text-gray-400'">
        {{ label }}
      </span>
    </div>

    <!-- Download button for PDF results -->
    <a
      v-if="downloadUrl"
      :href="downloadUrl"
      target="_blank"
      class="mt-2 inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      {{ downloadLabel }}
      <span v-if="fileSizeKb" class="text-xs text-emerald-500">({{ fileSizeKb }} Ko)</span>
    </a>
  </div>
</template>
