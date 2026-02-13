<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    language?: 'python' | 'json'
    height?: number
    placeholder?: string
    readonly?: boolean
  }>(),
  {
    language: 'python',
    height: 300,
    placeholder: '',
    readonly: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Tab') {
    event.preventDefault()
    const textarea = textareaRef.value
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = textarea.value
    const newValue = value.substring(0, start) + '    ' + value.substring(end)
    emit('update:modelValue', newValue)

    // Restore cursor position
    requestAnimationFrame(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 4
    })
  }
}
</script>

<template>
  <div class="relative border border-gray-300 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-emerald-500">
    <!-- Language indicator -->
    <div class="absolute top-2 right-2 z-10">
      <span class="px-2 py-0.5 text-xs font-mono rounded bg-gray-700 text-gray-300">
        {{ language }}
      </span>
    </div>

    <textarea
      ref="textareaRef"
      :value="modelValue"
      @input="handleInput"
      @keydown="handleKeydown"
      :placeholder="placeholder"
      :readonly="readonly"
      :style="{ height: height + 'px' }"
      class="w-full p-4 font-mono text-sm bg-gray-900 text-gray-100 resize-y focus:outline-none"
      spellcheck="false"
    />
  </div>
</template>
