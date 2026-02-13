<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, upload, del } = useApi()

const loading = ref(true)
const uploading = ref(false)
const documents = ref<any[]>([])
const entrepriseId = ref<string | null>(null)

// Upload
const fileInput = ref<HTMLInputElement | null>(null)

const fileIcons: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOC',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLS',
  'image/png': 'IMG',
  'image/jpeg': 'IMG',
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' o'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko'
  return (bytes / (1024 * 1024)).toFixed(1) + ' Mo'
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function iconBg(mime: string): string {
  if (mime.includes('pdf')) return 'bg-red-100 text-red-600'
  if (mime.includes('word') || mime.includes('document')) return 'bg-blue-100 text-blue-600'
  if (mime.includes('sheet') || mime.includes('excel')) return 'bg-green-100 text-green-600'
  if (mime.includes('image')) return 'bg-purple-100 text-purple-600'
  return 'bg-gray-100 text-gray-600'
}

async function loadEntreprise() {
  try {
    const entreprises = await get<any[]>('/api/entreprises/')
    if (entreprises && entreprises.length > 0) {
      entrepriseId.value = entreprises[0].id
    }
  } catch {
    // silent
  }
}

async function loadDocuments() {
  if (!entrepriseId.value) return
  loading.value = true
  try {
    const docs = await get<any[]>(`/api/documents/entreprise/${entrepriseId.value}`)
    documents.value = docs ?? []
  } catch {
    documents.value = []
  } finally {
    loading.value = false
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !entrepriseId.value) return

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('entreprise_id', entrepriseId.value)
    await upload('/api/documents/upload', fd)
    await loadDocuments()
  } catch {
    // silent
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function deleteDocument(docId: string) {
  try {
    await del(`/api/documents/${docId}`)
    documents.value = documents.value.filter((d) => d.id !== docId)
  } catch {
    // silent
  }
}

onMounted(async () => {
  await loadEntreprise()
  await loadDocuments()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Documents</h1>
        <p class="mt-0.5 text-sm text-gray-500">Gérez les documents de votre entreprise</p>
      </div>
      <button
        class="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-50"
        :disabled="uploading || !entrepriseId"
        @click="triggerUpload"
      >
        <svg v-if="!uploading" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <div v-else class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        {{ uploading ? 'Envoi...' : 'Uploader' }}
      </button>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg"
        @change="handleFileSelected"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
    </div>

    <!-- No documents -->
    <div v-else-if="documents.length === 0" class="mx-auto max-w-md py-16 text-center">
      <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
        <svg class="h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-800">Aucun document</h2>
      <p class="mt-2 text-sm text-gray-500">
        Uploadez vos documents (rapports, bilans, certifications) pour enrichir votre analyse ESG.
      </p>
      <button
        class="mt-6 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700"
        @click="triggerUpload"
      >
        Uploader un document
      </button>
    </div>

    <!-- Documents list -->
    <div v-else class="divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white shadow-sm">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-gray-50"
      >
        <!-- Icon -->
        <div
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg text-xs font-bold"
          :class="iconBg(doc.type_mime || '')"
        >
          {{ fileIcons[doc.type_mime] || 'DOC' }}
        </div>

        <!-- Info -->
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-gray-800">{{ doc.nom_fichier }}</p>
          <div class="mt-0.5 flex items-center gap-3 text-xs text-gray-400">
            <span>{{ formatSize(doc.taille || 0) }}</span>
            <span>{{ formatDate(doc.created_at) }}</span>
            <span v-if="doc.nb_chunks" class="rounded bg-emerald-50 px-1.5 py-0.5 text-emerald-600">
              {{ doc.nb_chunks }} chunks
            </span>
          </div>
        </div>

        <!-- Delete -->
        <button
          class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
          title="Supprimer"
          @click="deleteDocument(doc.id)"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
