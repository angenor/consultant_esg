<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppSidebar from './components/common/AppSidebar.vue'
import AppHeader from './components/common/AppHeader.vue'

const route = useRoute()
const authStore = useAuthStore()

const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})

onMounted(() => {
  authStore.init()
})
</script>

<template>
  <!-- Auth pages: no sidebar/header -->
  <router-view v-if="isAuthPage" />

  <!-- Authenticated layout -->
  <div v-else class="flex h-screen bg-gray-100">
    <AppSidebar />
    <div class="ml-64 flex flex-1 flex-col overflow-hidden">
      <AppHeader />
      <main class="flex-1 overflow-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>
