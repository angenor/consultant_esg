<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppSidebar from './components/common/AppSidebar.vue'
import AppHeader from './components/common/AppHeader.vue'

const route = useRoute()
const authStore = useAuthStore()
const sidebarOpen = ref(false)

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
    <AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />
    <div class="flex flex-1 flex-col overflow-hidden md:ml-64">
      <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="flex-1 overflow-auto p-6">
        <router-view v-slot="{ Component }">
          <Transition
            enter-active-class="transition-opacity duration-200 ease-out"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition-opacity duration-150 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
            mode="out-in"
          >
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>
