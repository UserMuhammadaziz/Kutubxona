import clsx from 'clsx'
import { Building2, Check, MapPin, Phone, LogOut, Type, Moon, Sun, User as UserIcon } from 'lucide-react'
import { Card, PageHeader } from '../components/ui'
import { useOrganization } from '../hooks/useOrganization'
import { useAuthStore } from '../store/auth'
import { FONT_SIZES, useFontSizeStore } from '../store/fontSize'
import { useThemeStore } from '../store/theme'

const TURI: Record<string, string> = {
  library: 'Kutubxona',
  school: "Maktab / ta'lim muassasasi",
  university: 'Universitet / kollej',
  office: 'Ofis / tashkilot',
  other: 'Boshqa',
}

function Row({ icon: Icon, label, value }: { icon: typeof UserIcon; label: string; value?: string }) {
  return (
    <div className="flex items-start gap-3 py-3">
      <Icon className="mt-0.5 h-5 w-5 shrink-0 text-slate-500 dark:text-slate-400" aria-hidden="true" />
      <div className="min-w-0">
        <div className="text-sm text-slate-500 dark:text-slate-400">{label}</div>
        <div className="break-words text-base font-medium text-slate-900 dark:text-slate-100">{value || '—'}</div>
      </div>
    </div>
  )
}

export function Profile() {
  const { user, logout } = useAuthStore()
  const org = useOrganization().data
  const { size, setSize } = useFontSizeStore()
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggle)

  const initials = (user?.full_name || user?.username || '?')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')

  return (
    <div className="max-w-3xl">
      <PageHeader title="Profil" subtitle="Hisobingiz, kutubxona va ko‘rinish sozlamalari" />

      <Card className="mb-4 flex items-center gap-4 p-5">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-brand-600 text-2xl font-bold text-white">
          {initials}
        </div>
        <div className="min-w-0">
          <div className="truncate text-xl font-semibold text-slate-900 dark:text-slate-100">{user?.full_name}</div>
          <div className="text-base text-slate-600 dark:text-slate-300">
            {user?.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}
          </div>
        </div>
      </Card>

      <div className="mb-4 grid gap-4 md:grid-cols-2">
        <Card className="p-5">
          <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Mening ma’lumotlarim</h2>
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            <Row icon={UserIcon} label="Foydalanuvchi nomi" value={user?.username} />
            <Row icon={Phone} label="Telefon" value={user?.telefon} />
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Kutubxonam</h2>
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            <Row icon={Building2} label="Nomi" value={org?.nomi} />
            <Row icon={Building2} label="Turi" value={org ? TURI[org.turi] ?? org.turi : undefined} />
            <Row icon={MapPin} label="Manzil" value={org?.manzil} />
            <Row icon={Phone} label="Telefon" value={org?.telefon} />
          </div>
        </Card>
      </div>

      <Card className="mb-4 p-5">
        <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
          <Type className="h-5 w-5" aria-hidden="true" /> Yozuv o‘lchami
        </h2>
        <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
          O‘zingizga qulay o‘lchamni tanlang. Tanlov shu qurilmada saqlanadi.
        </p>
        <div role="radiogroup" aria-label="Yozuv o‘lchami" className="grid gap-3 sm:grid-cols-3">
          {FONT_SIZES.map((f) => {
            const active = size === f.key
            return (
              <button
                key={f.key}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setSize(f.key)}
                className={clsx(
                  'relative rounded-xl border-2 px-4 py-4 text-left transition',
                  active
                    ? 'border-brand-600 bg-brand-50 dark:bg-brand-900/30'
                    : 'border-slate-300 hover:border-brand-400 dark:border-slate-600',
                )}
              >
                {active && (
                  <Check className="absolute right-3 top-3 h-5 w-5 text-brand-700 dark:text-brand-300" aria-hidden="true" />
                )}
                <span
                  className="block font-semibold text-slate-900 dark:text-slate-100"
                  style={{ fontSize: `${f.percent / 100 * 1.5}rem` }}
                >
                  Aa
                </span>
                <span className="mt-1 block text-base font-medium text-slate-900 dark:text-slate-100">{f.label}</span>
                <span className="block text-sm text-slate-600 dark:text-slate-300">{f.hint}</span>
              </button>
            )
          })}
        </div>
      </Card>

      <Card className="mb-4 flex items-center justify-between gap-4 p-5">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Qorong‘i rejim</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">Kechqurun ko‘zni charchatmaydi.</p>
        </div>
        <button
          type="button"
          onClick={toggleTheme}
          className="inline-flex min-h-12 items-center gap-2 rounded-lg bg-slate-100 px-4 text-base font-semibold text-slate-800 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600"
        >
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          {theme === 'dark' ? 'Yoqilgan' : 'O‘chiq'}
        </button>
      </Card>

      <button
        type="button"
        onClick={logout}
        className="inline-flex min-h-12 items-center gap-2 rounded-lg border border-red-300 px-5 text-base font-semibold text-red-700 hover:bg-red-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10"
      >
        <LogOut className="h-5 w-5" aria-hidden="true" /> Chiqish
      </button>
    </div>
  )
}
