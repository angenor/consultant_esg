<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

defineProps<{
  open?: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const authStore = useAuthStore()

const mainNav = [
  { to: '/chat', label: 'Chat', icon: 'chat' },
  { to: '/dashboard', label: 'Tableau de bord', icon: 'chart' },
  { to: '/documents', label: 'Documents', icon: 'document' },
  { to: '/carbon', label: 'Empreinte Carbone', icon: 'leaf' },
  { to: '/credit-score', label: 'Score Crédit', icon: 'star' },
  { to: '/action-plan', label: "Plan d'Action", icon: 'clipboard' },
]

const adminNav = [
  { to: '/admin/skills', label: 'Skills' },
  { to: '/admin/referentiels', label: 'Référentiels' },
  { to: '/admin/fonds', label: 'Fonds Verts' },
  { to: '/admin/templates', label: 'Templates' },
  { to: '/admin/stats', label: 'Statistiques' },
]

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
  <!-- Mobile backdrop -->
  <Transition
    enter-active-class="transition-opacity duration-300"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="open"
      class="fixed inset-0 z-20 bg-black/40 md:hidden"
      @click="emit('close')"
    />
  </Transition>

  <aside
    class="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-gray-900 text-white transition-transform duration-300 md:translate-x-0"
    :class="open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <!-- Logo -->
    <div class="flex items-center justify-between px-5 py-5">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600">
          <svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.5S2 11.5 2 13.5s1.75 3.75 1.75 3.75" />
          </svg>
        </div>
        <span class="text-lg font-bold tracking-wide">ESG Advisor</span>
      </div>
      <!-- Mobile close -->
      <button
        class="rounded-lg p-1 text-gray-400 hover:text-white md:hidden"
        @click="emit('close')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Main Navigation -->
    <nav class="mt-2 flex-1 space-y-1 overflow-y-auto px-3">
      <RouterLink
        v-for="item in mainNav"
        :key="item.to"
        :to="item.to"
        active-class="!bg-emerald-600"
        class="flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-800 hover:text-white"
        @click="emit('close')"
      >
        <!-- Chat icon -->
        <svg v-if="item.icon === 'chat'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <!-- Chart icon -->
        <svg v-else-if="item.icon === 'chart'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 20V10M12 20V4M6 20v-6" />
        </svg>
        <!-- Document icon -->
        <svg v-else-if="item.icon === 'document'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        <!-- Leaf icon -->
        <svg v-else-if="item.icon === 'leaf'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.5S2 11.5 2 13.5s1.75 3.75 1.75 3.75" />
        </svg>
        <!-- Star icon -->
        <svg v-else-if="item.icon === 'star'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
        <!-- Clipboard icon -->
        <svg v-else-if="item.icon === 'clipboard'" class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
          <line x1="8" y1="12" x2="16" y2="12" />
          <line x1="8" y1="16" x2="16" y2="16" />
        </svg>
        <span>{{ item.label }}</span>
      </RouterLink>

      <!-- Separator + Admin section -->
      <template v-if="authStore.isAdmin">
        <div class="my-4 border-t border-gray-700" />
        <p class="mb-2 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
          Administration
        </p>
        <RouterLink
          v-for="item in adminNav"
          :key="item.to"
          :to="item.to"
          active-class="!bg-emerald-600"
          class="flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-800 hover:text-white"
          @click="emit('close')"
        >
          <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>{{ item.label }}</span>
        </RouterLink>
      </template>
    </nav>

    <!-- Bottom: User info + Logout -->
    <div class="border-t border-gray-700 p-4">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-sm font-semibold">
          {{ userInitials }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-white">
            {{ authStore.user?.nom_complet ?? 'Utilisateur' }}
          </p>
          <p class="truncate text-xs text-gray-400">
            {{ authStore.user?.email ?? '' }}
          </p>
        </div>
        <button
          title="Se déconnecter"
          class="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
          @click="authStore.logout()"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>
