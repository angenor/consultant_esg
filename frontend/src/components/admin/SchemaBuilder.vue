<script setup lang="ts">
import { ref, watch } from 'vue'

interface SchemaProperty {
  name: string
  type: string
  description: string
  required: boolean
  enumValues: string
}

const props = defineProps<{
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

const properties = ref<SchemaProperty[]>([])

// Parse initial schema into properties
function parseSchema(schema: Record<string, unknown>) {
  const props = (schema.properties || {}) as Record<string, Record<string, unknown>>
  const required = (schema.required || []) as string[]

  return Object.entries(props).map(([name, prop]) => ({
    name,
    type: (prop.type as string) || 'string',
    description: (prop.description as string) || '',
    required: required.includes(name),
    enumValues: Array.isArray(prop.enum) ? prop.enum.join(', ') : '',
  }))
}

// Watch for external changes
watch(
  () => props.modelValue,
  (schema) => {
    if (schema && typeof schema === 'object') {
      properties.value = parseSchema(schema)
    }
  },
  { immediate: true },
)

function buildSchema(): Record<string, unknown> {
  const schemaProps: Record<string, Record<string, unknown>> = {}
  const required: string[] = []

  for (const prop of properties.value) {
    if (!prop.name) continue
    const schemaProp: Record<string, unknown> = {
      type: prop.type,
    }
    if (prop.description) schemaProp.description = prop.description
    if (prop.enumValues) {
      schemaProp.enum = prop.enumValues.split(',').map((v) => v.trim()).filter(Boolean)
    }
    schemaProps[prop.name] = schemaProp
    if (prop.required) required.push(prop.name)
  }

  return {
    type: 'object',
    properties: schemaProps,
    ...(required.length > 0 ? { required } : {}),
  }
}

function emitUpdate() {
  emit('update:modelValue', buildSchema())
}

function addProperty() {
  properties.value.push({
    name: '',
    type: 'string',
    description: '',
    required: false,
    enumValues: '',
  })
}

function removeProperty(index: number) {
  properties.value.splice(index, 1)
  emitUpdate()
}

const types = ['string', 'number', 'integer', 'boolean', 'object', 'array']
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="(prop, index) in properties"
      :key="index"
      class="border border-gray-200 rounded-lg p-3 bg-white"
    >
      <div class="grid grid-cols-12 gap-2 items-start">
        <div class="col-span-3">
          <label class="block text-xs text-gray-500 mb-1">Nom</label>
          <input
            v-model="prop.name"
            @change="emitUpdate"
            type="text"
            placeholder="param_name"
            class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm font-mono focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-gray-500 mb-1">Type</label>
          <select
            v-model="prop.type"
            @change="emitUpdate"
            class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-1 focus:ring-emerald-500"
          >
            <option v-for="t in types" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="col-span-4">
          <label class="block text-xs text-gray-500 mb-1">Description</label>
          <input
            v-model="prop.description"
            @change="emitUpdate"
            type="text"
            placeholder="Description du paramètre"
            class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <div class="col-span-1 pt-5">
          <label class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer">
            <input
              v-model="prop.required"
              @change="emitUpdate"
              type="checkbox"
              class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
            />
            Req.
          </label>
        </div>
        <div class="col-span-2 pt-5 text-right">
          <button
            @click="removeProperty(index)"
            class="text-red-500 hover:text-red-700 text-sm"
          >
            Supprimer
          </button>
        </div>
      </div>

      <!-- Enum values if string -->
      <div v-if="prop.type === 'string'" class="mt-2">
        <label class="block text-xs text-gray-500 mb-1">Valeurs possibles (séparées par des virgules, optionnel)</label>
        <input
          v-model="prop.enumValues"
          @change="emitUpdate"
          type="text"
          placeholder="valeur1, valeur2, valeur3"
          class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-1 focus:ring-emerald-500"
        />
      </div>
    </div>

    <button
      @click="addProperty"
      type="button"
      class="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-dashed border-gray-400 text-gray-600 rounded-lg hover:border-emerald-500 hover:text-emerald-600 transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Ajouter un paramètre
    </button>
  </div>
</template>
