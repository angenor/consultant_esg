<template>
  <div class="border-t border-gray-200 bg-white">
    <!-- Toggle -->
    <button
      @click="isOpen = !isOpen"
      class="w-full px-4 py-2 flex items-center gap-2 text-sm font-medium text-gray-700
             hover:bg-gray-50 transition-colors"
    >
      <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2
              2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
      Poser une question
      <svg class="w-4 h-4 ml-auto transition-transform" :class="{ 'rotate-180': isOpen }"
           fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
      </svg>
    </button>

    <!-- Chat panel -->
    <div v-if="isOpen" class="border-t border-gray-100">
      <!-- Messages -->
      <div ref="messagesRef" class="h-48 overflow-y-auto px-4 py-3 space-y-3">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[85%] rounded-lg px-3 py-2 text-sm"
            :class="msg.role === 'user'
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-100 text-gray-800'"
          >
            {{ msg.content }}
          </div>
        </div>
        <div v-if="loading" class="flex justify-start">
          <div class="bg-gray-100 rounded-lg px-4 py-2">
            <div class="flex gap-1">
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
              <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="px-4 pb-3 flex gap-2">
        <input
          v-model="input"
          @keydown.enter="sendMessage"
          placeholder="Ex: Que mettre dans ce champ ?"
          class="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
        <button
          @click="sendMessage"
          :disabled="!input.trim() || loading"
          class="bg-emerald-600 text-white rounded-lg px-3 py-1.5
                 hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>

      <!-- Suggestions rapides -->
      <div class="px-4 pb-3 flex flex-wrap gap-1.5">
        <button
          v-for="q in quickQuestions"
          :key="q"
          @click="askQuick(q)"
          class="text-[11px] bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full
                 hover:bg-emerald-50 hover:text-emerald-700 transition-colors"
        >
          {{ q }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { FundSiteConfig } from '@shared/types'

const props = defineProps<{
  fundConfig: FundSiteConfig
  currentStep: number
}>()

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const isOpen = ref(false)
const input = ref('')
const messages = ref<ChatMessage[]>([])
const loading = ref(false)
const messagesRef = ref<HTMLElement>()

const quickQuestions = [
  'Que mettre dans ce champ ?',
  'Quels documents fournir ?',
  'Conseils pour cette etape',
]

function askQuick(q: string) {
  input.value = q
  sendMessage()
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: text,
  })
  input.value = ''
  loading.value = true

  await nextTick()
  messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'FIELD_SUGGESTION',
      payload: {
        fonds_id: props.fundConfig.fonds_id,
        field_name: 'chat',
        field_label: text,
        context: `Etape ${props.currentStep + 1}: ${props.fundConfig.steps[props.currentStep]?.title}`,
      },
    })

    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response?.suggestion || 'Desole, je n\'ai pas pu generer de reponse.',
    })
  } catch {
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Erreur de communication. Verifiez votre connexion.',
    })
  } finally {
    loading.value = false
    await nextTick()
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>
