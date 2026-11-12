import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, Eye, EyeOff, Loader2, Lock, User, Users, Clock, BarChart3 } from 'lucide-react'
import { useAuthStore } from '../store/auth'
import { errorMessage } from '../api/client'
import { ErrorBanner } from '../components/ui'
import { LogoMark } from '../components/Logo'

const FEATURES = [
  { icon: BookOpen, title: 'Fond nazorati', text: 'Kitob va nusxalar bir joyda, holati doim aniq.' },
  { icon: Users, title: 'O‘quvchilar va o‘qituvchilar', text: 'Telegram bot orqali a’zolik arizasi va bildirishnomalar.' },
  { icon: Clock, title: 'Muddat va jarimalar', text: 'Qaytarish muddati kuzatiladi, eslatmalar avtomatik.' },
  { icon: BarChart3, title: 'Statistika', text: 'Eng ko‘p o‘qilgan kitoblar va faollik hisoboti.' },
]

const inputCls =
  'w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-3 text-[15px] text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-brand-400 dark:focus:ring-brand-900/60'

export function Login() {
  const { status, login } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Foydalanuvchi kirishdan keyin kutayotgan sahifaga qaytadi. Manba
  // ikkalida bo'lishi mumkin: `?from=` (RequireAuth) yoki `state.from`.
  const params = new URLSearchParams(location.search)
  const from =
    params.get('from') ?? (location.state as { from?: string } | null)?.from ?? '/'

  if (status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      {/* Brend paneli */}
      <aside className="relative flex flex-col justify-between overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 px-6 py-8 text-white sm:px-10 lg:px-14 lg:py-12">
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-6 -right-4 h-64 w-auto text-white/[0.07] lg:h-[26rem]"
          viewBox="0 0 320 260"
          fill="currentColor"
        >
          <rect x="10" y="60" width="38" height="200" rx="4" />
          <rect x="56" y="20" width="44" height="240" rx="4" />
          <rect x="108" y="80" width="34" height="180" rx="4" />
          <rect x="150" y="40" width="48" height="220" rx="4" />
          <rect x="206" y="100" width="36" height="160" rx="4" />
          <rect x="250" y="55" width="52" height="205" rx="4" transform="rotate(8 276 260)" />
        </svg>

        <div className="relative flex items-center gap-3">
          <LogoMark className="h-10 w-10 shadow-lg shadow-black/20" />
          <span className="text-lg font-semibold tracking-tight">Kutubxona</span>
        </div>

        <div className="relative my-10 max-w-lg lg:my-0">
          <h1 className="font-['Cormorant_Garamond',serif] text-4xl font-semibold leading-[1.1] sm:text-5xl lg:text-6xl">
            Kitoblaringiz tartibda,
            <br />
            o‘quvchilaringiz xotirjam.
          </h1>
          <p className="mt-4 max-w-md text-base text-brand-100/90">
            Maktab va jamoat kutubxonalari uchun yagona boshqaruv paneli.
          </p>
          <ul className="mt-8 hidden gap-4 sm:grid sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15">
                  <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
                </span>
                <span>
                  <span className="block text-sm font-semibold">{title}</span>
                  <span className="block text-[13px] leading-snug text-brand-100/80">{text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative hidden text-xs text-brand-100/60 lg:block">
          © {new Date().getFullYear()} Kutubxona tizimi
        </p>
      </aside>

      {/* Forma */}
      <main className="flex items-center justify-center bg-canvas px-5 py-10 dark:bg-slate-900 sm:px-8">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            Xush kelibsiz
          </h2>
          <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
            Davom etish uchun kutubxonachi hisobingizga kiring.
          </p>

          <div className="mt-6">
            <ErrorBanner message={error} />
          </div>

          <form onSubmit={onSubmit} className="mt-2 space-y-4">
            <div>
              <label htmlFor="login-username" className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Foydalanuvchi nomi
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="login-username"
                  autoFocus
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  placeholder="masalan: librarian_1"
                  className={inputCls}
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Parol
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="login-password"
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`${inputCls} pr-12`}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  aria-label={showPass ? 'Parolni yashirish' : 'Parolni ko‘rsatish'}
                  className="absolute right-1.5 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-lg text-slate-400 transition hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {showPass ? <EyeOff className="h-[18px] w-[18px]" /> : <Eye className="h-[18px] w-[18px]" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-3 text-[15px] font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.99] disabled:opacity-60"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              {loading ? 'Kirilmoqda...' : 'Kirish'}
            </button>
          </form>

          <Link
            to="/yordam"
            className="mt-6 flex items-center justify-center gap-2 text-sm font-medium text-brand-700 transition hover:text-brand-800 dark:text-brand-300"
          >
            <BookOpen className="h-4 w-4" aria-hidden="true" />
            Tizimdan foydalanish qo‘llanmasi
          </Link>
        </div>
      </main>
    </div>
  )
}
