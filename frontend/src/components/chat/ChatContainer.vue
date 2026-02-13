<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { ChatMessage } from '../../composables/useChat'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  messages: ChatMessage[]
}>()

const scrollContainer = ref<HTMLDivElement>()

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

// Auto-scroll on new messages or content updates
watch(
  () => props.messages.length,
  () => scrollToBottom(),
)

watch(
  () => {
    const last = props.messages[props.messages.length - 1]
    return last?.content?.length ?? 0
  },
  () => scrollToBottom(),
)
</script>

<template>
  <div
    ref="scrollContainer"
    class="flex-1 overflow-y-auto px-4 py-6"
  >
    <!-- Empty state -->
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
    </div>

    <!-- Messages -->
    <div v-else class="mx-auto max-w-3xl space-y-4">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
    </div>
  </div>
</template>
