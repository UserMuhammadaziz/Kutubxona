import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { api, onTenantRequired } from '../api/client'
import { useAuthStore } from '../store/auth'
import type { Azolik, JoriyKutubxona, UserKutubxona } from '../types'
import { Icons } from './icons'
import { Badge, Button, Spinner } from './ui'

interface TenantOption extends UserKutubxona {
  holat?: string
}

const ROL_LABELS: Record<string, string> = {
  egasi: 'Egasi',
  administrator: 'Administrator',
  kutubxonachi: 'Kutubxonachi',
}

/**
 * Ko'p kutubxonaga a'zo foydalanuvchi uchun tanlagich.
 * - 2+ kutubxona va tanlov yo'q bo'lsa — butun ilovani bloklovchi modal;
 * - Profildagi «Kutubxona almashtirish» tugmasi — oddiy, yopiladigan modal.
 * Backend 400 {"organization": ...} qaytarsa, interceptor shu modarni ochadi.
 */
export function TenantSwitcher() {
  const status = useAuthStore((s) => s.status)
  const user = useAuthStore((s) => s.user)
  const organizationId = useAuthStore((s) => s.organizationId)
  const pickerOpen = useAuthStore((s) => s.tenantPickerOpen)
  const setOrganizationId = useAuthStore((s) => s.setOrganizationId)
  const closeTenantPicker = useAuthStore((s) => s.closeTenantPicker)
  const openTenantPicker = useAuthStore((s) => s.openTenantPicker)
  const refresh = useAuthStore((s) => s.refresh)
  const queryClient = useQueryClient()

  const kutubxonalar = user?.kutubxonalar
  const blocking = status === 'authenticated' && (kutubxonalar?.length ?? 0) > 1 && organizationId === null
  const open = status === 'authenticated' && (pickerOpen || blocking)
  const needsMemberships = open && !kutubxonalar?.length

  // me.kutubxonalar bo'sh bo'lsa (masalan superuser) a'zoliklar endpointidan
  // olamiz. MembershipSerializer: organization (id), organization_nomi, rol,
  // organization_status. /auth/organization/ esa OrganizationSerializer yoki null.
  const membershipsQuery = useQuery({
    queryKey: ['tenant-memberships', user?.id],
    queryFn: () =>
      api.get<Azolik[]>('/auth/memberships/').then(({ data }) => (Array.isArray(data) ? data : [])),
    enabled: needsMemberships,
  })
  const currentOrgQuery = useQuery({
    queryKey: ['tenant-current-organization', organizationId],
    queryFn: () =>
      api.get<JoriyKutubxona | null>('/auth/organization/').then(({ data }) =>
        data && typeof data === 'object' && data.id ? data : null,
      ),
    enabled: open,
    retry: false,
  })

  const options: TenantOption[] = kutubxonalar?.length
    ? kutubxonalar.map((k) => ({ ...k }))
    : (membershipsQuery.data ?? [])
        .filter((a) => a.faol !== false)
        .map((a) => ({
          id: Number(a.organization),
          nomi: a.organization_nomi || `Kutubxona #${a.organization}`,
          slug: '',
          rol: a.rol,
          holat: a.organization_status,
        }))
        .filter((k) => Number.isInteger(k.id) && k.id > 0)

  const yuklanmoqda = needsMemberships && membershipsQuery.isLoading
  const xato = needsMemberships && membershipsQuery.isError ? "Kutubxonalar ro'yxati yuklanmadi." : null
  const joriyNomi =
    organizationId !== null
      ? (options.find((k) => k.id === organizationId)?.nomi ?? currentOrgQuery.data?.nomi)
      : null

  useEffect(() => onTenantRequired(openTenantPicker), [openTenantPicker])

  useEffect(() => {
    if (!open || blocking) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeTenantPicker()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, blocking, closeTenantPicker])

  function tanla(id: number) {
    if (id !== organizationId) {
      setOrganizationId(id)
      // Yangi header bilan me/joriy_rol va barcha ma'lumotlar qayta olinadi.
      void refresh().catch(() => undefined)
      void queryClient.invalidateQueries()
    }
    closeTenantPicker()
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tenant-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-paper p-6 shadow-2xl dark:bg-slate-800">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
              <Icons.books className="h-6 w-6" />
            </span>
            <div>
              <h2 id="tenant-title" className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Kutubxona tanlang
              </h2>
              <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                Qaysi kutubxonada ishlayotganingizni belgilang.
              </p>
            </div>
          </div>
          {!blocking && (
            <button
              type="button"
              onClick={closeTenantPicker}
              aria-label="Yopish"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <Icons.close className="h-5 w-5" />
            </button>
          )}
        </div>

        {joriyNomi && (
          <p className="mb-3 rounded-lg bg-canvas px-3 py-2 text-sm text-slate-600 dark:bg-slate-900/40 dark:text-slate-300">
            Hozirgi kutubxona: <b>{joriyNomi}</b>
          </p>
        )}
        {xato && (
          <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
            {xato}
          </p>
        )}

        {yuklanmoqda ? (
          <Spinner label="Yuklanmoqda..." />
        ) : options.length ? (
          <ul className="max-h-72 space-y-2 overflow-y-auto">
            {options.map((k) => (
              <li key={k.id}>
                <button
                  type="button"
                  onClick={() => tanla(k.id)}
                  className={clsx(
                    'flex w-full items-center gap-2 rounded-xl border px-3 py-3 text-left transition-colors',
                    k.id === organizationId
                      ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/30'
                      : 'border-slate-200 hover:border-brand-300 hover:bg-brand-50/60 dark:border-slate-700 dark:hover:bg-slate-700/60',
                  )}
                >
                  <span className="min-w-0 flex-1 truncate font-medium text-slate-900 dark:text-slate-100">
                    {k.nomi}
                  </span>
                  {k.holat && k.holat !== 'active' && <Badge tone="amber">{k.holat}</Badge>}
                  {k.rol && <Badge tone="slate">{ROL_LABELS[k.rol] ?? k.rol}</Badge>}
                  {k.id === organizationId && (
                    <Icons.check className="h-5 w-5 shrink-0 text-brand-600 dark:text-brand-400" />
                  )}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-4 text-center text-sm text-slate-500 dark:text-slate-400">
            Sizga birorta faol kutubxona biriktirilmagan.
          </p>
        )}

        {!blocking && (
          <Button variant="secondary" className="mt-4 w-full" onClick={closeTenantPicker}>
            Bekor qilish
          </Button>
        )}
      </div>
    </div>
  )
}
