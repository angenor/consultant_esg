<script setup lang="ts">
export interface ReferentielOption {
  id: string
  nom: string
  code: string
  institution: string | null
}

const props = defineProps<{
  referentiels: ReferentielOption[]
  modelValue: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [code: string | null]
}>()

function onChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  emit('update:modelValue', val || null)
}
</script>

<template>
  <div class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-sm">
    <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
    <select
      :value="modelValue ?? ''"
      class="appearance-none border-none bg-transparent pr-6 text-sm font-medium text-gray-700 outline-none"
      @change="onChange"
    >
      <option value="">Tous les référentiels</option>
      <option v-for="r in referentiels" :key="r.code" :value="r.code">
        {{ r.nom }}
      </option>
    </select>
  </div>
</template>
