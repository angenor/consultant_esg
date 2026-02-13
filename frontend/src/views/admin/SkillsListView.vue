<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore, type Skill } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const filterCategory = ref<string>('')
const filterStatus = ref<string>('')
const searchQuery = ref('')

const filteredSkills = computed(() => {
  let result = adminStore.skills

  if (filterCategory.value) {
    result = result.filter((s) => s.category === filterCategory.value)
  }
  if (filterStatus.value === 'active') {
    result = result.filter((s) => s.is_active)
  } else if (filterStatus.value === 'inactive') {
    result = result.filter((s) => !s.is_active)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      (s) => s.nom.toLowerCase().includes(q) || s.description.toLowerCase().includes(q),
    )
  }

  return result
})

const categories = ['esg', 'finance', 'carbon', 'report', 'utils', 'document', 'knowledge', 'profile']

function isBuiltin(skill: Skill) {
  return skill.handler_key.startsWith('builtin.')
}

async function handleToggle(skill: Skill) {
  try {
    await adminStore.toggleSkill(skill.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur')
  }
}

async function handleDelete(skill: Skill) {
  if (!confirm(`Supprimer le skill "${skill.nom}" ? Cette action est irréversible.`)) return
  try {
    await adminStore.deleteSkill(skill.id)
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Erreur')
  }
}

onMounted(() => {
  adminStore.loadSkills()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Administration des Skills</h1>
        <p class="mt-1 text-sm text-gray-500">
          Gérez les skills IA : créer, modifier, tester, activer/désactiver
        </p>
      </div>
      <button
        @click="router.push({ name: 'AdminSkillNew' })"
        class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nouveau Skill
      </button>
    </div>

    <!-- Filtres -->
    <div class="flex flex-wrap gap-3 mb-6">
      <select
        v-model="filterCategory"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      >
        <option value="">Toutes catégories</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
      <select
        v-model="filterStatus"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      >
        <option value="">Tous statuts</option>
        <option value="active">Actifs</option>
        <option value="inactive">Inactifs</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher..."
        class="flex-1 min-w-50 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      />
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Error -->
    <div
      v-else-if="adminStore.error"
      class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"
    >
      {{ adminStore.error }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="filteredSkills.length === 0"
      class="text-center py-12 text-gray-500"
    >
      <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      <p>Aucun skill trouvé</p>
    </div>

    <!-- Skills list -->
    <div v-else class="space-y-3">
      <div
        v-for="skill in filteredSkills"
        :key="skill.id"
        class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span
                class="inline-block w-2 h-2 rounded-full"
                :class="skill.is_active ? 'bg-emerald-500' : 'bg-gray-400'"
              ></span>
              <h3 class="font-mono font-semibold text-gray-900">{{ skill.nom }}</h3>
              <span
                class="px-2 py-0.5 text-xs rounded-full font-medium"
                :class="
                  isBuiltin(skill)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-purple-100 text-purple-700'
                "
              >
                {{ isBuiltin(skill) ? 'builtin' : 'custom' }}
              </span>
            </div>
            <p class="text-sm text-gray-600 mb-2 line-clamp-2">{{ skill.description }}</p>
            <div class="flex items-center gap-4 text-xs text-gray-500">
              <span class="px-2 py-0.5 bg-gray-100 rounded">{{ skill.category }}</span>
              <span>Version {{ skill.version }}</span>
              <span :class="skill.is_active ? 'text-emerald-600' : 'text-red-500'">
                {{ skill.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 ml-4">
            <button
              @click="router.push({ name: 'AdminSkillEdit', params: { id: skill.id } })"
              class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Modifier
            </button>
            <button
              @click="handleToggle(skill)"
              class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
              :class="
                skill.is_active
                  ? 'border-orange-300 text-orange-600 hover:bg-orange-50'
                  : 'border-emerald-300 text-emerald-600 hover:bg-emerald-50'
              "
            >
              {{ skill.is_active ? 'Désactiver' : 'Activer' }}
            </button>
            <button
              v-if="!isBuiltin(skill)"
              @click="handleDelete(skill)"
              class="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            >
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Count -->
    <p class="mt-4 text-sm text-gray-500">
      {{ filteredSkills.length }} skill(s) affiché(s) sur {{ adminStore.skills.length }}
    </p>
  </div>
</template>
