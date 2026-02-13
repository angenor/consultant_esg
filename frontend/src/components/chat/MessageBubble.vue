<script setup lang="ts">
import type { ChatMessage } from '../../composables/useChat'
import SkillIndicator from './SkillIndicator.vue'
import StreamingText from './StreamingText.vue'

defineProps<{
  message: ChatMessage
}>()
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
      class="max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
      :class="
        message.role === 'user'
          ? 'bg-emerald-600 text-white'
          : 'bg-white text-gray-800 shadow-sm ring-1 ring-gray-100'
      "
    >
      <!-- Skill indicators (assistant only) -->
      <template v-if="message.role === 'assistant' && message.skills?.length">
        <SkillIndicator
          v-for="(skill, i) in message.skills"
          :key="i"
          :name="skill.name"
          :status="skill.status"
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
