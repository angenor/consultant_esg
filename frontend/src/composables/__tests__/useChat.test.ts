import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useChat } from '../useChat'

// Mock crypto.randomUUID for deterministic IDs
let uuidCounter = 0
vi.stubGlobal('crypto', {
  randomUUID: () => `uuid-${++uuidCounter}`,
})

describe('useChat', () => {
  beforeEach(() => {
    uuidCounter = 0
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('clearMessages resets state', () => {
    const { messages, error, clearMessages } = useChat(() => 'conv-1')

    // Add some messages manually
    messages.value.push({
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
    })
    messages.value.push({
      id: 'msg-2',
      role: 'assistant',
      content: 'Hi there',
    })
    error.value = 'Some error'

    expect(messages.value).toHaveLength(2)
    expect(error.value).toBe('Some error')

    clearMessages()

    expect(messages.value).toHaveLength(0)
    expect(error.value).toBeNull()
  })

  it('sendMessage adds user message and assistant placeholder', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('event: done\ndata: {"type":"done"}\n\n'),
        )
        controller.close()
      },
    })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    })

    localStorage.setItem('token', 'test-token')

    const { messages, sendMessage } = useChat(() => 'conv-1')

    await sendMessage('Hello ESG')

    expect(messages.value).toHaveLength(2)

    // First message is the user message
    expect(messages.value[0].role).toBe('user')
    expect(messages.value[0].content).toBe('Hello ESG')

    // Second message is the assistant placeholder
    expect(messages.value[1].role).toBe('assistant')
    expect(messages.value[1].isStreaming).toBe(false) // done event sets it to false
  })
})
