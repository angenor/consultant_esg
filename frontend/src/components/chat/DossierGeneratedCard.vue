<script setup lang="ts">
import { ref } from 'vue'

interface DocInfo {
  type: string
  nom: string
  label: string
  format: string
  taille: number
  url_telechargement: string
}

interface DocManquant {
  nom: string
  note: string
}

const props = defineProps<{
  result: {
    dossier_id?: string
    reference?: string
    type_dossier?: string
    fonds?: string
    fonds_institution?: string
    intermediaire?: string | null
    documents_generes?: DocInfo[]
    documents_en_erreur?: { type: string; format: string; erreur: string }[] | null
    documents_manquants?: DocManquant[] | null
    zip_url?: string | null
    prochaine_etape?: string
    nb_documents?: number
  }
}>()

const downloading = ref<string | null>(null)

async function handleDownload(url: string, filename: string) {
  downloading.value = filename
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
  } catch (e) {
    console.error('Erreur de téléchargement:', e)
  } finally {
    downloading.value = null
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  return `${Math.round(bytes / 1024)} Ko`
}
</script>

<template>
  <div class="mt-3 overflow-hidden rounded-xl border border-emerald-200 bg-emerald-50/50">
    <!-- Header -->
    <div class="border-b border-emerald-200 bg-emerald-600 px-4 py-3 text-white">
      <div class="flex items-center gap-2">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <div>
          <h3 class="font-semibold">Dossier de candidature — {{ result.fonds }}</h3>
          <p v-if="result.intermediaire" class="text-sm text-emerald-100">
            Via {{ result.intermediaire }}
          </p>
        </div>
      </div>
      <div v-if="result.reference" class="mt-1 text-xs text-emerald-200">
        Réf. {{ result.reference }}
        <span v-if="result.type_dossier === 'template_vierge'" class="ml-2 rounded bg-emerald-700 px-1.5 py-0.5">
          Template vierge
        </span>
      </div>
    </div>

    <!-- Documents list -->
    <div class="divide-y divide-emerald-100">
      <div
        v-for="doc in result.documents_generes"
        :key="doc.nom"
        class="flex items-center justify-between px-4 py-2.5 transition-colors hover:bg-emerald-50"
      >
        <div class="flex items-center gap-2">
          <svg class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="text-sm text-gray-700">{{ doc.label }}</span>
          <span class="text-xs text-gray-400">{{ formatSize(doc.taille) }}</span>
        </div>
        <button
          :disabled="downloading === doc.nom"
          class="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-white px-2.5 py-1 text-xs font-medium text-emerald-600 transition-colors hover:bg-emerald-50 disabled:opacity-50"
          @click="handleDownload(doc.url_telechargement, doc.nom)"
        >
          <svg v-if="downloading === doc.nom" class="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span class="uppercase">{{ doc.format }}</span>
        </button>
      </div>
    </div>

    <!-- Documents manquants -->
    <div v-if="result.documents_manquants?.length" class="border-t border-amber-200 bg-amber-50 px-4 py-3">
      <p class="mb-1 text-xs font-semibold text-amber-700">Documents à fournir :</p>
      <ul class="space-y-1">
        <li v-for="doc in result.documents_manquants" :key="doc.nom" class="flex items-start gap-1.5 text-xs text-amber-600">
          <svg class="mt-0.5 h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span><strong>{{ doc.nom }}</strong> — {{ doc.note }}</span>
        </li>
      </ul>
    </div>

    <!-- ZIP download + prochaine étape -->
    <div class="border-t border-emerald-200 bg-white px-4 py-3">
      <button
        v-if="result.zip_url"
        :disabled="downloading === 'zip'"
        class="mb-2 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
        @click="handleDownload(result.zip_url!, 'dossier.zip')"
      >
        <svg v-if="downloading === 'zip'" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        {{ downloading === 'zip' ? 'Téléchargement...' : 'Télécharger le dossier complet (ZIP)' }}
      </button>

      <p v-if="result.prochaine_etape" class="text-xs text-gray-500">
        <strong>Prochaine étape :</strong> {{ result.prochaine_etape }}
      </p>
    </div>
  </div>
</template>
