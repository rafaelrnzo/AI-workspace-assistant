import { create } from 'zustand'

const TOKEN_KEY = 'auth-token'
const USER_KEY = 'auth-user'

export interface AuthUser {
  id: string
  name: string
  email: string
  role: 'user' | 'admin'
}

interface AuthStore {
  token: string | null
  user: AuthUser | null
  error: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, role: string) => Promise<void>
  logout: () => void
  restore: () => Promise<void>
}

const api = async (path: string, body: object) => {
  const res = await fetch(`/api/auth${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `Error ${res.status}`)
  }
  return res.json()
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  token: localStorage.getItem(TOKEN_KEY),
  user: (() => {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })(),
  error: null,
  loading: false,

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const data = await api('/login', { email, password })
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      set({ token: data.access_token, user: data.user, loading: false })
    } catch (err: any) {
      set({ error: err.message, loading: false })
    }
  },

  register: async (name, email, password, role) => {
    set({ loading: true, error: null })
    try {
      const data = await api('/register', { name, email, password, role })
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      set({ token: data.access_token, user: data.user, loading: false })
    } catch (err: any) {
      set({ error: err.message, loading: false })
    }
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    set({ token: null, user: null })
  },

  restore: async () => {
    const token = get().token
    if (!token) return
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error()
      const user = await res.json()
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      set({ user })
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      set({ token: null, user: null })
    }
  },
}))

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
