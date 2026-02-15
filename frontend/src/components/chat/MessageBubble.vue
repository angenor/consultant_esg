<script setup lang="ts">
import type { ChatMessage } from '../../composables/useChat'
import SkillIndicator from './SkillIndicator.vue'
import StreamingText from './StreamingText.vue'

defineProps<{
  message: ChatMessage
}>()

function handleContentClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const anchor = target.closest('a') as HTMLAnchorElement | null
  if (!anchor) return

  const href = anchor.getAttribute('href') || ''
  if (!href.includes('/api/reports/download/')) return

  event.preventDefault()
  const token = localStorage.getItem('token')
  fetch(href, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
    .then((resp) => {
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const filename = href.split('/').pop() || 'document'
      return resp.blob().then((blob) => ({ blob, filename }))
    })
    .then(({ blob, filename }) => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    })
    .catch((e) => console.error('Erreur de téléchargement:', e))
}
</script>

<template>
  <div
    class="flex"
    :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <!-- Avatar for assistant -->
    <div
      v-if="message.role === 'assistant'"
      class="mr-3 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-sm font-semibold text-white"
    >
      AI
    </div>

    <div
      :class="
        message.role === 'user'
          ? 'max-w-[75%] rounded-2xl bg-emerald-600 px-4 py-3 text-sm leading-relaxed text-white'
          : 'min-w-0 flex-1 overflow-hidden rounded-2xl bg-white px-5 py-4 text-sm leading-relaxed text-gray-800 shadow-sm ring-1 ring-gray-100'
      "
      @click="message.role === 'assistant' ? handleContentClick($event) : undefined"
    >
      <!-- Skill indicators (assistant only) -->
      <template v-if="message.role === 'assistant' && message.skills?.length">
        <SkillIndicator
          v-for="(skill, i) in message.skills"
          :key="i"
          :name="skill.name"
          :status="skill.status"
          :result="skill.result"
        />
      </template>

      <!-- Message content -->
      <StreamingText
        v-if="message.role === 'assistant'"
        :content="message.content"
        :is-streaming="message.isStreaming"
      />
      <span v-else>{{ message.content }}</span>
    </div>

    <!-- Avatar for user -->
    <div
      v-if="message.role === 'user'"
      class="ml-3 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-300 text-sm font-semibold text-gray-600"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    </div>
  </div>
</template>
