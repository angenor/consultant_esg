import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock chrome.storage
const mockStorage: Record<string, Record<string, unknown>> = {
  session: {},
  local: {},
}

vi.stubGlobal('chrome', {
  storage: {
    session: {
      get: vi.fn(async (key: string) => ({ [key]: mockStorage.session[key] })),
      set: vi.fn(async (data: Record<string, unknown>) => {
        Object.assign(mockStorage.session, data)
      }),
      remove: vi.fn(async (key: string) => {
        delete mockStorage.session[key]
      }),
    },
    local: {
      get: vi.fn(async (key: string) => ({ [key]: mockStorage.local[key] })),
      set: vi.fn(async (data: Record<string, unknown>) => {
        Object.assign(mockStorage.local, data)
      }),
      remove: vi.fn(async (key: string) => {
        delete mockStorage.local[key]
      }),
    },
  },
})

// Mock fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('AuthManager', () => {
  beforeEach(() => {
    mockStorage.session = {}
    mockStorage.local = {}
    vi.clearAllMocks()
  })

  it('hasToken retourne false sans token', async () => {
    const { authManager } = await import('../src/shared/auth')
    const hasToken = await authManager.hasToken()
    expect(hasToken).toBe(false)
  })

  it('hasToken retourne true avec token', async () => {
    mockStorage.session['esg_jwt_token'] = 'test-token'
    const { authManager } = await import('../src/shared/auth')
    const hasToken = await authManager.hasToken()
    expect(hasToken).toBe(true)
  })

  it('getCachedUser retourne null sans utilisateur cache', async () => {
    const { authManager } = await import('../src/shared/auth')
    const user = await authManager.getCachedUser()
    expect(user).toBeNull()
  })

  it('getCachedUser retourne l\'utilisateur cache', async () => {
    const mockUser = { id: '1', email: 'test@test.com', nom_complet: 'Test', role: 'user', is_active: true }
    mockStorage.local['esg_user'] = mockUser
    const { authManager } = await import('../src/shared/auth')
    const user = await authManager.getCachedUser()
    expect(user).toEqual(mockUser)
  })

  it('logout efface les donnees', async () => {
    mockStorage.session['esg_jwt_token'] = 'token'
    mockStorage.local['esg_user'] = { id: '1' }
    const { authManager } = await import('../src/shared/auth')
    await authManager.logout()
    expect(chrome.storage.session.remove).toHaveBeenCalledWith('esg_jwt_token')
    expect(chrome.storage.local.remove).toHaveBeenCalledWith([
      'esg_user',
      'esg_synced_data',
      'esg_active_application',
    ])
  })
})
