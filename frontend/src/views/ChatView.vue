<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useEntrepriseStore } from '../stores/entreprise'
import { useChat } from '../composables/useChat'
import ChatContainer from '../components/chat/ChatContainer.vue'
import MessageInput from '../components/chat/MessageInput.vue'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const entrepriseStore = useEntrepriseStore()

// --- Entreprise creation form ---
const showCreateEntreprise = ref(false)
const newEntrepriseName = ref('')
const creatingEntreprise = ref(false)

// --- Active conversation from route ---
const activeConvId = computed(() => (route.params.conversationId as string) || null)

// --- Chat composable ---
const { messages, isLoading, sendMessage, loadHistory, clearMessages } = useChat(
  () => activeConvId.value ?? undefined,
)

// --- Load data on mount ---
onMounted(async () => {
  await entrepriseStore.loadEntreprises()
  await chatStore.loadConversations()

  // If conversation ID in route, load history
  if (activeConvId.value) {
    chatStore.setActiveConversation(activeConvId.value)
    await loadHistory()
  }
})

// --- Watch route changes for conversation switching ---
watch(
  () => route.params.conversationId,
  async (newId) => {
    if (newId) {
      chatStore.setActiveConversation(newId as string)
      clearMessages()
      await loadHistory()
    } else {
      chatStore.setActiveConversation(null)
      clearMessages()
    }
  },
)

// --- Actions ---
async function handleNewConversation() {
  const entreprise = entrepriseStore.activeEntreprise
  if (!entreprise) return

  const conv = await chatStore.createConversation(entreprise.id)
  router.push(`/chat/${conv.id}`)
}

async function handleSend(text: string) {
  // Auto-create conversation if none active
  if (!activeConvId.value) {
    const entreprise = entrepriseStore.activeEntreprise
    if (!entreprise) return
    const conv = await chatStore.createConversation(entreprise.id)
    router.push(`/chat/${conv.id}`)
    // Wait for route to update, then send
    await new Promise((r) => setTimeout(r, 50))
  }
  await sendMessage(text)
  // Refresh conversation list to update order
  chatStore.loadConversations()
}

function selectConversation(id: string) {
  router.push(`/chat/${id}`)
}

async function handleDeleteConversation(id: string) {
  await chatStore.deleteConversation(id)
  if (activeConvId.value === id) {
    router.push('/chat')
  }
}

async function handleCreateEntreprise() {
  if (!newEntrepriseName.value.trim()) return
  creatingEntreprise.value = true
  try {
    await entrepriseStore.createEntreprise({ nom: newEntrepriseName.value.trim() })
    newEntrepriseName.value = ''
    showCreateEntreprise.value = false
  } finally {
    creatingEntreprise.value = false
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "À l'instant"
  if (diffMins < 60) return `Il y a ${diffMins} min`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `Il y a ${diffHours}h`
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}
</script>

<template>
  <div class="-m-6 flex h-[calc(100vh-4rem)] overflow-hidden">
    <!-- Conversations sidebar -->
    <aside class="flex w-72 shrink-0 flex-col border-r border-gray-200 bg-white">
      <!-- Header -->
      <div class="border-b border-gray-200 p-4">
        <!-- Entreprise selector -->
        <div class="mb-3">
          <label class="mb-1 block text-xs font-medium text-gray-500">Entreprise</label>
          <div v-if="entrepriseStore.entreprises.length === 0 && !entrepriseStore.isLoading" class="text-sm text-gray-400">
            <button
              class="text-emerald-600 hover:underline"
              @click="showCreateEntreprise = true"
            >
              Créer une entreprise
            </button>
          </div>
          <select
            v-else
            :value="entrepriseStore.activeEntrepriseId"
            class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm outline-none focus:border-emerald-500"
            @change="entrepriseStore.selectEntreprise(($event.target as HTMLSelectElement).value)"
          >
            <option
              v-for="e in entrepriseStore.entreprises"
              :key="e.id"
              :value="e.id"
            >
              {{ e.nom }}
            </option>
          </select>
        </div>

        <button
          :disabled="!entrepriseStore.activeEntreprise"
          class="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:bg-gray-300"
          @click="handleNewConversation"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nouvelle conversation
        </button>
      </div>

      <!-- Conversations list -->
      <div class="flex-1 overflow-y-auto">
        <div
          v-if="chatStore.isLoadingConversations"
          class="flex items-center justify-center py-8 text-sm text-gray-400"
        >
          Chargement...
        </div>
        <div
          v-else-if="chatStore.conversations.length === 0"
          class="px-4 py-8 text-center text-sm text-gray-400"
        >
          Aucune conversation
        </div>
        <div v-else>
          <button
            v-for="conv in chatStore.conversations"
            :key="conv.id"
            class="group flex w-full items-start gap-2 border-b border-gray-100 px-4 py-3 text-left transition-colors hover:bg-gray-50"
            :class="activeConvId === conv.id ? 'bg-emerald-50' : ''"
            @click="selectConversation(conv.id)"
          >
            <div class="min-w-0 flex-1">
              <p
                class="truncate text-sm font-medium"
                :class="activeConvId === conv.id ? 'text-emerald-700' : 'text-gray-800'"
              >
                {{ conv.titre || 'Conversation' }}
              </p>
              <p class="mt-0.5 text-xs text-gray-400">
                {{ formatDate(conv.updated_at) }}
              </p>
            </div>
            <button
              class="mt-0.5 shrink-0 rounded p-1 text-gray-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
              title="Supprimer"
              @click.stop="handleDeleteConversation(conv.id)"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </button>
        </div>
      </div>
    </aside>

    <!-- Chat area -->
    <div class="flex flex-1 flex-col bg-gray-50">
      <ChatContainer :messages="messages" />
      <MessageInput :disabled="isLoading" @send="handleSend" />
    </div>

    <!-- Create entreprise modal -->
    <div
      v-if="showCreateEntreprise"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="showCreateEntreprise = false"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="text-lg font-semibold text-gray-900">Créer une entreprise</h3>
        <p class="mt-1 text-sm text-gray-500">
          Ajoutez votre entreprise pour commencer à utiliser l'advisor ESG.
        </p>
        <input
          v-model="newEntrepriseName"
          type="text"
          placeholder="Nom de l'entreprise"
          class="mt-4 w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          @keydown.enter="handleCreateEntreprise"
        />
        <div class="mt-4 flex justify-end gap-3">
          <button
            class="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
            @click="showCreateEntreprise = false"
          >
            Annuler
          </button>
          <button
            :disabled="!newEntrepriseName.trim() || creatingEntreprise"
            class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-gray-300"
            @click="handleCreateEntreprise"
          >
            Créer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
