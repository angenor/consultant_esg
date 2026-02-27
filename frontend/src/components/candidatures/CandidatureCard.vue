<script setup lang="ts">
import { useRouter } from 'vue-router'
import StatusBadge from './StatusBadge.vue'
import type { Candidature } from '../../stores/candidatures'

const props = defineProps<{
  candidature: Candidature
}>()

const router = useRouter()

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>

<template>
  <div
    class="border rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
    @click="router.push({ name: 'CandidatureDetail', params: { id: candidature.id } })"
  >
    <div class="flex justify-between items-start">
      <div class="min-w-0 flex-1">
        <h3 class="font-semibold text-gray-900 truncate">{{ candidature.fonds_nom }}</h3>
        <p class="text-sm text-gray-500">{{ candidature.fonds_institution }}</p>
        <p class="text-xs text-gray-400 mt-1">
          Démarrée le {{ formatDate(candidature.started_at) }}
        </p>
      </div>
      <StatusBadge :status="candidature.status" class="ml-3 shrink-0" />
    </div>

    <!-- Barre de progression -->
    <div class="mt-3">
      <div class="flex justify-between text-xs text-gray-500 mb-1">
        <span v-if="candidature.total_steps">
          {{ candidature.current_step }}/{{ candidature.total_steps }} étapes
        </span>
        <span v-else>Progression</span>
        <span>{{ Math.round(candidature.progress_pct) }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="h-2 rounded-full transition-all duration-500"
          :class="candidature.progress_pct >= 100 ? 'bg-emerald-500' : 'bg-blue-500'"
          :style="{ width: candidature.progress_pct + '%' }"
        />
      </div>
    </div>

    <!-- Prochaine étape -->
    <p v-if="candidature.next_step" class="mt-2 text-xs text-gray-600">
      Prochaine étape : <span class="font-medium">{{ candidature.next_step }}</span>
    </p>

    <!-- Documents count -->
    <p v-if="candidature.documents_count > 0" class="mt-1 text-xs text-gray-400">
      {{ candidature.documents_count }} document{{ candidature.documents_count > 1 ? 's' : '' }} générés
    </p>
  </div>
</template>
