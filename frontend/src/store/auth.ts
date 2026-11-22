import { create } from 'zustand'
import { authApi, type RegisterPayload } from '../api/resources'
import { tenantStore, tokenStore } from '../api/client'
import type { User } from '../types'

interface AuthState {
  user: User | null
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated'
  /** So'rovlarda X-Organization-Id sifatida yuboriladigan tanlangan kutubxona. */
  organizationId: number | null
  tenantPickerOpen: boolean
  login: (username: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
  hydrate: () => Promise<void>
  /** Kutubxona almashtirilgandan keyin me/joriy_rol ni yangilaydi. */
  refresh: () => Promise<void>
  setOrganizationId: (id: number | null) => void
  openTenantPicker: () => void
  closeTenantPicker: () => void
}

/**
 * Saqlangan ID hali ham foydalanuvchining faol kutubxonalari ichidami?
 * Yo'q bo'lsa (boshqa hisobga kirish, a'zolik o'chirilgan) — tozalaymiz.
 * Bitta kutubxona bo'lsa backend ham o'zi topadi, lekin header'ni oldindan
 * yuborish orqali ortiqcha 400/xatoliklarning oldini olamiz.
 */
function kutubxonaniTasdiqla(user: User | null): number | null {
  const kutubxonalar = user?.kutubxonalar ?? []
  const saqlangan = tenantStore.get()
  if (saqlangan !== null && kutubxonalar.some((k) => k.id === saqlangan)) {
    return saqlangan
  }
  if (kutubxonalar.length === 1) {
    tenantStore.set(kutubxonalar[0].id)
    return kutubxonalar[0].id
  }
  tenantStore.set(null)
  return null
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'idle',
  organizationId: tenantStore.get(),
  tenantPickerOpen: false,

  login: async (username, password) => {
    const { access, refresh } = await authApi.login(username, password)
    tokenStore.set(access, refresh)
    // Eski hisobdan qolgan tanlov qolmasligi uchun oldin tozalaymiz.
    tenantStore.set(null)
    const user = await authApi.me()
    set({ user, status: 'authenticated', organizationId: kutubxonaniTasdiqla(user), tenantPickerOpen: false })
  },

  register: async (payload) => {
    const natija = await authApi.register(payload)
    tokenStore.set(natija.access, natija.refresh)
    tenantStore.set(null)
    const user = await authApi.me()
    let organizationId = kutubxonaniTasdiqla(user)
    // Ro'yxatdan o'tishda yangi tashkilot hali PENDING bo'ladi: me.kutubxonalar
    // bo'sh bo'lsa ham, javobdagi organization id sini tanlab qo'yamiz.
    if (organizationId === null && natija.organization?.id) {
      const id = Number(natija.organization.id)
      if (Number.isInteger(id) && id > 0) {
        tenantStore.set(id)
        organizationId = id
      }
    }
    set({ user, status: 'authenticated', organizationId, tenantPickerOpen: false })
  },

  logout: () => {
    tokenStore.clear()
    tenantStore.set(null)
    set({ user: null, status: 'unauthenticated', organizationId: null, tenantPickerOpen: false })
  },

  hydrate: async () => {
    if (!tokenStore.getAccess()) {
      tenantStore.set(null)
      set({ status: 'unauthenticated', organizationId: null })
      return
    }
    set({ status: 'loading' })
    try {
      const user = await authApi.me()
      set({ user, status: 'authenticated', organizationId: kutubxonaniTasdiqla(user) })
    } catch {
      tokenStore.clear()
      tenantStore.set(null)
      set({ user: null, status: 'unauthenticated', organizationId: null })
    }
  },

  refresh: async () => {
    const user = await authApi.me()
    set((old) => ({ user, organizationId: kutubxonaniTasdiqla(user), tenantPickerOpen: old.tenantPickerOpen }))
  },

  setOrganizationId: (id) => {
    tenantStore.set(id)
    set({ organizationId: id })
  },

  openTenantPicker: () => set({ tenantPickerOpen: true }),
  closeTenantPicker: () => set({ tenantPickerOpen: false }),
}))

export const isAdmin = (user: User | null) => user?.rol === 'administrator'
