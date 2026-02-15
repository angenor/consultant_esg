<template>
  <div class="px-4 py-4 border-t border-gray-200">
    <h3 class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
      <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0
              01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Documents requis
      <span class="text-xs text-gray-400">
        {{ availableCount }}/{{ requiredDocs.length }}
      </span>
    </h3>

    <div class="space-y-2">
      <div
        v-for="doc in docsWithStatus"
        :key="doc.name"
        class="flex items-start gap-2 p-2 rounded-lg"
        :class="doc.available ? 'bg-emerald-50' : 'bg-gray-50'"
      >
        <!-- Icone statut -->
        <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
             :class="doc.available ? 'bg-emerald-500' : 'bg-gray-300'">
          <svg v-if="doc.available" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else class="w-2 h-2 bg-white rounded-full"></span>
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium" :class="doc.available ? 'text-emerald-800' : 'text-gray-700'">
              {{ doc.name }}
            </span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 text-gray-500">
              {{ doc.format }}
            </span>
          </div>
          <p class="text-[11px] text-gray-500 mt-0.5">{{ doc.description }}</p>
          <p v-if="doc.available" class="text-[11px] text-emerald-600 mt-0.5">
            Disponible sur la plateforme
          </p>
          <a v-else href="http://localhost:5173/documents" target="_blank"
             class="text-[11px] text-blue-600 hover:underline mt-0.5 inline-block">
            Telecharger sur la plateforme
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RequiredDoc, DocumentSummary } from '@shared/types'

const props = defineProps<{
  requiredDocs: RequiredDoc[]
  availableDocs: DocumentSummary[]
}>()

const docsWithStatus = computed(() =>
  props.requiredDocs.map(doc => ({
    ...doc,
    available: doc.available_on_platform ||
      props.availableDocs.some(d =>
        d.nom_fichier.toLowerCase().includes(doc.type.toLowerCase()) ||
        d.type_mime?.includes(doc.format.toLowerCase())
      ),
  }))
)

const availableCount = computed(() =>
  docsWithStatus.value.filter(d => d.available).length
)
</script>
