import { ref } from 'vue'
import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

export interface Conversation {
  id: string
  entreprise_id: string
  titre: string | null
  created_at: string
  updated_at: string
}

export const useChatStore = defineStore('chat', () => {
  const { get, post, del } = useApi()

  // --------------- State ---------------
  const conversations = ref<Conversation[]>([])
  const activeConversationId = ref<string | null>(null)
  const isLoadingConversations = ref(false)

  // --------------- Actions ---------------
  async function loadConversations() {
    isLoadingConversations.value = true
    try {
      conversations.value = await get<Conversation[]>('/api/chat/conversations')
    } finally {
      isLoadingConversations.value = false
    }
  }

  async function createConversation(entrepriseId: string, titre?: string): Promise<Conversation> {
    const conv = await post<Conversation>('/api/chat/conversations', {
      entreprise_id: entrepriseId,
      titre,
    })
    conversations.value.unshift(conv)
    activeConversationId.value = conv.id
    return conv
  }

  async function deleteConversation(id: string) {
    await del<void>(`/api/chat/conversations/${id}`)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (activeConversationId.value === id) {
      activeConversationId.value = null
    }
  }

  function setActiveConversation(id: string | null) {
    activeConversationId.value = id
  }

  return {
    conversations,
    activeConversationId,
    isLoadingConversations,
    loadConversations,
    createConversation,
    deleteConversation,
    setActiveConversation,
  }
})
