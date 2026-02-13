<script setup lang="ts">
defineProps<{
  content: string
  isStreaming?: boolean
}>()
</script>

<template>
  <div class="whitespace-pre-wrap break-words">
    {{ content }}<span
      v-if="isStreaming"
      class="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-gray-400"
    />
  </div>
</template>
