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
  <div class="flex items-center gap-3">
    <label class="text-sm font-medium text-gray-600">Référentiel :</label>
    <select
      :value="modelValue ?? ''"
      class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
      @change="onChange"
    >
      <option value="">Tous les référentiels</option>
      <option v-for="r in referentiels" :key="r.code" :value="r.code">
        {{ r.nom }}
      </option>
    </select>
  </div>
</template>
