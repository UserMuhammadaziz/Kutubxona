import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { statsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Card, EmptyState, ErrorState, PageHeader, Spinner } from '../components/ui'
import { formatMoney } from '../lib/format'

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: 'red' | 'amber' }) {
  return (
    <Card className="p-5">
      <div className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</div>
      <div
        className={
          'mt-2 text-3xl font-semibold ' +
          (tone === 'red' ? 'text-red-600 dark:text-red-400' : tone === 'amber' ? 'text-amber-600 dark:text-amber-400' : 'text-slate-900 dark:text-slate-100')
        }
      >
        {value}
      </div>
    </Card>
  )
}

export function Dashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.dashboard,
  })
  const {
    data: topBooks,
    isLoading: topLoading,
    isError: topError,
    error: topErr,
    refetch: refetchTop,
    isFetching: topFetching,
  } = useQuery({
    queryKey: ['stats', 'top-books'],
    queryFn: () => statsApi.topBooks(10),
  })

  if (isLoading) return <Spinner label="Statistika yuklanmoqda..." />

  if (isError || !data) {
    return (
      <div>
        <PageHeader title="Boshqaruv paneli" subtitle="Kutubxona holati bo'yicha umumiy ko'rsatkichlar" />
        <ErrorState
          title="Statistikani yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" subtitle="Kutubxona holati bo'yicha umumiy ko'rsatkichlar" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jami kitoblar" value={data.jami_kitoblar} />
        <StatCard label="Jami nusxalar" value={data.jami_nusxalar} />
        <StatCard label="Mavjud nusxalar" value={data.mavjud_nusxalar} />
        <StatCard label="Berilgan nusxalar" value={data.berilgan_nusxalar} />
        <Link to="/loans" className="block">
          <StatCard label="Muddati o'tgan berishlar" value={data.muddati_otgan_berishlar} tone="red" />
        </Link>
        <Link to="/reservations" className="block">
          <StatCard label="Faol navbatlar" value={data.faol_navbatlar} />
        </Link>
        <Link to="/fines" className="block">
          <StatCard label="To'lanmagan jarimalar" value={data.tolanmagan_jarimalar_soni} tone="amber" />
        </Link>
        <Link to="/fines" className="block">
          <StatCard label="Umumiy qarzdorlik" value={formatMoney(data.umumiy_qarz)} tone="amber" />
        </Link>
      </div>

      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Eng ko'p o'qilgan kitoblar</h2>
        <Card className="p-4">
          {topLoading && <Spinner label="Ro‘yxat yuklanmoqda..." className="py-4" />}
          {topError && (
            <ErrorState
              title="Kitoblar ro‘yxatini yuklab bo‘lmadi"
              message={errorMessage(topErr)}
              onRetry={() => void refetchTop()}
              retrying={topFetching}
            />
          )}
          {!topLoading && !topError && !topBooks?.length && (
            <EmptyState
              icon="📚"
              title="Hali hech qanday kitob berilmagan"
              description="Berish/qaaytarish bo‘limidan kitoblar berilgach, eng o‘qilganlar shu yerda ko‘rinadi."
            />
          )}
          {!topLoading && !topError && !!topBooks?.length && (
            <ol className="divide-y divide-slate-100 dark:divide-slate-700">
              {topBooks.map((b, i) => (
                <li key={b.id} className="flex items-center justify-between py-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-50 text-sm font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                      {i + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="truncate font-medium text-slate-900 dark:text-slate-100">{b.nomi}</div>
                      <div className="text-sm text-slate-500 dark:text-slate-400">{b.muallif}</div>
                    </div>
                  </div>
                  <div className="ml-3 shrink-0 text-sm font-medium text-slate-600 dark:text-slate-300">
                    {b.berishlar_soni} marta
                  </div>
                </li>
              ))}
            </ol>
          )}
        </Card>
      </div>
    </div>
  )
}
