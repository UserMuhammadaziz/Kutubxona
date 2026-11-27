import { LogOut } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { applicationsApi, statsApi } from '../api/resources'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { useAuthStore, isAdmin } from '../store/auth'
import { useThemeStore } from '../store/theme'
import { Logo, LogoMark } from './Logo'
import { Chatbot } from './Chatbot'
import { ReportIssueButton } from './ReportIssue'
import { CommandBar } from './CommandBar'
import { Icons } from './icons'
import { canManageCompany as canManageCompanyRole, useOrganization } from '../hooks/useOrganization'
import { useOrganizationBlock } from '../hooks/useOrganizationBlock'
import { isSchool } from '../lib/organization'

type NavItem = { to: string; label: string; icon: (p: { className?: string }) => React.ReactNode; end?: boolean; badge?: 'overdue' | 'applications' }

// Grouped by how often they are used; the profile lives in the user block, not here.
const navGroups: { title: string; items: NavItem[] }[] = [
  {
    title: 'Kundalik ish',
    items: [
      { to: '/', label: 'Boshqaruv paneli', icon: Icons.dashboard, end: true },
      { to: '/loans', label: 'Berish / Qaytarish', icon: Icons.arrowsRightLeft, badge: 'overdue' },
      { to: '/books', label: 'Kitoblar', icon: Icons.books },
      { to: '/copies', label: 'Nusxalar', icon: Icons.package },
      { to: '/reservations', label: 'Navbatlar', icon: Icons.clock },
      { to: '/bandlar', label: 'Bandlar', icon: Icons.lock },
    ],
  },
  {
    title: 'Odamlar',
    items: [
      { to: '/readers', label: "O'quvchilar", icon: Icons.graduationCap },
      { to: '/teachers', label: "O'qituvchilar", icon: Icons.user },
      { to: '/kitobxonlar', label: 'Kitobxonlar', icon: Icons.users },
      { to: '/applications', label: 'Arizalar', icon: Icons.clipboardList, badge: 'applications' },
    ],
  },
  {
    title: 'Hisob va aloqa',
    items: [
      { to: '/statistics', label: 'Statistika', icon: Icons.chart },
      { to: '/fines', label: 'Jarimalar', icon: Icons.money },
      { to: '/announcements', label: 'E‘lonlar', icon: Icons.bell },
    ],
  },
]

// Kundalik ish uchun mobil pastki panel (ilova kabi): bosh sahifa, berish, kitoblar, o'quvchilar.
const tabItems = [
  { to: '/', label: 'Bosh', icon: Icons.dashboard, end: true },
  { to: '/loans', label: 'Berish', icon: Icons.arrowsRightLeft },
  { to: '/books', label: 'Kitoblar', icon: Icons.books },
  { to: '/readers', label: "O'quvchilar", icon: Icons.graduationCap },
]

/** Libraries have members, not students and teachers: relabel readers and drop the teachers page. */
function forOrgType<T extends { to: string; label: string }>(items: T[], library: boolean): T[] {
  if (!library) return items
  return items
    .filter((item) => item.to !== '/teachers')
    .map((item) => (item.to === '/readers' ? { ...item, label: "A'zolar" } : item))
}

const platformTabItems = [{ to: '/platform', label: 'Platforma', icon: Icons.shield, end: true }]

function BottomTabs({ onMenu }: { onMenu: () => void }) {
  const { user } = useAuthStore()
  const blocked = useOrganizationBlock()
  // Library tabs lead nowhere for a platform user without a usable library.
  const org = useOrganization().data
  const library = !!org && !isSchool(org)
  const items =
    user?.is_platform && (!user.kutubxonalar?.length || blocked) ? platformTabItems : forOrgType(tabItems, library)
  const tab = 'pwa-tab flex min-h-[3.25rem] min-w-0 flex-1 flex-col items-center justify-center gap-0.5 whitespace-nowrap px-0.5 text-[0.6875rem] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-500'
  return (
    <nav className="pwa-tabs fixed inset-x-0 bottom-0 z-30 flex border-t border-slate-200 bg-paper lg:hidden dark:border-slate-700 dark:bg-slate-800">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            clsx(tab, isActive ? 'text-brand-700 dark:text-brand-400' : 'text-slate-500 dark:text-slate-400')
          }
        >
          {item.icon({ className: 'h-6 w-6' })}
          {item.label}
        </NavLink>
      ))}
      <button onClick={onMenu} className={clsx(tab, 'text-slate-500 dark:text-slate-400')}>
        {Icons.menu({ className: 'h-6 w-6' })}
        Yana
      </button>
    </nav>
  )
}

function NavBadge({ count, tone }: { count: number; tone: 'red' | 'amber' }) {
  if (!count) return null
  return (
    <span
      className={clsx(
        'ml-auto min-w-[1.25rem] rounded-full px-1.5 py-0.5 text-center text-xs font-semibold tabular-nums',
        tone === 'red' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300',
      )}
      aria-label={`${count} ta`}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

function SearchTrigger({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <button
      type="button"
      onClick={() => {
        onNavigate?.()
        // CommandBar listens for Ctrl+K on window.
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))
      }}
      className="mx-3 mt-2 flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-500 transition-colors hover:border-slate-300 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
    >
      {Icons.search({ className: 'h-4 w-4' })}
      <span className="whitespace-nowrap">Qidirish</span>
      <kbd className="ml-auto hidden whitespace-nowrap rounded border border-slate-200 px-1.5 font-sans text-[11px] font-medium text-slate-400 lg:inline dark:border-slate-600">Ctrl K</kbd>
    </button>
  )
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuthStore()
  const org = useOrganization().data
  const canManageCompany = canManageCompanyRole(org)
  const library = !!org && !isSchool(org)
  // A platform-only master user belongs to no library: library pages would be empty for them.
  // Same when the selected library is blocked: only the platform pages stay usable.
  const blocked = useOrganizationBlock()
  const platformOnly = !!user?.is_platform && (!user.kutubxonalar?.length || !!blocked)
  const stats = useQuery({ queryKey: ['stats', 'dashboard'], queryFn: statsApi.dashboard, enabled: !platformOnly, staleTime: 60_000 })
  const apps = useQuery({
    queryKey: ['applications', 'pending-count'],
    queryFn: () => applicationsApi.list({ holati: 'kutmoqda' }),
    enabled: !platformOnly && isAdmin(user),
    staleTime: 60_000,
  })
  const counts = { overdue: stats.data?.muddati_otgan_berishlar ?? 0, applications: apps.data?.count ?? 0 }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    clsx(
      'relative flex min-h-9 items-center gap-3 rounded-lg px-3 py-1 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
      isActive
        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-slate-100',
    )

  const Item = ({ item }: { item: NavItem }) => (
    <NavLink to={item.to} end={item.end} className={linkClass} onClick={onNavigate}>
      {({ isActive }) => (
        <>
          {isActive && <span aria-hidden className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-brand-600 dark:bg-brand-400" />}
          <span aria-hidden>{item.icon({ className: 'h-5 w-5' })}</span>
          {item.label}
          {item.badge && <NavBadge count={counts[item.badge]} tone={item.badge === 'overdue' ? 'red' : 'amber'} />}
        </>
      )}
    </NavLink>
  )

  const manage: NavItem[] = [
    ...(user?.is_platform ? [{ to: '/platform', label: 'Platforma', icon: Icons.shield }] : []),
    ...(!platformOnly && canManageCompany ? [{ to: '/company', label: 'Kutubxona profili', icon: Icons.building }] : []),
    ...(!platformOnly && isAdmin(user) ? [{ to: '/staff', label: 'Xodimlar', icon: Icons.users }] : []),
  ]
  const groups = [
    ...(platformOnly ? [] : navGroups.map((g) => ({ ...g, items: forOrgType(g.items, library) }))),
    ...(manage.length ? [{ title: 'Boshqaruv', items: manage }] : []),
    ...(platformOnly ? [] : [{ title: 'Yordam', items: [{ to: '/guide', label: "Qo'llanma", icon: Icons.bookClosed }] as NavItem[] }]),
  ]

  return (
    <>
      {!platformOnly && <SearchTrigger onNavigate={onNavigate} />}
      <nav aria-label="Asosiy menyu" className="flex-1 overflow-y-auto px-3 pb-3 pt-1 [scrollbar-width:thin] [scrollbar-color:theme(colors.slate.300)_transparent]">
        {groups.map((g) => (
          <NavGroup key={g.title} title={g.title} items={g.items} counts={counts} Item={Item} defaultOpen={g.title !== 'Yordam'} />
        ))}
      </nav>
    </>
  )
}

const GROUPS_KEY = 'nav-groups-closed'

function readClosed(): string[] {
  try {
    return JSON.parse(localStorage.getItem(GROUPS_KEY) ?? '[]')
  } catch {
    return []
  }
}

/** Collapsible nav group. Remembers its state; always open while it holds the current page. */
function NavGroup({
  title,
  items,
  counts,
  Item,
  defaultOpen,
}: {
  title: string
  items: NavItem[]
  counts: Record<'overdue' | 'applications', number>
  Item: (p: { item: NavItem }) => React.ReactNode
  defaultOpen: boolean
}) {
  const { pathname } = useLocation()
  const [closed, setClosed] = useState(() => {
    const stored = readClosed()
    return stored.includes(title) || (!defaultOpen && !stored.includes(`+${title}`))
  })
  const holdsActive = items.some((i) => (i.end ? pathname === i.to : pathname.startsWith(i.to)))
  const open = !closed || holdsActive
  // A collapsed group still surfaces its alerts so nothing urgent hides.
  const alert = items.reduce((n, i) => n + (i.badge ? counts[i.badge] : 0), 0)

  function toggle() {
    const next = !closed
    setClosed(next)
    try {
      const rest = readClosed().filter((t) => t !== title && t !== `+${title}`)
      localStorage.setItem(GROUPS_KEY, JSON.stringify(next ? [...rest, title] : [...rest, `+${title}`]))
    } catch {
      /* storage unavailable: state stays in memory */
    }
  }

  return (
    <div className="mt-3 first:mt-1">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="flex w-full items-center gap-1 rounded-md px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:text-slate-200"
      >
        <span>{title}</span>
        {!open && alert > 0 && <span className="ml-1 h-1.5 w-1.5 rounded-full bg-red-500" aria-label="Diqqat talab qiladi" />}
        <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden className={clsx('ml-auto h-3.5 w-3.5 opacity-50 transition-transform duration-200', open && 'rotate-90')}>
          <path d="M7.3 4.3a1 1 0 0 1 1.4 0l5 5a1 1 0 0 1 0 1.4l-5 5a1 1 0 1 1-1.4-1.4L11.6 10 7.3 5.7a1 1 0 0 1 0-1.4Z" />
        </svg>
      </button>
      {open && (
        <div className="space-y-0.5">
          {items.map((item) => (
            <Item key={item.to} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

function UserBlock({
  onLogout,
  onNavigate,
  theme,
  onToggleTheme,
}: {
  onLogout: () => void
  onNavigate?: () => void
  theme?: 'light' | 'dark'
  onToggleTheme?: () => void
}) {
  const { user } = useAuthStore()
  const orgRole = useOrganization().data?.rol
  const roleLabel = user?.is_platform
    ? 'Platforma'
    : orgRole === 'egasi'
      ? 'Egasi'
      : user?.rol === 'administrator'
        ? 'Administrator'
        : 'Kutubxonachi'
  return (
    <div className="border-t border-slate-200 p-3 dark:border-slate-700">
    <div className="flex items-center gap-1">
      <NavLink
        to="/profile"
        onClick={onNavigate}
        title="Profil"
        className="flex min-w-0 flex-1 items-center gap-3 rounded-lg p-1.5 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:hover:bg-slate-700"
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
          {(user?.full_name || user?.username || '?').trim()[0]?.toUpperCase()}
        </span>
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{user?.full_name}</span>
          <span className="block truncate text-xs text-slate-500 dark:text-slate-400">{roleLabel}</span>
        </span>
      </NavLink>
      {onToggleTheme && (
        <button
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
          title={theme === 'dark' ? 'Yorug rejim' : "Qorong'i rejim"}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100"
        >
          {theme === 'dark' ? Icons.sun({ className: 'h-5 w-5' }) : Icons.moon({ className: 'h-5 w-5' })}
        </button>
      )}
    </div>
      <button
        type="button"
        onClick={onLogout}
        className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-slate-700 dark:text-slate-300 dark:hover:border-red-500/30 dark:hover:bg-red-500/10 dark:hover:text-red-300"
      >
        <LogOut className="h-4 w-4" aria-hidden="true" />
        Chiqish
      </button>
    </div>
  )
}

export function Layout() {
  const { logout } = useAuthStore()
  const org = useOrganization().data
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
    if (!drawerOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setDrawerOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [drawerOpen])

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [drawerOpen])

  return (
    <div className="min-h-dvh bg-canvas dark:bg-slate-900">
      {/* Mobil yuqori panel */}
      <header className="pwa-safe-top sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-200 bg-paper px-4 py-3 lg:hidden dark:border-slate-700 dark:bg-slate-800">
        <button
          onClick={() => setDrawerOpen(true)}
          aria-label="Menyuni ochish"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          {Icons.menu({ className: 'h-6 w-6' })}
        </button>
        <span className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
          <LogoMark className="h-6 w-6" />
          Kutubxona
        </span>
        <button
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          {theme === 'dark' ? Icons.sun({ className: 'h-6 w-6' }) : Icons.moon({ className: 'h-6 w-6' })}
        </button>
      </header>

      <div className="flex">
        {/* Desktop yon panel */}
        <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-slate-200 bg-paper lg:flex dark:border-slate-700 dark:bg-slate-800">
          <div className="border-b border-slate-200 px-5 py-3.5 dark:border-slate-700">
            <div className="flex min-w-0 items-center gap-2">
              <Logo subtitle={org?.nomi} logoUrl={org?.logo_url} />
            </div>
          </div>
          <NavList />
          <UserBlock onLogout={logout} theme={theme} onToggleTheme={toggleTheme} />
          <ReportIssueButton />
        </aside>

        {/* Mobil yon panel (drawer) */}
        {drawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Menyu">
            <div
              className="absolute inset-0 bg-slate-900/50 dark:bg-slate-950/70"
              onClick={() => setDrawerOpen(false)}
            />
            <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-paper shadow-xl dark:bg-slate-800">
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3.5 dark:border-slate-700">
                <span className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
                  <LogoMark className="h-6 w-6" />
                  Kutubxona
                </span>
                <button
                  onClick={() => setDrawerOpen(false)}
                  aria-label="Menyuni yopish"
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  {Icons.close({ className: 'h-6 w-6' })}
                </button>
              </div>
              <NavList onNavigate={() => setDrawerOpen(false)} />
              <UserBlock onLogout={logout} onNavigate={() => setDrawerOpen(false)} />
          <ReportIssueButton />
            </div>
          </div>
        )}

        {/* Bottom padding keeps page-end controls clear of the floating chatbot button. */}
        <main className="min-w-0 flex-1 p-4 pb-36 sm:p-6 sm:pb-36 lg:p-8 lg:pb-24">
          <Outlet />
        </main>
      </div>
      <BottomTabs onMenu={() => setDrawerOpen(true)} />
      <Chatbot />
      <CommandBar />
    </div>
  )
}
