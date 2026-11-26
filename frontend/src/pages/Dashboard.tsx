import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { loansApi, statsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { Card, EmptyState, ErrorState, PageHeader, ListSkeleton, PageSkeleton } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'
import { StartActions } from '../components/StartActions'
import { DASHBOARD_WIDGET_INFO, type DashboardWidget } from '../lib/organization'
import type { DashboardStats } from '../types'

function StatCard({ label, value, hint, tone }: { label: string; value: string | number; hint?: string; tone?: 'red' | 'amber' }) {
  return (
    <Card className="p-4">
      <div className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</div>
      <div
        className={
          'mt-1 text-3xl font-bold tabular-nums ' +
          (tone === 'red' ? 'text-red-600 dark:text-red-400' : tone === 'amber' ? 'text-amber-600 dark:text-amber-400' : 'text-slate-900 dark:text-slate-100')
        }
      >
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-slate-600 dark:text-slate-300">{hint}</div>}
    </Card>
  )
}

/** Bosh sahifadagi ikki ustunli blok uchun sarlavhali karta. */
function Panel({ title, to, children }: { title: string; to: string; children: React.ReactNode }) {
  return (
    <Card className="p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        <Link to={to} className="text-sm text-brand-700 hover:underline dark:text-brand-400">
          Hammasi
        </Link>
      </div>
      {children}
    </Card>
  )
}

type StatWidget = { value: (d: DashboardStats) => string | number; to?: string; tone?: (d: DashboardStats) => 'red' | 'amber' | undefined }

const STAT_WIDGETS: Partial<Record<DashboardWidget, StatWidget>> = {
  overdue_loans: { value: (d) => d.muddati_otgan_berishlar, to: '/loans?kechikkan=1', tone: (d) => (d.muddati_otgan_berishlar ? 'red' : undefined) },
  active_reservations: { value: (d) => d.faol_navbatlar, to: '/reservations' },
  total_debt: { value: (d) => formatMoney(d.umumiy_qarz), to: '/fines', tone: (d) => (Number(d.umumiy_qarz) ? 'amber' : undefined) },
  unpaid_fines: { value: (d) => d.tolanmagan_jarimalar_soni, to: '/fines', tone: (d) => (d.tolanmagan_jarimalar_soni ? 'amber' : undefined) },
  total_books: { value: (d) => d.jami_kitoblar, to: '/books' },
  total_copies: { value: (d) => d.jami_nusxalar, to: '/copies' },
  available_copies: { value: (d) => d.mavjud_nusxalar, to: '/copies' },
  issued_copies: { value: (d) => d.berilgan_nusxalar, to: '/loans?holat=faol' },
  students_count: { value: (d) => d.oquvchi_soni ?? 0, to: '/readers' },
  teachers_count: { value: (d) => d.oqituvchi_soni ?? 0, to: '/teachers' },
  members_count: { value: (d) => d.members_count ?? 0, to: '/readers' },
  pending_applications: { value: (d) => d.pending_applications ?? 0, to: '/applications', tone: (d) => (d.pending_applications ? 'amber' : undefined) },
  approved_applications: { value: (d) => d.approved_applications ?? 0, to: '/applications' },
}

const PANEL_WIDGETS: DashboardWidget[] = ['recent_activity', 'top_books', 'readers_by_class']

/** Students per class, with teachers on their own row, so totals can be read off a phone. */
function ClassBreakdown({ data }: { data: DashboardStats }) {
  const rows = data.readers_by_class ?? []
  const students = rows.reduce((sum, r) => sum + r.count, 0)
  if (!rows.length && !data.oqituvchi_soni) {
    return <EmptyState icon={<Icons.users className="h-10 w-10" />} title="Hali kitobxon yo‘q" description="Arizalar tasdiqlangach shu yerda ko‘rinadi." />
  }
  return (
    <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-700">
      {rows.map((r) => (
        <li key={r.class_name || 'none'} className="flex items-center justify-between py-2">
          <span className="text-slate-700 dark:text-slate-200">{r.class_name ? `${r.class_name.replace(/-$/, '')} sinf` : 'Sinfi ko‘rsatilmagan'}</span>
          <span className="font-semibold tabular-nums text-slate-900 dark:text-slate-100">{r.count}</span>
        </li>
      ))}
      <li className="flex items-center justify-between py-2 font-medium">
        <span className="text-slate-700 dark:text-slate-200">Jami o‘quvchilar</span>
        <span className="tabular-nums text-slate-900 dark:text-slate-100">{students}</span>
      </li>
      <li className="flex items-center justify-between py-2 font-medium">
        <span className="text-slate-700 dark:text-slate-200">O‘qituvchilar</span>
        <span className="tabular-nums text-slate-900 dark:text-slate-100">{data.oqituvchi_soni ?? 0}</span>
      </li>
    </ul>
  )
}

/** Older API responses have no `widgets`: show what the dashboard always showed. */
const LEGACY_WIDGETS: DashboardWidget[] = [
  'overdue_loans', 'active_reservations', 'total_debt', 'unpaid_fines',
  'total_books', 'total_copies', 'available_copies', 'issued_copies', 'recent_activity', 'top_books',
]

export function Dashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.dashboard,
  })
  const widgets = data?.widgets ?? LEGACY_WIDGETS
  const showTop = widgets.includes('top_books')
  const showRecent = widgets.includes('recent_activity')
  const top = useQuery({ queryKey: ['stats', 'top-books'], queryFn: () => statsApi.topBooks(5), enabled: !!data && showTop })
  const recent = useQuery({ queryKey: ['loans', 'recent'], queryFn: () => loansApi.list({ page: 1 }), enabled: !!data && showRecent })

  if (isLoading) return <PageSkeleton />

  if (isError || !data) {
    return (
      <div>
        <PageHeader title="Boshqaruv paneli" subtitle="Bugungi holat" />
        <ErrorState
          title="Statistikani yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      </div>
    )
  }

  const statKeys = widgets.filter((key) => key in STAT_WIDGETS)
  const panelKeys = widgets.filter((key) => PANEL_WIDGETS.includes(key))
  const topBooks = top.data ?? []
  const recentLoans = (recent.data?.results ?? []).slice(0, 6)

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" subtitle="Bugungi holat" />

      <StartActions data={data} />

      {statKeys.length > 0 && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {statKeys.map((key) => {
            const stat = STAT_WIDGETS[key]!
            const info = DASHBOARD_WIDGET_INFO[key]
            const card = <StatCard label={info.label} value={stat.value(data)} hint={info.hint} tone={stat.tone?.(data)} />
            return stat.to ? (
              <Link key={key} to={stat.to} className="block">
                {card}
              </Link>
            ) : (
              <div key={key}>{card}</div>
            )
          })}
        </div>
      )}

      {!widgets.length && (
        <Card className="p-6 text-center text-sm text-slate-500 dark:text-slate-400">
          Dashboard uchun widget tanlanmagan. Ularni kutubxona sozlamalarida yoqish mumkin.
        </Card>
      )}

      {panelKeys.length > 0 && (
        <div className={'mt-6 grid gap-4 ' + (panelKeys.length > 1 ? 'lg:grid-cols-2' : '')}>
          {panelKeys.map((key) => key === 'readers_by_class' ? (
          <Panel key={key} title="Sinflar bo‘yicha kitobxonlar" to="/readers">
            <ClassBreakdown data={data} />
          </Panel>
          ) : key === 'recent_activity' ? (
          <Panel key={key} title="So‘nggi harakatlar" to="/loans">
            {recent.isLoading ? (
              <ListSkeleton rows={3} />
            ) : recent.isError ? (
              <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(recent.error)} onRetry={() => void recent.refetch()} retrying={recent.isFetching} />
            ) : !recentLoans.length ? (
              <EmptyState icon={<Icons.arrowsRightLeft className="h-10 w-10" />} title="Hali harakat yo‘q" description="Kitob berilgach shu yerda ko‘rinadi." />
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-700">
                {recentLoans.map((l) => {
                  const qaytdi = !!l.qaytarilgan_sana
                  return (
                    <li key={l.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                      <div className="min-w-0">
                        <span className="font-medium text-slate-900 dark:text-slate-100">{l.oquvchi_fish}</span>{' '}
                        <span className="text-slate-500 dark:text-slate-400">
                          {qaytdi ? 'qaytardi' : 'oldi'}: {l.kitob_nomi}
                        </span>
                      </div>
                      <span className="shrink-0 text-xs text-slate-400">{formatDate(qaytdi ? l.qaytarilgan_sana : l.berilgan_sana)}</span>
                    </li>
                  )
                })}
              </ul>
            )}
          </Panel>
          ) : (
          <Panel key={key} title="Eng ko‘p o‘qilgan kitoblar" to="/books">
            {top.isLoading ? (
              <ListSkeleton rows={3} />
            ) : top.isError ? (
              <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(top.error)} onRetry={() => void top.refetch()} retrying={top.isFetching} />
            ) : !topBooks.length ? (
              <EmptyState icon={<Icons.books className="h-10 w-10" />} title="Hali kitob berilmagan" description="Kitoblar berilgach eng o‘qilganlari shu yerda ko‘rinadi." />
            ) : (
              <ol className="divide-y divide-slate-100 dark:divide-slate-700">
                {topBooks.map((b, i) => (
                  <li key={b.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                        {i + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="truncate font-medium text-slate-900 dark:text-slate-100">{b.nomi}</div>
                        <div className="truncate text-xs text-slate-500 dark:text-slate-400">{b.muallif}</div>
                      </div>
                    </div>
                    <span className="shrink-0 text-slate-600 dark:text-slate-300">{b.berishlar_soni} marta</span>
                  </li>
                ))}
              </ol>
            )}
          </Panel>
          ))}
        </div>
      )}
    </div>
  )
}
