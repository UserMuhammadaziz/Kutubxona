import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { loansApi, statsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { Button, Card, EmptyState, ErrorState, PageHeader, Spinner } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'

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

export function Dashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.dashboard,
  })
  const top = useQuery({ queryKey: ['stats', 'top-books'], queryFn: () => statsApi.topBooks(5) })
  const recent = useQuery({ queryKey: ['loans', 'recent'], queryFn: () => loansApi.list({ page: 1 }) })

  if (isLoading) return <Spinner label="Statistika yuklanmoqda..." />

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

  const topBooks = top.data ?? []
  const recentLoans = (recent.data?.results ?? []).slice(0, 6)

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" subtitle="Bugungi holat" />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:max-w-md">
        <Link to="/loans?berish=1">
          <Button className="w-full py-3">Kitob berish</Button>
        </Link>
        <Link to="/loans?holat=faol">
          <Button variant="secondary" className="w-full py-3">
            Qaytarib olish
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Link to="/loans?kechikkan=1" className="block">
          <StatCard label="Muddati o'tgan" value={data.muddati_otgan_berishlar} hint="qaytarilmagan berishlar" tone={data.muddati_otgan_berishlar ? 'red' : undefined} />
        </Link>
        <Link to="/reservations" className="block">
          <StatCard label="Navbatda" value={data.faol_navbatlar} hint="kutayotgan o'quvchilar" />
        </Link>
        <Link to="/fines" className="block">
          <StatCard label="Umumiy qarz" value={formatMoney(data.umumiy_qarz)} hint="to'lanmagan jarimalar summasi" tone={data.umumiy_qarz ? 'amber' : undefined} />
        </Link>
        <Link to="/fines" className="block">
          <StatCard label="To'lanmagan jarimalar" value={data.tolanmagan_jarimalar_soni} hint="ta jarima" tone={data.tolanmagan_jarimalar_soni ? 'amber' : undefined} />
        </Link>
        <Link to="/books" className="block">
          <StatCard label="Jami kitoblar" value={data.jami_kitoblar} hint="nomdagi kitoblar" />
        </Link>
        <Link to="/copies" className="block">
          <StatCard label="Jami nusxalar" value={data.jami_nusxalar} hint="fonddagi barcha nusxalar" />
        </Link>
        <Link to="/copies" className="block">
          <StatCard label="Javonda" value={data.mavjud_nusxalar} hint="berishga tayyor nusxalar" />
        </Link>
        <Link to="/loans?holat=faol" className="block">
          <StatCard label="Berilgan" value={data.berilgan_nusxalar} hint="o'quvchilarda turgan nusxalar" />
        </Link>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel title="So‘nggi harakatlar" to="/loans">
          {recent.isLoading ? (
            <Spinner label="Yuklanmoqda..." className="py-4" />
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

        <Panel title="Eng ko‘p o‘qilgan kitoblar" to="/books">
          {top.isLoading ? (
            <Spinner label="Yuklanmoqda..." className="py-4" />
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
      </div>
    </div>
  )
}
