<script setup lang="ts">
import { ref, watch } from 'vue'
import SkillCodeEditor from './SkillCodeEditor.vue'
import SchemaBuilder from './SchemaBuilder.vue'

export interface SkillFormData {
  nom: string
  description: string
  category: string
  input_schema: Record<string, unknown>
  handler_key: string
  handler_code: string
}

const props = withDefaults(
  defineProps<{
    initialData?: Partial<SkillFormData>
    isEdit?: boolean
    isBuiltin?: boolean
    saving?: boolean
  }>(),
  {
    isEdit: false,
    isBuiltin: false,
    saving: false,
  },
)

const emit = defineEmits<{
  submit: [data: SkillFormData]
  cancel: []
}>()

const form = ref<SkillFormData>({
  nom: props.initialData?.nom || '',
  description: props.initialData?.description || '',
  category: props.initialData?.category || 'esg',
  input_schema: props.initialData?.input_schema || { type: 'object', properties: {} },
  handler_key: props.initialData?.handler_key || 'custom.',
  handler_code:
    props.initialData?.handler_code ||
    `async def execute(params, context):
    """
    params: dict avec les paramètres définis ci-dessus
    context: dict avec db, rag, entreprise_id
    Retourne: dict avec les résultats
    """
    return {"message": "Hello from skill"}`,
})

// Sync handler_key with nom for new custom skills
watch(
  () => form.value.nom,
  (nom) => {
    if (!props.isEdit && !props.isBuiltin) {
      form.value.handler_key = `custom.${nom}`
    }
  },
)

// Schema mode toggle
const schemaMode = ref<'visual' | 'json'>('json')
const inputSchemaJson = ref(JSON.stringify(form.value.input_schema, null, 2))
const schemaError = ref<string | null>(null)

watch(inputSchemaJson, (val) => {
  try {
    form.value.input_schema = JSON.parse(val)
    schemaError.value = null
  } catch {
    schemaError.value = 'JSON invalide'
  }
})

watch(
  () => form.value.input_schema,
  (val) => {
    // Only update JSON text when schema changes from visual mode
    if (schemaMode.value === 'visual') {
      inputSchemaJson.value = JSON.stringify(val, null, 2)
    }
  },
  { deep: true },
)

// Watch for external initialData changes (when skill is loaded)
watch(
  () => props.initialData,
  (data) => {
    if (data) {
      form.value.nom = data.nom || form.value.nom
      form.value.description = data.description || form.value.description
      form.value.category = data.category || form.value.category
      form.value.input_schema = data.input_schema || form.value.input_schema
      form.value.handler_key = data.handler_key || form.value.handler_key
      form.value.handler_code = data.handler_code || form.value.handler_code
      inputSchemaJson.value = JSON.stringify(form.value.input_schema, null, 2)
    }
  },
  { deep: true },
)

const categories = [
  { value: 'esg', label: 'ESG' },
  { value: 'finance', label: 'Finance' },
  { value: 'carbon', label: 'Carbone' },
  { value: 'report', label: 'Rapports' },
  { value: 'document', label: 'Documents' },
  { value: 'knowledge', label: 'Connaissances' },
  { value: 'profile', label: 'Profil' },
  { value: 'utils', label: 'Utilitaires' },
]

function handleSubmit() {
  if (schemaError.value) return
  emit('submit', { ...form.value })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- Nom technique -->
    <div>
      <label class="block text-sm font-medium text-gray-700">Nom technique *</label>
      <input
        v-model="form.nom"
        type="text"
        required
        pattern="[a-z_]+"
        :disabled="isEdit"
        placeholder="mon_nouveau_skill"
        class="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100 disabled:text-gray-500"
      />
      <p class="text-xs text-gray-500 mt-1">Lettres minuscules et underscores uniquement</p>
    </div>

    <!-- Description -->
    <div>
      <label class="block text-sm font-medium text-gray-700">Description (envoyée au LLM) *</label>
      <textarea
        v-model="form.description"
        rows="3"
        required
        placeholder="Décrivez précisément ce que fait ce skill..."
        class="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      />
      <p class="text-xs text-amber-600 mt-1">
        Cette description est envoyée au LLM. Soyez précis pour qu'il sache quand utiliser ce skill.
      </p>
    </div>

    <!-- Catégorie -->
    <div>
      <label class="block text-sm font-medium text-gray-700">Catégorie *</label>
      <select
        v-model="form.category"
        class="mt-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      >
        <option v-for="cat in categories" :key="cat.value" :value="cat.value">
          {{ cat.label }}
        </option>
      </select>
    </div>

    <!-- JSON Schema -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Paramètres d'entrée (JSON Schema)</label>
      <div class="flex gap-2 mb-2">
        <button
          type="button"
          @click="schemaMode = 'visual'"
          class="px-3 py-1 text-sm rounded-lg transition-colors"
          :class="schemaMode === 'visual' ? 'bg-emerald-100 text-emerald-700 font-medium' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          Visuel
        </button>
        <button
          type="button"
          @click="schemaMode = 'json'"
          class="px-3 py-1 text-sm rounded-lg transition-colors"
          :class="schemaMode === 'json' ? 'bg-emerald-100 text-emerald-700 font-medium' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          JSON
        </button>
      </div>

      <SchemaBuilder
        v-if="schemaMode === 'visual'"
        v-model="form.input_schema"
      />

      <div v-else>
        <SkillCodeEditor
          v-model="inputSchemaJson"
          language="json"
          :height="200"
        />
        <p v-if="schemaError" class="text-xs text-red-500 mt-1">{{ schemaError }}</p>
      </div>

      <p class="text-xs text-gray-500 mt-1">
        Ce schéma définit les paramètres que le LLM peut envoyer au skill.
      </p>
    </div>

    <!-- Code Python (custom only) -->
    <div v-if="!isBuiltin">
      <label class="block text-sm font-medium text-gray-700 mb-1">Code Python du handler</label>
      <SkillCodeEditor
        v-model="form.handler_code"
        language="python"
        :height="400"
        placeholder="async def execute(params, context):
    # Votre code ici
    return {}"
      />

      <details class="mt-2 text-sm text-gray-600">
        <summary class="cursor-pointer hover:text-gray-800">Fonctions disponibles dans context</summary>
        <ul class="mt-1 ml-4 list-disc space-y-1">
          <li><code class="text-xs bg-gray-100 px-1 rounded">context["db"].fetch_one(sql, *args)</code> — un résultat</li>
          <li><code class="text-xs bg-gray-100 px-1 rounded">context["db"].fetch_all(sql, *args)</code> — liste</li>
          <li><code class="text-xs bg-gray-100 px-1 rounded">context["rag"].search(query, category, top_k)</code> — recherche sémantique</li>
          <li>Modules : <code class="text-xs bg-gray-100 px-1 rounded">json</code>, <code class="text-xs bg-gray-100 px-1 rounded">datetime</code>, <code class="text-xs bg-gray-100 px-1 rounded">math</code>, <code class="text-xs bg-gray-100 px-1 rounded">re</code></li>
        </ul>
      </details>
    </div>

    <div v-else class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
      Le code des skills builtin est dans le code source et ne peut pas être modifié ici.
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
      <button
        type="button"
        @click="emit('cancel')"
        class="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
      >
        Annuler
      </button>
      <button
        type="submit"
        :disabled="saving || !!schemaError"
        class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <span v-if="saving">Sauvegarde...</span>
        <span v-else>{{ isEdit ? 'Sauvegarder' : 'Créer le Skill' }}</span>
      </button>
    </div>
  </form>
</template>
