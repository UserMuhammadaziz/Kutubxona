import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { useAuthStore, isAdmin } from '../store/auth'
import { useThemeStore } from '../store/theme'

const navItems = [
  { to: '/', label: 'Boshqaruv paneli', icon: '📊', end: true },
  { to: '/books', label: 'Kitoblar', icon: '📚' },
  { to: '/copies', label: 'Nusxalar', icon: '📦' },
  { to: '/readers', label: "O'quvchilar", icon: '🎓' },
  { to: '/teachers', label: "O'qituvchilar", icon: '👩‍🏫' },
  { to: '/applications', label: 'Arizalar', icon: '📋' },
  { to: '/loans', label: 'Berish / Qaytarish', icon: '🔄' },
  { to: '/reservations', label: 'Navbatlar', icon: '⏳' },
  { to: '/fines', label: 'Jarimalar', icon: '💰' },
]

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuthStore()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    clsx(
      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
      isActive
        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
        : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700',
    )

  return (
    <nav className="flex-1 space-y-1 overflow-y-auto p-3">
      {navItems.map((item) => (
        <NavLink key={item.to} to={item.to} end={item.end} className={linkClass} onClick={onNavigate}>
          <span aria-hidden>{item.icon}</span>
          {item.label}
        </NavLink>
      ))}
      {isAdmin(user) && (
        <NavLink to="/staff" className={linkClass} onClick={onNavigate}>
          <span aria-hidden>🛡️</span>
          Xodimlar
        </NavLink>
      )}
    </nav>
  )
}

function UserBlock({ onLogout }: { onLogout: () => void }) {
  const { user } = useAuthStore()
  return (
    <div className="border-t border-slate-200 p-4 dark:border-slate-700">
      <div className="mb-2 min-w-0 text-sm">
        <div className="truncate font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</div>
        <div className="text-slate-500 dark:text-slate-400">
          {user?.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}
        </div>
      </div>
      <button
        onClick={onLogout}
        className="w-full rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
      >
        Chiqish
      </button>
    </div>
  )
}

export function Layout() {
  const { logout } = useAuthStore()
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggle)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()
  const [oldindanYol, setOldindanYol] = useState(location.pathname)

  // Sahifa almashganda mobil yon panel yopiladi. Effect ichida setState
  // qilish qo'shimcha render va "set-state-in-effect" ogohlantirishiga
  // olib keladi, shuning uchun holat render paytida yangilanadi.
  if (oldindanYol !== location.pathname) {
    setOldindanYol(location.pathname)
    if (drawerOpen) setDrawerOpen(false)
  }

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [drawerOpen])

  return (
    <div className="min-h-screen bg-canvas dark:bg-slate-900">
      {/* Mobil yuqori panel */}
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-200 bg-paper px-4 py-3 lg:hidden dark:border-slate-700 dark:bg-slate-800">
        <button
          onClick={() => setDrawerOpen(true)}
          aria-label="Menyuni ochish"
          className="rounded-lg p-2 text-xl text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          ☰
        </button>
        <span className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
          <span aria-hidden>📖</span>
          Kutubxona
        </span>
        <button
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
          className="rounded-lg p-2 text-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </header>

      <div className="flex">
        {/* Desktop yon panel */}
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-slate-200 bg-paper lg:flex dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <span className="text-xl" aria-hidden>
                📖
              </span>
              <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">Kutubxona</span>
            </div>
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
              title={theme === 'dark' ? 'Yorug' : "Qorong'i"}
              className="rounded-lg p-2 text-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
          <NavList />
          <UserBlock onLogout={logout} />
        </aside>

        {/* Mobil yon panel (drawer) */}
        {drawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="absolute inset-0 bg-slate-900/50 dark:bg-slate-950/70"
              onClick={() => setDrawerOpen(false)}
            />
            <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-paper shadow-xl dark:bg-slate-800">
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3.5 dark:border-slate-700">
                <span className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
                  <span aria-hidden>📖</span>
                  Kutubxona
                </span>
                <button
                  onClick={() => setDrawerOpen(false)}
                  aria-label="Menyuni yopish"
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  ✕
                </button>
              </div>
              <NavList onNavigate={() => setDrawerOpen(false)} />
              <UserBlock onLogout={logout} />
            </div>
          </div>
        )}

        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
