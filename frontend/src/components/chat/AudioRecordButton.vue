<script setup lang="ts">
import { useAudioRecorder } from '../../composables/useAudioRecorder'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  audio: [blob: Blob]
}>()

const { state, error, startRecording, stopRecording, cancelRecording } = useAudioRecorder()

async function handleClick() {
  if (props.disabled) return

  if (state.value === 'idle') {
    await startRecording()
  } else if (state.value === 'recording') {
    const blob = await stopRecording()
    if (blob && blob.size > 0) {
      state.value = 'sending'
      emit('audio', blob)
      // Le parent remettra à idle via le prop disabled / fin du loading
      // On remet manuellement après un tick pour que l'UI reflète l'envoi
      setTimeout(() => {
        state.value = 'idle'
      }, 500)
    }
  }
}

function handleCancel(e: Event) {
  e.stopPropagation()
  cancelRecording()
}
</script>

<template>
  <div class="relative">
    <!-- Bouton micro principal -->
    <button
      :disabled="disabled && state === 'idle'"
      class="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl transition-all"
      :class="{
        'bg-gray-100 text-gray-500 hover:bg-gray-200': state === 'idle' && !disabled,
        'bg-red-500 text-white animate-pulse': state === 'recording',
        'bg-gray-300 text-gray-400': state === 'sending' || (state === 'idle' && disabled),
      }"
      :title="
        state === 'idle' ? 'Enregistrer un message vocal' :
        state === 'recording' ? 'Arrêter l\'enregistrement' :
        'Envoi en cours...'
      "
      @click="handleClick"
    >
      <!-- Icône micro (idle) -->
      <svg
        v-if="state === 'idle'"
        class="h-5 w-5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>

      <!-- Icône stop (recording) -->
      <svg
        v-else-if="state === 'recording'"
        class="h-5 w-5"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <rect x="6" y="6" width="12" height="12" rx="2" />
      </svg>

      <!-- Icône spinner (sending) -->
      <svg
        v-else
        class="h-5 w-5 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25" />
        <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1" />
      </svg>
    </button>

    <!-- Bouton annuler (visible pendant l'enregistrement) -->
    <button
      v-if="state === 'recording'"
      class="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-gray-600 text-white shadow-sm"
      title="Annuler"
      @click="handleCancel"
    >
      <svg class="h-2.5 w-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>

    <!-- Message d'erreur -->
    <div
      v-if="error"
      class="absolute bottom-full right-0 mb-2 w-64 rounded-lg bg-red-50 p-2 text-xs text-red-600 shadow-lg"
    >
      {{ error }}
    </div>
  </div>
</template>
