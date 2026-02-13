import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

vi.mock('../../router', () => ({
  default: { push: vi.fn() },
}))

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('login sets token and user', async () => {
    const mockUser = {
      id: '1',
      email: 'test@test.com',
      nom_complet: 'Test User',
      role: 'user' as const,
      is_active: true,
    }

    const mockResponse = {
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
      user: mockUser,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    })

    const store = useAuthStore()
    await store.login('test@test.com', 'test1234')

    expect(store.token).toBe('fake-jwt-token')
    expect(store.user).toEqual(mockUser)
    expect(localStorage.getItem('token')).toBe('fake-jwt-token')
    expect(store.isAuthenticated).toBe(true)
  })

  it('logout clears state and redirects', async () => {
    const { default: router } = await import('../../router')

    const store = useAuthStore()

    // Set initial state
    store.token = 'some-token'
    store.user = {
      id: '1',
      email: 'test@test.com',
      nom_complet: 'Test User',
      role: 'user',
      is_active: true,
    }
    localStorage.setItem('token', 'some-token')

    store.logout()

    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(router.push).toHaveBeenCalledWith('/login')
  })

  it('init calls fetchMe when token exists', async () => {
    const mockUser = {
      id: '1',
      email: 'test@test.com',
      nom_complet: 'Test User',
      role: 'user' as const,
      is_active: true,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser),
    })

    localStorage.setItem('token', 'existing-token')

    // Create a new pinia so the store picks up the token from localStorage
    setActivePinia(createPinia())
    const store = useAuthStore()

    await store.init()

    expect(global.fetch).toHaveBeenCalledWith('/api/auth/me', {
      headers: { Authorization: 'Bearer existing-token' },
    })
    expect(store.user).toEqual(mockUser)
  })
})
