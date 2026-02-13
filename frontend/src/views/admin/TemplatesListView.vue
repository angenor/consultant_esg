<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAdminStore, type ReportTemplate } from '../../stores/admin'

const adminStore = useAdminStore()
const searchQuery = ref('')
const showCreateForm = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const error = ref<string | null>(null)

const form = ref({
  nom: '',
  description: '',
  sections_json: '{\n  "sections": []\n}',
  template_html: '<div>\n  <h1>{{titre}}</h1>\n</div>',
})

const filteredTemplates = computed(() => {
  if (!searchQuery.value) return adminStore.templates
  const q = searchQuery.value.toLowerCase()
  return adminStore.templates.filter((t) => t.nom.toLowerCase().includes(q))
})

function startCreate() {
  editingId.value = null
  form.value = {
    nom: '',
    description: '',
    sections_json: '{\n  "sections": []\n}',
    template_html: '<div>\n  <h1>{{titre}}</h1>\n</div>',
  }
  showCreateForm.value = true
}

function startEdit(t: ReportTemplate) {
  editingId.value = t.id
  form.value = {
    nom: t.nom,
    description: t.description || '',
    sections_json: JSON.stringify(t.sections_json, null, 2),
    template_html: t.template_html,
  }
  showCreateForm.value = true
}

function cancelForm() {
  showCreateForm.value = false
  editingId.value = null
}

async function handleSubmit() {
  saving.value = true
  error.value = null
  try {
    const payload = {
      nom: form.value.nom,
      description: form.value.description || null,
      sections_json: JSON.parse(form.value.sections_json),
      template_html: form.value.template_html,
    }
    if (editingId.value) {
      await adminStore.updateTemplate(editingId.value, payload)
    } else {
      await adminStore.createTemplate(payload)
    }
    showCreateForm.value = false
    editingId.value = null
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

async function handleDelete(t: ReportTemplate) {
  if (!confirm(`Supprimer le template "${t.nom}" ?`)) return
  try {
    await adminStore.deleteTemplate(t.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur lors de la suppression')
  }
}

onMounted(() => adminStore.loadTemplates())
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Templates Rapports</h1>
        <p class="mt-1 text-sm text-gray-500">{{ filteredTemplates.length }} template(s)</p>
      </div>
      <button
        @click="startCreate()"
        class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouveau Template
      </button>
    </div>

    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher..."
        class="w-full max-w-sm border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500"
      />
    </div>

    <!-- Create/Edit Form -->
    <div v-if="showCreateForm" class="mb-6 bg-white border border-gray-200 rounded-lg p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">
        {{ editingId ? 'Modifier le Template' : 'Nouveau Template' }}
      </h2>
      <div v-if="error" class="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        {{ error }}
      </div>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
            <input v-model="form.nom" type="text" required
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input v-model="form.description" type="text"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Structure JSON</label>
          <textarea v-model="form.sections_json" rows="4"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-emerald-500"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Template HTML</label>
          <textarea v-model="form.template_html" rows="6"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-emerald-500"></textarea>
        </div>
        <div class="flex items-center gap-3">
          <button type="submit" :disabled="saving"
            class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50">
            {{ editingId ? 'Sauvegarder' : 'Créer' }}
          </button>
          <button type="button" @click="cancelForm()"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
            Annuler
          </button>
        </div>
      </form>
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- List -->
    <div v-if="!adminStore.loading" class="space-y-3">
      <div
        v-for="t in filteredTemplates"
        :key="t.id"
        class="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:shadow-md transition-shadow"
      >
        <div>
          <div class="flex items-center gap-3">
            <h3 class="font-semibold text-gray-900">{{ t.nom }}</h3>
            <span
              :class="t.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'"
              class="px-2 py-0.5 text-xs font-medium rounded-full"
            >
              {{ t.is_active ? 'Actif' : 'Inactif' }}
            </span>
          </div>
          <p v-if="t.description" class="text-sm text-gray-500 mt-1">{{ t.description }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="startEdit(t)"
            class="px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100">
            Modifier
          </button>
          <button @click="handleDelete(t)"
            class="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100">
            Supprimer
          </button>
        </div>
      </div>

      <div v-if="filteredTemplates.length === 0 && !adminStore.loading" class="text-center py-12 text-gray-500">
        Aucun template trouvé
      </div>
    </div>
  </div>
</template>
