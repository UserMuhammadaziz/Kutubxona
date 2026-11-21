import type { ReactNode } from 'react'
import { useAuthStore } from '../store/auth'
import { useThemeStore } from '../store/theme'
import { Icons } from '../components/icons'
import { Badge, Button, Card, PageHeader } from '../components/ui'

const ROL_LABELS: Record<string, string> = {
  egasi: 'Egasi',
  administrator: 'Administrator',
  kutubxonachi: 'Kutubxonachi',
}

function rolLabel(rol?: string | null): string {
  return (rol && ROL_LABELS[rol]) || rol || '—'
}

function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 border-b border-slate-100 py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
      <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>
      <span className="min-w-0 break-words text-sm font-medium text-slate-900 dark:text-slate-100">
        {children}
      </span>
    </div>
  )
}

/** Kutubxonachi o'z hisobi va a'zoliklarini ko'radi. */
export function Profile() {
  const { user, logout } = useAuthStore()
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggle)

  if (!user) return null

  const boshHarflar = (user.full_name || user.username || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((soz) => soz[0]?.toUpperCase() ?? '')
    .join('')

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Profil" subtitle="Kutubxonachi hisobi haqidagi ma'lumotlar" />

      <Card className="mb-5 overflow-hidden">
        <div className="flex flex-col items-start gap-4 bg-gradient-to-r from-brand-50 to-transparent p-6 sm:flex-row sm:items-center dark:from-brand-900/20">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xl font-semibold text-white">
            {boshHarflar || '?'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-xl font-semibold text-slate-900 dark:text-slate-100">
              {user.full_name || user.username}
            </div>
            <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">@{user.username}</div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={user.rol === 'administrator' ? 'blue' : 'green'}>
              {rolLabel(user.rol)}
            </Badge>
            <Badge tone={user.is_active ? 'green' : 'red'}>
              {user.is_active ? 'Faol' : 'Bloklangan'}
            </Badge>
          </div>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="p-5">
          <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
            <Icons.idCard className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            Shaxsiy ma'lumotlar
          </h2>
          <InfoRow label="To'liq ism">{user.full_name || '—'}</InfoRow>
          <InfoRow label="Foydalanuvchi nomi">@{user.username}</InfoRow>
          <InfoRow label="Telefon raqam">{user.telefon || '—'}</InfoRow>
          <InfoRow label="Tizimdagi roli">{rolLabel(user.rol)}</InfoRow>
          <InfoRow label="Joriy kutubxonadagi roli">{rolLabel(user.joriy_rol)}</InfoRow>
        </Card>

        <div className="flex flex-col gap-5">
          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <Icons.users className="h-5 w-5 text-brand-600 dark:text-brand-400" />
              Kutubxonalarim
            </h2>
            {user.kutubxonalar?.length ? (
              <ul className="space-y-2">
                {user.kutubxonalar.map((k) => (
                  <li
                    key={k.id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700"
                  >
                    <span className="min-w-0 truncate text-sm font-medium text-slate-800 dark:text-slate-200">
                      {k.nomi}
                    </span>
                    <Badge tone={k.rol === 'egasi' ? 'amber' : 'slate'}>{rolLabel(k.rol)}</Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Hech qanday kutubxonaga bog'lanmagansiz.
              </p>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <Icons.info className="h-5 w-5 text-brand-600 dark:text-brand-400" />
              Sozlamalar
            </h2>
            <div className="flex flex-col gap-2">
              <Button variant="secondary" onClick={toggleTheme} className="w-full !justify-start">
                {theme === 'dark' ? Icons.sun({ className: 'h-4 w-4' }) : Icons.moon({ className: 'h-4 w-4' })}
                {theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
              </Button>
              <Button variant="secondary" onClick={logout} className="w-full !justify-start">
                <Icons.close className="h-4 w-4" />
                Tizimdan chiqish
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
