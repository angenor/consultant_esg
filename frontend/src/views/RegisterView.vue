<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const nom_complet = ref('')
const email = ref('')
const password = ref('')
const password_confirm = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (password.value !== password_confirm.value) {
    error.value = 'Les mots de passe ne correspondent pas.'
    return
  }

  if (password.value.length < 6) {
    error.value = 'Le mot de passe doit contenir au moins 6 caractères.'
    return
  }

  loading.value = true

  try {
    await authStore.register(email.value, password.value, nom_complet.value)
    router.push('/chat')
  } catch (err: any) {
    error.value = err.message || 'Une erreur est survenue lors de l\'inscription.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4">
    <div class="max-w-md w-full">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
          <svg
            class="w-8 h-8 text-emerald-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">ESG Mefali</h1>
        <p class="text-gray-500 mt-2">Votre assistant intelligent en conseil ESG</p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-lg shadow-md p-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Créer un compte</h2>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <!-- Nom complet -->
          <div>
            <label for="nom_complet" class="block text-sm font-medium text-gray-700 mb-1">
              Nom complet
            </label>
            <input
              id="nom_complet"
              v-model="nom_complet"
              type="text"
              required
              autocomplete="name"
              placeholder="Jean Dupont"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
            />
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Adresse e-mail
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="vous@exemple.com"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Mot de passe
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="new-password"
              placeholder="Au moins 6 caractères"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
            />
          </div>

          <!-- Password confirmation -->
          <div>
            <label for="password_confirm" class="block text-sm font-medium text-gray-700 mb-1">
              Confirmer le mot de passe
            </label>
            <input
              id="password_confirm"
              v-model="password_confirm"
              type="password"
              required
              autocomplete="new-password"
              placeholder="Confirmer votre mot de passe"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
            />
          </div>

          <!-- Error message -->
          <p v-if="error" class="text-red-600 text-sm mt-2">{{ error }}</p>

          <!-- Submit button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-emerald-600 text-white py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors font-medium cursor-pointer disabled:cursor-not-allowed"
          >
            <span v-if="loading" class="inline-flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="none"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Inscription en cours...
            </span>
            <span v-else>Créer un compte</span>
          </button>
        </form>

        <!-- Login link -->
        <p class="text-center text-sm text-gray-600 mt-6">
          Déjà un compte ?
          <RouterLink to="/login" class="text-emerald-600 hover:text-emerald-700 font-medium">
            Se connecter
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
