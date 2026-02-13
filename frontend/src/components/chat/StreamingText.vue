<script setup lang="ts">
import MarkdownViewer from './MarkdownViewer.vue'

defineProps<{
  content: string
  isStreaming?: boolean
}>()
</script>

<template>
  <MarkdownViewer :content="content" :is-streaming="isStreaming" />
</template>
