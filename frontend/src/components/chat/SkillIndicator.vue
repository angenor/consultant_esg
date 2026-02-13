<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  status: 'running' | 'done'
}>()

const skillLabels: Record<string, { running: string; done: string }> = {
  get_company_profile: { running: 'Chargement du profil...', done: 'Profil chargé' },
  update_company_profile: { running: 'Mise à jour du profil...', done: 'Profil mis à jour' },
  list_referentiels: { running: 'Chargement des référentiels...', done: 'Référentiels chargés' },
  analyze_document: { running: 'Analyse du document...', done: 'Document analysé' },
  calculate_esg_score: { running: 'Calcul du score ESG...', done: 'Score ESG calculé' },
  search_green_funds: { running: 'Recherche de fonds verts...', done: 'Fonds verts trouvés' },
  calculate_carbon: { running: "Calcul de l'empreinte carbone...", done: 'Empreinte calculée' },
  generate_report_section: { running: 'Génération du rapport...', done: 'Section générée' },
  search_knowledge_base: { running: 'Recherche dans la base...', done: 'Recherche terminée' },
}

const label = computed(() => {
  const labels = skillLabels[props.name]
  if (!labels) {
    return props.status === 'running' ? `${props.name} en cours...` : `${props.name} terminé`
  }
  return labels[props.status]
})
</script>

<template>
  <div class="my-1.5 flex items-center gap-2 text-sm">
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
</template>
