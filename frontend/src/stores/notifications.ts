import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

export interface AppNotification {
  id: string
  type: string
  titre: string
  contenu: string | null
  lien: string | null
  is_read: boolean
  created_at: string
}

export const useNotificationStore = defineStore('notifications', () => {
  const { get, put } = useApi()

  // --------------- State ---------------
  const notifications = ref<AppNotification[]>([])
  const unreadCount = ref(0)
  const isLoading = ref(false)

  // --------------- Getters ---------------
  const hasUnread = computed(() => unreadCount.value > 0)

  // --------------- Actions ---------------
  async function fetchUnreadCount() {
    try {
      const data = await get<{ count: number }>('/api/notifications/unread-count')
      unreadCount.value = data.count
    } catch {
      // Silently fail for polling
    }
  }

  async function fetchNotifications(limit = 20) {
    isLoading.value = true
    try {
      notifications.value = await get<AppNotification[]>(
        `/api/notifications/?limit=${limit}`
      )
    } catch {
      // fail silently
    } finally {
      isLoading.value = false
    }
  }

  async function markAsRead(id: string) {
    try {
      await put<AppNotification>(`/api/notifications/${id}/read`)
      const notif = notifications.value.find((n) => n.id === id)
      if (notif && !notif.is_read) {
        notif.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // fail silently
    }
  }

  async function markAllRead() {
    try {
      await put('/api/notifications/read-all')
      notifications.value.forEach((n) => (n.is_read = true))
      unreadCount.value = 0
    } catch {
      // fail silently
    }
  }

  return {
    notifications,
    unreadCount,
    isLoading,
    hasUnread,
    fetchUnreadCount,
    fetchNotifications,
    markAsRead,
    markAllRead,
  }
})
