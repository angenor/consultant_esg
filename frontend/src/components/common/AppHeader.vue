<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const pageTitle = computed(() => {
  return (route.meta?.title as string) || (route.name as string) || 'ESG Advisor'
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
    <!-- Left: Page title -->
    <h1 class="text-lg font-semibold text-gray-800">{{ pageTitle }}</h1>

    <!-- Right: Notification bell + User avatar -->
    <div class="flex items-center gap-4">
      <!-- Notification bell placeholder -->
      <button
        title="Notifications"
        class="relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        <!-- Notification dot -->
        <span class="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-500" />
      </button>

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
