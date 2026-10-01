import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiError } from '../types'

const ACCESS_KEY = 'kutubxona_access'
const REFRESH_KEY = 'kutubxona_refresh'

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStore.getRefresh()
  if (!refresh) throw new Error('no refresh token')
  const res = await axios.post('/api/auth/token/refresh/', { refresh })
  const access = res.data.access as string
  const newRefresh = res.data.refresh as string | undefined
  tokenStore.set(access, newRefresh)
  return access
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined

    if (error.response?.status === 401 && original && !original._retry && tokenStore.getRefresh()) {
      original._retry = true
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null
          })
        }
        const access = await refreshPromise
        original.headers = original.headers ?? {}
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch {
        tokenStore.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  },
)

export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined
    const detail = (data?.detail ?? (data as ApiError | undefined)?.error) as unknown
    if (typeof detail === 'string' && detail) return detail
    // Ba'zi joylarda backend {"error": ..., "detail": ...} shaklida qaytaradi,
    // ba'zan esa DRF standart {"field": ["xato"]} — ikkalasini ham qamrab olamiz.
    if (data && typeof data === 'object') {
      for (const qiymat of Object.values(data)) {
        if (typeof qiymat === 'string' && qiymat) return qiymat
        if (Array.isArray(qiymat) && typeof qiymat[0] === 'string') return qiymat[0]
      }
    }
    if (err.response) {
      return `Server xatosi (${err.response.status}). Keyinroq urinib ko'ring.`
    }
    if (err.message) return err.message
  }
  if (err instanceof Error) return err.message
  return "Noma'lum xatolik yuz berdi"
}
