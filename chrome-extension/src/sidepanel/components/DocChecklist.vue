<template>
  <div class="px-4 py-4 border-t border-gray-200">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-800 flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0
                01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Documents requis
        <span class="text-xs text-gray-400">{{ readyCount }}/{{ requiredDocs.length }}</span>
      </h3>
      <button @click="$emit('refresh')" class="text-xs text-emerald-600 hover:text-emerald-700">
        Actualiser
      </button>
    </div>

    <!-- Barre de progression documents -->
    <div class="w-full bg-gray-200 rounded-full h-1.5 mb-3">
      <div class="bg-emerald-500 h-1.5 rounded-full transition-all"
           :style="{ width: `${progressPct}%` }">
      </div>
    </div>

    <div class="space-y-2">
      <DocItem
        v-for="doc in docs"
        :key="doc.name"
        :doc="doc"
        @generate="handleGenerate(doc)"
        @upload="handleUploadRedirect(doc)"
      />
    </div>

    <!-- Message si tout est pret -->
    <div v-if="readyCount === requiredDocs.length && requiredDocs.length > 0"
         class="mt-3 bg-emerald-50 rounded-lg p-3 text-center">
      <p class="text-sm text-emerald-700 font-medium">Tous les documents sont prets !</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RequiredDoc, DocumentSummary, DocWithStatus } from '@shared/types'
import { validateDocument } from '@shared/doc-validator'
import DocItem from './DocItem.vue'

const GENERATABLE_DOCS = [
  'rapport_esg',
  'fiche_entreprise',
  'bilan_carbone',
  'plan_action_esg',
]

const props = defineProps<{
  requiredDocs: RequiredDoc[]
  availableDocs: DocumentSummary[]
  entrepriseId?: string
}>()

const emit = defineEmits<{
  refresh: []
  'doc-ready-count': [count: number, total: number]
}>()

function findMatchingDoc(doc: RequiredDoc): DocumentSummary | null {
  return props.availableDocs.find(d =>
    d.nom_fichier.toLowerCase().includes(doc.type.toLowerCase()) ||
    d.type_mime?.includes(doc.format.toLowerCase())
  ) || null
}

const docs = computed<DocWithStatus[]>(() => {
  const result = props.requiredDocs.map(doc => {
    const matchedDoc = doc.available_on_platform ? null : findMatchingDoc(doc)
    const isAvailable = doc.available_on_platform || !!matchedDoc
    const validation = isAvailable ? validateDocument(doc, matchedDoc) : { valid: false, warnings: [] }

    return {
      ...doc,
      status: isAvailable ? 'ready' as const : 'missing' as const,
      can_generate: GENERATABLE_DOCS.includes(doc.type),
      warnings: isAvailable ? validation.warnings : [],
      matched_doc: matchedDoc,
    }
  })
  return result
})

const readyCount = computed(() => docs.value.filter(d => d.status === 'ready').length)

const progressPct = computed(() => {
  if (!props.requiredDocs.length) return 0
  return Math.round((readyCount.value / props.requiredDocs.length) * 100)
})

async function handleGenerate(doc: DocWithStatus) {
  // Passer en mode generating
  doc.status = 'generating'
  try {
    const { apiClient } = await import('@shared/api-client')
    await apiClient.post('/api/documents/generate', {
      type: doc.type,
      entreprise_id: props.entrepriseId,
    })
    // Demander un rafraichissement au parent
    emit('refresh')
  } catch (error) {
    doc.status = 'missing'
    console.error('Erreur generation document:', error)
  }
}

function handleUploadRedirect(doc: DocWithStatus) {
  const url = `http://localhost:5173/documents?upload=true&type=${doc.type}`
  chrome.tabs.create({ url })
}
</script>
