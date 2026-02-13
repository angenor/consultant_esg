import { ref } from 'vue'

export interface SkillEvent {
  name: string
  status: 'running' | 'done'
  params?: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  skills?: SkillEvent[]
  isStreaming?: boolean
}

export function useChat(conversationId: () => string | undefined) {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function sendMessage(text: string) {
    const convId = conversationId()
    if (!convId || !text.trim()) return

    error.value = null

    // Add user message
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    })

    // Prepare assistant bubble (empty, streaming)
    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      skills: [],
      isStreaming: true,
    }
    messages.value.push(assistantMsg)
    isLoading.value = true

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `/api/chat/conversations/${convId}/message`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ message: text }),
        },
      )

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEventType = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
            continue
          }

          if (line.startsWith('data: ')) {
            const raw = line.slice(6)
            if (!raw) continue

            let data: Record<string, unknown>
            try {
              data = JSON.parse(raw)
            } catch {
              continue
            }

            const eventType = (data.type as string) || currentEventType

            switch (eventType) {
              case 'text':
                assistantMsg.content += data.content as string
                break

              case 'skill_start':
                assistantMsg.skills!.push({
                  name: data.skill as string,
                  status: 'running',
                  params: data.params as Record<string, unknown> | undefined,
                })
                break

              case 'skill_result': {
                const skill = assistantMsg.skills!.find(
                  (s) => s.name === (data.skill as string) && s.status === 'running',
                )
                if (skill) skill.status = 'done'
                break
              }

              case 'done':
                assistantMsg.isStreaming = false
                isLoading.value = false
                break

              case 'error':
                assistantMsg.content += '\n\nUne erreur est survenue.'
                assistantMsg.isStreaming = false
                isLoading.value = false
                error.value = (data.content as string) || 'Erreur inconnue'
                break
            }
          }
        }
      }

      // Safety: ensure streaming ends
      if (assistantMsg.isStreaming) {
        assistantMsg.isStreaming = false
        isLoading.value = false
      }
    } catch (err) {
      assistantMsg.content += '\n\nImpossible de contacter le serveur.'
      assistantMsg.isStreaming = false
      isLoading.value = false
      error.value = err instanceof Error ? err.message : 'Erreur inconnue'
    }
  }

  async function loadHistory() {
    const convId = conversationId()
    if (!convId) return

    const token = localStorage.getItem('token')
    const response = await fetch(`/api/chat/conversations/${convId}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })

    if (!response.ok) return

    const data = await response.json()
    messages.value = (data.messages || []).map((m: Record<string, unknown>) => ({
      id: m.id as string,
      role: m.role as 'user' | 'assistant',
      content: m.content as string,
      skills: [],
      isStreaming: false,
    }))
  }

  function clearMessages() {
    messages.value = []
    error.value = null
  }

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    loadHistory,
    clearMessages,
  }
}
