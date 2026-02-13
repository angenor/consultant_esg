import { onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '../stores/notifications'
import { useAuthStore } from '../stores/auth'

const POLL_INTERVAL = 30_000 // 30 seconds

/**
 * Composable qui démarre le polling des notifications.
 * À utiliser dans le layout principal (App.vue ou AppHeader).
 */
export function useNotifications() {
  const store = useNotificationStore()
  const auth = useAuthStore()
  let intervalId: ReturnType<typeof setInterval> | null = null

  function startPolling() {
    if (intervalId) return
    // Fetch immediately
    if (auth.isAuthenticated) {
      store.fetchUnreadCount()
    }
    // Then poll
    intervalId = setInterval(() => {
      if (auth.isAuthenticated) {
        store.fetchUnreadCount()
      }
    }, POLL_INTERVAL)
  }

  function stopPolling() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  onMounted(startPolling)
  onUnmounted(stopPolling)

  return {
    store,
    startPolling,
    stopPolling,
  }
}
