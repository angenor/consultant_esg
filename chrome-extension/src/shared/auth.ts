import { apiClient, ApiError } from './api-client'
import { STORAGE_KEYS } from './constants'
import type { User, LoginRequest, AuthResponse } from './types'

class AuthManager {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.login(credentials)

    await chrome.storage.session.set({
      [STORAGE_KEYS.TOKEN]: response.access_token,
    })

    await chrome.storage.local.set({
      [STORAGE_KEYS.USER]: response.user,
    })

    return response
  }

  async logout(): Promise<void> {
    await chrome.storage.session.remove(STORAGE_KEYS.TOKEN)
    await chrome.storage.local.remove([
      STORAGE_KEYS.USER,
      STORAGE_KEYS.SYNCED_DATA,
      STORAGE_KEYS.ACTIVE_APPLICATION,
    ])
  }

  async checkAuth(): Promise<User | null> {
    try {
      const tokenResult = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
      if (!tokenResult[STORAGE_KEYS.TOKEN]) {
        return null
      }

      const user = await apiClient.get<User>('/api/auth/me')
      await chrome.storage.local.set({ [STORAGE_KEYS.USER]: user })
      return user
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        await this.logout()
      }
      return null
    }
  }

  async getCachedUser(): Promise<User | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.USER)
    return result[STORAGE_KEYS.USER] || null
  }

  async hasToken(): Promise<boolean> {
    const result = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
    return !!result[STORAGE_KEYS.TOKEN]
  }
}

export const authManager = new AuthManager()
