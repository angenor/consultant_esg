<script setup lang="ts">
import { ref } from 'vue'
import { useApi } from '../../composables/useApi'

const props = defineProps<{
  entrepriseId: string
}>()

const { post } = useApi()
const shareUrl = ref('')
const copying = ref(false)
const generating = ref(false)

async function generateLink() {
  generating.value = true
  try {
    const data = await post<{ share_url: string }>(`/api/credit-score/entreprise/${props.entrepriseId}/share`, {
      expires_hours: 72,
    })
    shareUrl.value = window.location.origin + data.share_url
  } catch {
    // silent
  } finally {
    generating.value = false
  }
}

async function copyLink() {
  if (!shareUrl.value) return
  await navigator.clipboard.writeText(shareUrl.value)
  copying.value = true
  setTimeout(() => (copying.value = false), 2000)
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
    <div class="flex items-start gap-4">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-50">
        <svg class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
        </svg>
      </div>
      <div class="min-w-0 flex-1">
        <h4 class="text-sm font-semibold text-gray-900">Partager mon score</h4>
        <p class="mt-1 text-xs leading-relaxed text-gray-500">
          Générez un lien sécurisé pour partager votre score crédit vert avec un partenaire financier.
        </p>
      </div>
    </div>

    <div v-if="!shareUrl" class="mt-5">
      <button
        class="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 px-4 py-3 text-sm font-medium text-gray-600 transition-all hover:border-emerald-300 hover:bg-emerald-50/50 hover:text-emerald-700 disabled:opacity-50"
        :disabled="generating"
        @click="generateLink"
      >
        <svg v-if="!generating" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <span v-if="generating" class="h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
        {{ generating ? 'Génération...' : 'Générer un lien de partage' }}
      </button>
    </div>

    <div v-else class="mt-5 space-y-3">
      <div class="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 p-2.5">
        <svg class="h-4 w-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <input
          :value="shareUrl"
          readonly
          class="min-w-0 flex-1 truncate border-none bg-transparent text-xs text-gray-600 outline-none"
        />
        <button
          class="shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all"
          :class="copying ? 'bg-emerald-100 text-emerald-700' : 'bg-emerald-600 text-white hover:bg-emerald-700'"
          @click="copyLink"
        >
          {{ copying ? 'Copié !' : 'Copier' }}
        </button>
      </div>
      <div class="flex items-center gap-1.5 text-xs text-gray-400">
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Ce lien expire dans 72 heures
      </div>
    </div>
  </div>
</template>
