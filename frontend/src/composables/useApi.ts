import router from '../router'

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token')

  const headers = new Headers(options.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  // Set Content-Type to application/json unless the body is FormData
  // (let the browser set the correct multipart boundary for FormData)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    localStorage.removeItem('token')
    router.push('/login')
    throw new Error('Session expired. Redirecting to login.')
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`
    try {
      const errorBody = await response.json()
      errorMessage = errorBody.detail || errorBody.message || errorMessage
    } catch {
      // response body was not JSON — keep the default message
    }
    throw new Error(errorMessage)
  }

  return response.json() as Promise<T>
}

export function useApi() {
  function get<T>(url: string): Promise<T> {
    return request<T>(url, { method: 'GET' })
  }

  function post<T>(url: string, body?: unknown): Promise<T> {
    return request<T>(url, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  function put<T>(url: string, body?: unknown): Promise<T> {
    return request<T>(url, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  function del<T>(url: string): Promise<T> {
    return request<T>(url, { method: 'DELETE' })
  }

  function upload<T>(url: string, formData: FormData): Promise<T> {
    return request<T>(url, {
      method: 'POST',
      body: formData,
    })
  }

  return { get, post, put, del, upload }
}
