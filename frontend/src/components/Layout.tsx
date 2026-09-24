import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { useAuthStore, isAdmin } from '../store/auth'
import { useThemeStore } from '../store/theme'

const navItems = [
  { to: '/', label: 'Boshqaruv paneli', icon: '📊', end: true },
  { to: '/books', label: 'Kitoblar', icon: '📚' },
  { to: '/copies', label: 'Nusxalar', icon: '📦' },
  { to: '/readers', label: "O'quvchilar", icon: '🎓' },
  { to: '/loans', label: 'Berish / Qaytarish', icon: '🔄' },
  { to: '/reservations', label: 'Navbatlar', icon: '⏳' },
  { to: '/fines', label: 'Jarimalar', icon: '💰' },
]

export function Layout() {
  const { user, logout } = useAuthStore()
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggle)

  return (
    <div className="flex min-h-screen bg-canvas dark:bg-slate-900">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-paper dark:border-slate-700 dark:bg-slate-800">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <span className="text-xl">📖</span>
            <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">Kutubxona</span>
          </div>
          <button
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Yorug' : "Qorong'i"}
            className="rounded-lg p-2 text-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700',
                )
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
          {isAdmin(user) && (
            <NavLink
              to="/staff"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700',
                )
              }
            >
              <span>🛡️</span>
              Xodimlar
            </NavLink>
          )}
        </nav>
        <div className="border-t border-slate-200 p-4 dark:border-slate-700">
          <div className="mb-2 text-sm">
            <div className="font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</div>
            <div className="text-slate-500 dark:text-slate-400">{user?.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}</div>
          </div>
          <button
            onClick={logout}
            className="w-full rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
          >
            Chiqish
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-x-hidden p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}
