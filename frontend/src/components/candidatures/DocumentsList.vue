<script setup lang="ts">
import type { CandidatureDocument } from '../../stores/candidatures'

defineProps<{
  documents: CandidatureDocument[]
}>()
</script>

<template>
  <div v-if="documents.length > 0" class="border rounded-lg divide-y">
    <div
      v-for="doc in documents"
      :key="doc.nom"
      class="flex items-center justify-between px-4 py-3"
    >
      <div class="min-w-0 flex-1">
        <p class="text-sm font-medium text-gray-900 truncate">{{ doc.nom }}</p>
        <p class="text-xs text-gray-500">{{ doc.date }}</p>
      </div>
      <div class="flex gap-2 ml-3 shrink-0">
        <a
          v-if="doc.url_docx"
          :href="doc.url_docx"
          target="_blank"
          class="text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline px-2 py-1 rounded bg-blue-50"
        >
          DOCX
        </a>
        <a
          v-if="doc.url_pdf"
          :href="doc.url_pdf"
          target="_blank"
          class="text-xs font-medium text-emerald-600 hover:text-emerald-700 hover:underline px-2 py-1 rounded bg-emerald-50"
        >
          PDF
        </a>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-6 text-sm text-gray-400">
    Aucun document généré pour cette candidature.
  </div>
</template>
