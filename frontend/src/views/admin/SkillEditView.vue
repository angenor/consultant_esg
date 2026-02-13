<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore, type Skill } from '../../stores/admin'
import SkillForm, { type SkillFormData } from '../../components/admin/SkillForm.vue'
import SkillTestPanel from '../../components/admin/SkillTestPanel.vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const isNew = computed(() => route.name === 'AdminSkillNew')
const skillId = computed(() => (isNew.value ? null : (route.params.id as string)))

const skill = ref<Skill | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const savedSkillId = ref<string | null>(null)

const isBuiltin = computed(() => skill.value?.handler_key.startsWith('builtin.') ?? false)

const initialData = computed(() => {
  if (!skill.value) return undefined
  return {
    nom: skill.value.nom,
    description: skill.value.description,
    category: skill.value.category || 'esg',
    input_schema: skill.value.input_schema,
    handler_key: skill.value.handler_key,
    handler_code: skill.value.handler_code || '',
  }
})

async function loadSkill() {
  if (isNew.value || !skillId.value) return

  loading.value = true
  error.value = null
  try {
    skill.value = await adminStore.getSkill(skillId.value)
    savedSkillId.value = skill.value.id
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
  } finally {
    loading.value = false
  }
}

async function handleSubmit(data: SkillFormData) {
  saving.value = true
  error.value = null

  try {
    if (isNew.value) {
      const created = await adminStore.createSkill(data)
      savedSkillId.value = created.id
      router.replace({ name: 'AdminSkillEdit', params: { id: created.id } })
    } else if (skillId.value) {
      const updatePayload: Record<string, unknown> = {}
      if (data.description) updatePayload.description = data.description
      if (data.category) updatePayload.category = data.category
      if (data.input_schema) updatePayload.input_schema = data.input_schema
      if (data.handler_code && !isBuiltin.value) updatePayload.handler_code = data.handler_code

      await adminStore.updateSkill(skillId.value, updatePayload)
      skill.value = await adminStore.getSkill(skillId.value)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'AdminSkills' })
}

onMounted(loadSkill)
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-6">
      <button
        @click="router.push({ name: 'AdminSkills' })"
        class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Retour aux skills
      </button>
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isNew ? 'Créer un nouveau Skill' : `Modifier : ${skill?.nom || '...'}` }}
      </h1>
      <p v-if="skill" class="mt-1 text-sm text-gray-500">
        Version {{ skill.version }} &middot;
        <span :class="skill.is_active ? 'text-emerald-600' : 'text-red-500'">
          {{ skill.is_active ? 'Actif' : 'Inactif' }}
        </span>
        <span v-if="isBuiltin" class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
          builtin
        </span>
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700"
    >
      {{ error }}
    </div>

    <!-- Form -->
    <div v-if="!loading" class="space-y-6">
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <SkillForm
          :initial-data="initialData"
          :is-edit="!isNew"
          :is-builtin="isBuiltin"
          :saving="saving"
          @submit="handleSubmit"
          @cancel="handleCancel"
        />
      </div>

      <!-- Test Panel -->
      <SkillTestPanel :skill-id="savedSkillId || skillId" />
    </div>
  </div>
</template>
