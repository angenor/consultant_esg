import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import router from '../router'

export interface User {
  id: string
  email: string
  nom_complet: string
  role: 'user' | 'admin'
  is_active: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export const useAuthStore = defineStore('auth', () => {
  // --------------- State ---------------
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  // --------------- Getters ---------------
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // --------------- Actions ---------------
  async function login(email: string, password: string) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data: AuthResponse = await response.json()
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
  }

  async function register(email: string, password: string, nom_complet: string) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, nom_complet }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    const data: AuthResponse = await response.json()
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  async function fetchMe() {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      })

      if (!response.ok) {
        throw new Error('Unauthorized')
      }

      const data: User = await response.json()
      user.value = data
    } catch {
      logout()
    }
  }

  async function init() {
    if (token.value) {
      await fetchMe()
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    fetchMe,
    init,
  }
})
