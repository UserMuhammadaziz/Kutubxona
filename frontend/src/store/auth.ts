import { create } from 'zustand'
import { authApi } from '../api/resources'
import { tokenStore } from '../api/client'
import type { User } from '../types'

interface AuthState {
  user: User | null
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated'
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  hydrate: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'idle',

  login: async (username, password) => {
    const { access, refresh } = await authApi.login(username, password)
    tokenStore.set(access, refresh)
    const user = await authApi.me()
    set({ user, status: 'authenticated' })
  },

  logout: () => {
    tokenStore.clear()
    set({ user: null, status: 'unauthenticated' })
  },

  hydrate: async () => {
    if (!tokenStore.getAccess()) {
      set({ status: 'unauthenticated' })
      return
    }
    set({ status: 'loading' })
    try {
      const user = await authApi.me()
      set({ user, status: 'authenticated' })
    } catch {
      tokenStore.clear()
      set({ user: null, status: 'unauthenticated' })
    }
  },
}))

export const isAdmin = (user: User | null) => user?.rol === 'administrator'
