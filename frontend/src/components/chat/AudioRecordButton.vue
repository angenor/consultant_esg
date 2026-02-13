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

// Barres disposées en cercle — hauteurs modulées par le volume
const circularBars = computed(() => {
  const count = 40
  const bars: { rotation: number; height: number }[] = []
  const level = audioLevel.value
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * 360
    const base = 0.2
    const wave = Math.sin((i / count) * Math.PI * 4 + elapsed.value * 3) * 0.3
    const noise = Math.sin(i * 5.7 + elapsed.value * 6) * 0.15
    const h = Math.max(base, Math.min(1, base + (wave + noise + 0.5) * level))
    bars.push({ rotation: angle, height: h })
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

  <!-- Overlay flottant circulaire -->
  <Teleport to="body">
    <Transition name="recorder-overlay">
      <div
        v-if="state === 'recording'"
        class="fixed inset-0 z-[100] flex items-center justify-center"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="handleCancel" />

        <!-- Widget circulaire -->
        <div class="relative z-10 animate-pop-in">
          <!-- Anneaux pulsants extérieurs -->
          <div
            class="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400/5 transition-transform duration-300"
            :style="{ transform: `translate(-50%, -50%) scale(${1.1 + audioLevel * 0.4})` }"
          />
          <div
            class="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400/10 transition-transform duration-200"
            :style="{ transform: `translate(-50%, -50%) scale(${1.05 + audioLevel * 0.3})` }"
          />

          <!-- Cercle principal -->
          <div class="relative flex h-56 w-56 flex-col items-center justify-center rounded-full bg-white shadow-2xl ring-1 ring-black/5">

            <!-- Barres radiales autour du cercle -->
            <div class="absolute inset-0">
              <div
                v-for="(bar, i) in circularBars"
                :key="i"
                class="absolute left-1/2 top-0 origin-bottom"
                :style="{
                  height: '50%',
                  transform: `translateX(-50%) rotate(${bar.rotation}deg)`,
                }"
              >
                <div
                  class="mx-auto w-0.75 rounded-full transition-all duration-100"
                  :class="audioLevel > 0.05 ? 'bg-emerald-400' : 'bg-gray-300'"
                  :style="{
                    height: `${8 + bar.height * 20}px`,
                    opacity: 0.3 + bar.height * 0.7,
                  }"
                />
              </div>
            </div>

            <!-- Contenu central -->
            <div class="relative z-10 flex flex-col items-center">
              <!-- Icône micro -->
              <div class="mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/25">
                <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </div>

              <!-- Timer -->
              <div class="flex items-center gap-1.5">
                <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
                <span class="font-mono text-sm font-semibold text-gray-700">{{ formattedTime }}</span>
              </div>

              <!-- Label -->
              <p class="mt-1 text-[11px] text-gray-400">
                {{ audioLevel > 0.05 ? 'Écoute...' : 'Parlez' }}
              </p>
            </div>
          </div>

          <!-- Boutons d'action sous le cercle -->
          <div class="mt-5 flex items-center justify-center gap-8">
            <!-- Annuler -->
            <button
              class="flex h-12 w-12 items-center justify-center rounded-full bg-white text-gray-500 shadow-lg ring-1 ring-black/5 transition-all hover:bg-red-50 hover:text-red-500 active:scale-90"
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
              class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 transition-all hover:bg-emerald-600 active:scale-90"
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
@keyframes pop-in {
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  70% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-pop-in {
  animation: pop-in 0.4s cubic-bezier(0.16, 1, 0.3, 1);
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
