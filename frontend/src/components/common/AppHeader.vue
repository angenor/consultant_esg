<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import NotificationBell from './NotificationBell.vue'

const emit = defineEmits<{
  toggleSidebar: []
}>()

const route = useRoute()
const authStore = useAuthStore()

const pageTitle = computed(() => {
  return (route.meta?.title as string) || (route.name as string) || 'ESG Mefali'
})

const userInitials = computed(() => {
  if (!authStore.user?.nom_complet) return '?'
  return authStore.user.nom_complet
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})
</script>

<template>
  <header class="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm">
    <div class="flex items-center gap-3">
      <!-- Mobile hamburger -->
      <button
        class="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 md:hidden"
        @click="emit('toggleSidebar')"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>
      <!-- Page title -->
      <h1 class="text-lg font-semibold text-gray-800">{{ pageTitle }}</h1>
    </div>

    <!-- Right: Notification bell + User avatar -->
    <div class="flex items-center gap-4">
      <NotificationBell />

      <!-- User avatar -->
      <div class="flex items-center gap-3">
        <span class="hidden text-sm font-medium text-gray-700 sm:block">
          {{ authStore.user?.nom_complet ?? 'Utilisateur' }}
        </span>
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-xs font-semibold text-white">
          {{ userInitials }}
        </div>
      </div>
    </div>
  </header>
</template>
