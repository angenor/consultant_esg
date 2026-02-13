<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()

onMounted(() => adminStore.loadStats())
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Statistiques</h1>

    <!-- Loading -->
    <div v-if="!adminStore.stats" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>

    <!-- Stats cards -->
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Utilisateurs</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.users }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Entreprises</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.entreprises }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Conversations</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.conversations }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Scores ESG</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.scores_esg }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Skills</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">
          {{ adminStore.stats.skills.active }}
          <span class="text-sm font-normal text-gray-400">/ {{ adminStore.stats.skills.total }}</span>
        </p>
        <p class="text-xs text-gray-400 mt-1">actifs / total</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Référentiels ESG</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.referentiels }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Fonds Verts</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ adminStore.stats.fonds_verts }}</p>
      </div>
    </div>
  </div>
</template>
