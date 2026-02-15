<template>
  <div class="p-6 flex flex-col items-center">
    <!-- Logo / Illustration -->
    <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
      <svg class="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955
              11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29
              9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    </div>

    <h2 class="text-lg font-semibold text-gray-800 mb-1">Connectez-vous</h2>
    <p class="text-sm text-gray-500 mb-6 text-center">
      Utilisez vos identifiants ESG Advisor
    </p>

    <form @submit.prevent="handleLogin" class="w-full space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="votre@email.com"
          class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
        <input
          v-model="password"
          type="password"
          required
          placeholder="Votre mot de passe"
          class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
      </div>

      <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-emerald-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium
               hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
               flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent
                                     rounded-full animate-spin"></span>
        {{ loading ? 'Connexion...' : 'Se connecter' }}
      </button>
    </form>

    <p class="mt-4 text-xs text-gray-400 text-center">
      Pas encore de compte ?
      <a href="http://localhost:5173/register" target="_blank"
         class="text-emerald-600 hover:underline">
        Inscrivez-vous sur la plateforme
      </a>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { authManager } from '@shared/auth'
import { ApiError } from '@shared/api-client'

const emit = defineEmits<{
  'login-success': []
}>()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''

  try {
    await authManager.login({ email: email.value, password: password.value })
    emit('login-success')
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.message
    } else {
      error.value = 'Erreur de connexion. Verifiez votre connexion internet.'
    }
  } finally {
    loading.value = false
  }
}
</script>
