<script setup lang="ts">
import { computed } from 'vue'
import { useAudioRecorder } from '../../composables/useAudioRecorder'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  audio: [blob: Blob]
}>()

const { state, error, audioLevel, elapsed, startRecording, stopRecording, cancelRecording } =
  useAudioRecorder()

const formattedTime = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

// Génère les hauteurs des barres de l'onde à partir du niveau audio
const waveBars = computed(() => {
  const count = 32
  const bars: number[] = []
  const level = audioLevel.value
  for (let i = 0; i < count; i++) {
    // Onde sinusoïdale modulée par le niveau audio
    const base = 0.15
    const wave = Math.sin((i / count) * Math.PI * 2 + elapsed.value * 2) * 0.3
    const noise = Math.sin(i * 7.3 + elapsed.value * 5) * 0.2
    bars.push(Math.max(base, Math.min(1, base + (wave + noise + 0.5) * level)))
  }
  return bars
})

async function handleStart() {
  if (props.disabled) return
  await startRecording()
}

async function handleStop() {
  const blob = await stopRecording()
  if (blob && blob.size > 0) {
    state.value = 'sending'
    emit('audio', blob)
    setTimeout(() => {
      state.value = 'idle'
    }, 500)
  }
}

function handleCancel() {
  cancelRecording()
}
</script>

<template>
  <!-- Bouton micro (état idle) -->
  <button
    v-if="state === 'idle'"
    :disabled="disabled"
    class="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl bg-gray-100 text-gray-500 transition-all hover:bg-emerald-50 hover:text-emerald-600 disabled:bg-gray-100 disabled:text-gray-300"
    title="Enregistrer un message vocal"
    @click="handleStart"
  >
    <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  </button>

  <!-- Bouton spinner (état sending) -->
  <button
    v-else-if="state === 'sending'"
    disabled
    class="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-500"
  >
    <svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10" stroke-opacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1" />
    </svg>
  </button>

  <!-- Overlay flottant d'enregistrement -->
  <Teleport to="body">
    <Transition name="recorder-overlay">
      <div
        v-if="state === 'recording'"
        class="fixed inset-0 z-[100] flex items-end justify-center"
      >
        <!-- Backdrop semi-transparent -->
        <div class="absolute inset-0 bg-black/20 backdrop-blur-[2px]" @click="handleCancel" />

        <!-- Floating panel -->
        <div class="relative z-10 mb-6 w-full max-w-lg animate-slide-up">
          <div class="mx-4 overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-black/5">
            <!-- Visualisation audio -->
            <div class="relative flex flex-col items-center px-6 pt-8 pb-4">
              <!-- Cercle pulsant autour du micro -->
              <div class="relative mb-6">
                <div
                  class="absolute inset-0 rounded-full bg-emerald-400/20 transition-transform duration-150"
                  :style="{ transform: `scale(${1.2 + audioLevel * 0.8})` }"
                />
                <div
                  class="absolute inset-0 rounded-full bg-emerald-400/10 transition-transform duration-300"
                  :style="{ transform: `scale(${1.5 + audioLevel * 1.0})` }"
                />
                <div class="relative flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30">
                  <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                </div>
              </div>

              <!-- Timer -->
              <div class="mb-4 flex items-center gap-2">
                <span class="h-2 w-2 animate-pulse rounded-full bg-red-500" />
                <span class="font-mono text-lg font-semibold text-gray-800">{{ formattedTime }}</span>
              </div>

              <!-- Barres d'ondes -->
              <div class="flex h-16 w-full items-center justify-center gap-[3px]">
                <div
                  v-for="(height, i) in waveBars"
                  :key="i"
                  class="w-[6px] rounded-full transition-all duration-100"
                  :class="audioLevel > 0.05 ? 'bg-emerald-400' : 'bg-gray-300'"
                  :style="{
                    height: `${height * 100}%`,
                    opacity: 0.4 + height * 0.6,
                  }"
                />
              </div>

              <!-- Label -->
              <p class="mt-3 text-sm text-gray-400">
                {{ audioLevel > 0.05 ? 'Écoute en cours...' : 'Parlez maintenant' }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-center gap-6 border-t border-gray-100 bg-gray-50/50 px-6 py-4">
              <!-- Annuler -->
              <button
                class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-200 text-gray-600 transition-all hover:bg-red-100 hover:text-red-500 active:scale-95"
                title="Annuler"
                @click="handleCancel"
              >
                <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>

              <!-- Envoyer -->
              <button
                class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 transition-all hover:bg-emerald-600 active:scale-95"
                title="Envoyer"
                @click="handleStop"
              >
                <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Erreur -->
  <div
    v-if="error"
    class="fixed bottom-24 left-1/2 z-[101] -translate-x-1/2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 shadow-lg ring-1 ring-red-100"
  >
    {{ error }}
  </div>
</template>

<style scoped>
@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.animate-slide-up {
  animation: slide-up 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.recorder-overlay-enter-active {
  transition: opacity 0.25s ease;
}
.recorder-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.recorder-overlay-enter-from,
.recorder-overlay-leave-to {
  opacity: 0;
}
</style>
