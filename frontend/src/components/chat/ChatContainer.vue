<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
import type { ChatMessage } from '../../composables/useChat'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  messages: ChatMessage[]
}>()

const emit = defineEmits<{
  suggest: [text: string]
}>()

const scrollContainer = ref<HTMLDivElement>()
const isNearBottom = ref(true)
const showScrollButton = ref(false)

const suggestions = [
  'Calculer mon score ESG',
  'Mon empreinte carbone',
  'Trouver des fonds verts',
  'Profil de mon entreprise',
]

// Typing indicator: last message is assistant, streaming, and empty content
const showTyping = computed(() => {
  const last = props.messages[props.messages.length - 1]
  return last?.role === 'assistant' && last.isStreaming && !last.content
})

function checkNearBottom() {
  if (!scrollContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
  isNearBottom.value = scrollHeight - scrollTop - clientHeight < 100
  showScrollButton.value = !isNearBottom.value
}

function scrollToBottom(force = false) {
  nextTick(() => {
    if (scrollContainer.value && (isNearBottom.value || force)) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
      showScrollButton.value = false
    }
  })
}

// Auto-scroll on new messages
watch(
  () => props.messages.length,
  () => scrollToBottom(),
)

// Auto-scroll during streaming (if near bottom)
watch(
  () => {
    const last = props.messages[props.messages.length - 1]
    return last?.content?.length ?? 0
  },
  () => scrollToBottom(),
)

onMounted(() => {
  scrollContainer.value?.addEventListener('scroll', checkNearBottom, { passive: true })
})

onUnmounted(() => {
  scrollContainer.value?.removeEventListener('scroll', checkNearBottom)
})
</script>

<template>
  <div
    ref="scrollContainer"
    class="relative flex-1 overflow-y-auto px-6 py-6"
  >
    <!-- Empty state with suggestions -->
    <div
      v-if="messages.length === 0"
      class="flex h-full flex-col items-center justify-center text-center"
    >
      <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100">
        <svg class="h-8 w-8 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </div>
      <h3 class="text-lg font-semibold text-gray-900">ESG Advisor</h3>
      <p class="mt-1 max-w-sm text-sm text-gray-500">
        Posez vos questions sur l'ESG, la finance durable, ou le profil de votre entreprise.
      </p>
      <div class="mt-6 flex flex-wrap justify-center gap-2">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="rounded-full border border-emerald-200 bg-white px-4 py-2 text-sm text-emerald-700 transition-colors hover:bg-emerald-50 hover:border-emerald-300"
          @click="emit('suggest', suggestion)"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div v-else class="space-y-4">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />

      <!-- Typing indicator -->
      <div v-if="showTyping" class="flex items-start gap-3">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100">
          <svg class="h-4 w-4 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <div class="rounded-2xl rounded-tl-sm bg-white px-4 py-3 shadow-sm">
          <div class="flex items-center gap-1">
            <span class="typing-dot h-2 w-2 rounded-full bg-gray-400" />
            <span class="typing-dot h-2 w-2 rounded-full bg-gray-400" style="animation-delay: 0.15s" />
            <span class="typing-dot h-2 w-2 rounded-full bg-gray-400" style="animation-delay: 0.3s" />
          </div>
        </div>
      </div>
    </div>

    <!-- Scroll to bottom button -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <button
        v-if="showScrollButton"
        class="absolute bottom-4 right-6 flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-lg border border-gray-200 text-gray-500 hover:text-emerald-600 hover:border-emerald-300 transition-colors"
        @click="scrollToBottom(true)"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}
.typing-dot {
  animation: typingBounce 1.2s infinite;
}
</style>
