<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { AppNotification } from '../../stores/notifications'
import { useNotifications } from '../../composables/useNotifications'

const router = useRouter()
const { store } = useNotifications()
const isOpen = ref(false)

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    store.fetchNotifications()
  }
}

function close() {
  isOpen.value = false
}

async function handleClick(notif: AppNotification) {
  if (!notif.is_read) {
    await store.markAsRead(notif.id)
  }
  if (notif.lien) {
    router.push(notif.lien)
  }
  close()
}

async function handleMarkAllRead() {
  await store.markAllRead()
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)

  if (diffMin < 1) return "À l'instant"
  if (diffMin < 60) return `Il y a ${diffMin} min`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `Il y a ${diffH}h`
  const diffD = Math.floor(diffH / 24)
  return `Il y a ${diffD}j`
}

function typeIcon(type: string): string {
  const icons: Record<string, string> = {
    action_completee: '✅',
    progres_score: '📈',
    rappel_action: '⏰',
    echeance_fonds: '📅',
    nouveau_fonds: '💰',
  }
  return icons[type] || '🔔'
}

// Close dropdown on outside click
function onClickOutside(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest('.notification-bell')
  if (!el) close()
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <div class="notification-bell relative">
    <button
      title="Notifications"
      class="relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
      @click="toggle"
    >
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <!-- Badge -->
      <span
        v-if="store.hasUnread"
        class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
      >
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 top-12 z-50 w-80 rounded-lg border border-gray-200 bg-white shadow-lg"
      >
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
          <h3 class="text-sm font-semibold text-gray-800">Notifications</h3>
          <button
            v-if="store.hasUnread"
            class="text-xs text-emerald-600 hover:text-emerald-700"
            @click="handleMarkAllRead"
          >
            Tout marquer comme lu
          </button>
        </div>

        <!-- List -->
        <div class="max-h-80 overflow-y-auto">
          <div v-if="store.isLoading" class="px-4 py-6 text-center text-sm text-gray-400">
            Chargement...
          </div>
          <div v-else-if="store.notifications.length === 0" class="px-4 py-6 text-center text-sm text-gray-400">
            Aucune notification
          </div>
          <button
            v-for="notif in store.notifications"
            :key="notif.id"
            class="flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-gray-50"
            :class="{ 'bg-emerald-50/50': !notif.is_read }"
            @click="handleClick(notif)"
          >
            <span class="mt-0.5 text-base">{{ typeIcon(notif.type) }}</span>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-800" :class="{ 'font-semibold': !notif.is_read }">
                {{ notif.titre }}
              </p>
              <p v-if="notif.contenu" class="mt-0.5 truncate text-xs text-gray-500">
                {{ notif.contenu }}
              </p>
              <p class="mt-1 text-[11px] text-gray-400">
                {{ formatTime(notif.created_at) }}
              </p>
            </div>
            <span
              v-if="!notif.is_read"
              class="mt-2 h-2 w-2 shrink-0 rounded-full bg-emerald-500"
            />
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>
