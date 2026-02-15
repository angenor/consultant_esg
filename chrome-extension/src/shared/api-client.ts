import { API_BASE_URL, STORAGE_KEYS } from './constants'
import type { AuthResponse, LoginRequest } from './types'

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  private async getToken(): Promise<string | null> {
    const result = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
    return result[STORAGE_KEYS.TOKEN] || null
  }

  async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options: { skipAuth?: boolean } = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (!options.skipAuth) {
      const token = await this.getToken()
      if (!token) {
        throw new ApiError('Non authentifie', 401)
      }
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `Erreur ${response.status}`,
        response.status
      )
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  get<T>(path: string) { return this.request<T>('GET', path) }
  post<T>(path: string, body?: unknown) { return this.request<T>('POST', path, body) }
  put<T>(path: string, body?: unknown) { return this.request<T>('PUT', path, body) }
  del<T>(path: string) { return this.request<T>('DELETE', path) }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('POST', '/api/auth/login', credentials, { skipAuth: true })
  }
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

export const apiClient = new ApiClient()
