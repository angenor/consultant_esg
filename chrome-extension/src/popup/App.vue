<template>
  <div class="w-[400px] min-h-[500px] bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="bg-emerald-600 text-white px-4 py-3 flex items-center gap-3">
      <img src="../../assets/icons/icon-32.png" alt="ESG" class="w-8 h-8">
      <div>
        <h1 class="text-lg font-bold leading-tight">ESG Advisor</h1>
        <p class="text-emerald-100 text-xs">Guide Fonds Verts</p>
      </div>
      <button
        v-if="isAuthenticated"
        @click="handleLogout"
        class="ml-auto text-emerald-200 hover:text-white text-sm"
      >
        Deconnexion
      </button>
    </header>

    <!-- Contenu -->
    <main class="flex-1 overflow-y-auto">
      <LoginPanel v-if="!isAuthenticated" @login-success="onLoginSuccess" />
      <DashboardPanel v-else :data="syncedData" :loading="syncing" @refresh="syncData" />
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-200 px-4 py-2 bg-white">
      <a
        href="http://localhost:5173"
        target="_blank"
        class="text-xs text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
      >
        Ouvrir la plateforme ESG Advisor
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { authManager } from '@shared/auth'
import type { SyncedData } from '@shared/types'
import LoginPanel from './components/LoginPanel.vue'
import DashboardPanel from './components/DashboardPanel.vue'

const isAuthenticated = ref(false)
const syncedData = ref<SyncedData | null>(null)
const syncing = ref(false)

onMounted(async () => {
  const user = await authManager.checkAuth()
  isAuthenticated.value = !!user
  if (user) {
    await syncData()
  }
})

async function onLoginSuccess() {
  isAuthenticated.value = true
  await syncData()
}

async function syncData() {
  syncing.value = true
  try {
    const response = await chrome.runtime.sendMessage({ type: 'SYNC_DATA' })
    if (response) {
      syncedData.value = response
    }
  } catch (error) {
    console.error('[ESG Advisor] Erreur sync:', error)
  } finally {
    syncing.value = false
  }
}

async function handleLogout() {
  await authManager.logout()
  isAuthenticated.value = false
  syncedData.value = null
}
</script>
