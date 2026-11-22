import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { avtomatikXatolikniYubor } from '../lib/xatolikXabari'

const ACCESS_KEY = 'kutubxona_access'
const REFRESH_KEY = 'kutubxona_refresh'
const ORG_KEY = 'kutubxona_organization'

// Storage bloklangan (private rejim / iframe) bo'lganda ham joriy sessiya ishlashi
// uchun qiymatlarni xotirada saqlaymiz.
let memoryAccess: string | null = null
let memoryRefresh: string | null = null
let memoryOrganization: number | null = null

function readStore(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStore(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* storage taqiqlangan — faqat xotira yetarli */
  }
}

function removeStore(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch {
    /* storage taqiqlangan */
  }
}

export const tokenStore = {
  getAccess: () => readStore(ACCESS_KEY) ?? memoryAccess,
  getRefresh: () => readStore(REFRESH_KEY) ?? memoryRefresh,
  set: (access: string, refresh?: string) => {
    memoryAccess = access
    writeStore(ACCESS_KEY, access)
    if (refresh) {
      memoryRefresh = refresh
      writeStore(REFRESH_KEY, refresh)
    }
  },
  clear: () => {
    memoryAccess = null
    memoryRefresh = null
    removeStore(ACCESS_KEY)
    removeStore(REFRESH_KEY)
  },
}

/**
 * Tanlangan kutubxona (tenant) ID si. Zustand store'i bu qiymatni o'z holatiga
 * ham nusxalaydi; so'rov interceptor'i esa har doim shu yerdan o'qiydi — shuning
 * uchun header darrov, qayta render kutmasdan yangilanadi.
 */
export const tenantStore = {
  get: (): number | null => {
    const raw = readStore(ORG_KEY)
    if (raw !== null) {
      const parsed = Number(raw)
      if (Number.isInteger(parsed) && parsed > 0) return parsed
      return null
    }
    return memoryOrganization
  },
  set: (id: number | null) => {
    memoryOrganization = id
    if (id === null || id === undefined) removeStore(ORG_KEY)
    else writeStore(ORG_KEY, String(id))
  },
}

type TenantRequiredListener = () => void
const tenantRequiredListeners = new Set<TenantRequiredListener>()

/** 400 {"organization": ...} kelganda tanlagichni ochish uchun yengil hodisalar busi. */
export function onTenantRequired(listener: TenantRequiredListener): () => void {
  tenantRequiredListeners.add(listener)
  return () => {
    tenantRequiredListeners.delete(listener)
  }
}

function notifyTenantRequired(): void {
  tenantRequiredListeners.forEach((listener) => listener())
}

function hasOrganizationError(data: unknown): boolean {
  return !!data && typeof data === 'object' && 'organization' in data
}

export const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    const organizationId = tenantStore.get()
    if (organizationId !== null) {
      config.headers['X-Organization-Id'] = String(organizationId)
    }
  }
  return config
})

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStore.getRefresh()
  if (!refresh) throw new Error('no refresh token')
  const res = await axios.post('/api/auth/token/refresh/', { refresh })
  const access: unknown = res.data?.access
  if (typeof access !== 'string' || !access.trim()) {
    throw new Error('invalid access token')
  }
  const rotated: unknown = res.data?.refresh
  tokenStore.set(
    access,
    typeof rotated === 'string' && rotated.trim() ? rotated : undefined,
  )
  return access
}

function redirectToLogin(): void {
  try {
    const path = `${window.location.pathname}${window.location.search}`
    window.location.href = path.startsWith('/login')
      ? '/login'
      : `/login?from=${encodeURIComponent(path)}`
  } catch {
    window.location.href = '/login'
  }
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
        tenantStore.set(null)
        redirectToLogin()
        return Promise.reject(error)
      }
    }

    // Kutubxona tanlanmagan: backend 400 {"organization": "..."} qaytaradi.
    // Import halqasidan qochish uchun tanlagich bu yengil bus orqali ogohlantiriladi.
    if (error.response?.status === 400 && hasOrganizationError(error.response.data)) {
      notifyTenantRequired()
    }

    // Faqat haqiqiy server xatolari (5xx) avtomatik hisobotga yuboriladi.
    // 4xx — foydalanuvchi xatosi (masalan noto'g'ri parol), ular shovqin bo'lardi.
    // Xatolik xabari endpointi ham shu interceptor'dan o'tadi, shuning uchun
    // uni istisno qilamiz (aks holda o'z-o'zini yuborish halqasi yuz beradi).
    const url = error.config?.url || ''
    if (error.response && error.response.status >= 500 && !url.includes('xatolik-xabari')) {
      avtomatikXatolikniYubor(
        `${error.config?.method?.toUpperCase() || 'GET'} ${url}: ${error.response.status}`,
      )
    }

    return Promise.reject(error)
  },
)

/** DRF xato tanasidan (string, array yoki ichma-ich object) matn ajratadi. */
function xabarniAjrat(qiymat: unknown, chuqurlik = 0): string | null {
  if (typeof qiymat === 'string') return qiymat.trim() || null
  if (Array.isArray(qiymat)) {
    for (const element of qiymat) {
      const topilgan = xabarniAjrat(element, chuqurlik + 1)
      if (topilgan) return topilgan
    }
    return null
  }
  if (qiymat && typeof qiymat === 'object' && chuqurlik < 3) {
    const obyekt = qiymat as Record<string, unknown>
    for (const kalit of ['detail', 'error', 'message', 'organization']) {
      if (kalit in obyekt) {
        const topilgan = xabarniAjrat(obyekt[kalit], chuqurlik + 1)
        if (topilgan) return topilgan
      }
    }
    for (const qiymat2 of Object.values(obyekt)) {
      const topilgan = xabarniAjrat(qiymat2, chuqurlik + 1)
      if (topilgan) return topilgan
    }
  }
  return null
}

export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const topilgan = xabarniAjrat(err.response?.data)
    if (topilgan) return topilgan
    if (err.response) {
      return `Server xatosi (${err.response.status}). Keyinroq urinib ko'ring.`
    }
    if (err.message) return err.message
  }
  if (err instanceof Error) return err.message
  return "Noma'lum xatolik yuz berdi"
}
