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
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <h4 class="mb-3 text-sm font-semibold text-gray-700">Partager mon score</h4>
    <p class="mb-4 text-xs text-gray-500">
      Générez un lien sécurisé pour partager votre score crédit vert avec un partenaire financier.
    </p>

    <div v-if="!shareUrl" class="text-center">
      <button
        class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-50"
        :disabled="generating"
        @click="generateLink"
      >
        <svg v-if="!generating" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <span v-if="generating" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        {{ generating ? 'Génération...' : 'Générer un lien de partage' }}
      </button>
    </div>

    <div v-else class="space-y-3">
      <div class="flex items-center gap-2 rounded-lg bg-gray-50 p-2">
        <input
          :value="shareUrl"
          readonly
          class="flex-1 truncate border-none bg-transparent text-xs text-gray-600 outline-none"
        />
        <button
          class="shrink-0 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-700"
          @click="copyLink"
        >
          {{ copying ? 'Copié !' : 'Copier' }}
        </button>
      </div>
      <p class="text-xs text-gray-400">Ce lien expire dans 72 heures.</p>
    </div>
  </div>
</template>
