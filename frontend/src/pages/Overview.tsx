import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { statsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { StartActions } from '../components/StartActions'
import { Badge, Card, EmptyState, ErrorState, PageHeader, Spinner } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'
import type { RecentActivity, TopBook } from '../types'

function StatCard({
  label,
  value,
  tone,
  sub,
}: {
  label: string
  value: string | number
  tone?: 'red' | 'amber' | 'green' | 'blue'
  sub?: string
}) {
  const rang =
    tone === 'red'
      ? 'text-red-600 dark:text-red-400'
      : tone === 'amber'
        ? 'text-amber-600 dark:text-amber-400'
        : tone === 'green'
          ? 'text-green-600 dark:text-green-400'
          : tone === 'blue'
            ? 'text-blue-600 dark:text-blue-400'
            : 'text-slate-900 dark:text-slate-100'

  return (
    <Card className="p-5">
      <div className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</div>
      <div className={`mt-2 text-3xl font-semibold ${rang}`}>{value}</div>
      {sub && (
        <div className="mt-1 truncate text-xs text-slate-500 dark:text-slate-400" title={sub}>
          {sub}
        </div>
      )}
    </Card>
  )
}

function medalTone(orin: number): 'amber' | 'blue' | 'slate' {
  if (orin === 1) return 'amber'
  if (orin === 2) return 'blue'
  return 'slate'
}

function ActivityRow({ harakat }: { harakat: RecentActivity }) {
  const Icon = harakat.turi === 'berish' ? Icons.bookOpen : Icons.checkCircle
  const iconTone =
    harakat.turi === 'berish'
      ? 'bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400'
      : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400'

  return (
    <div className="flex items-start gap-3 p-4">
      <div className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconTone}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900 dark:text-slate-100">{harakat.sarlavha}</span>
          <Badge tone={harakat.turi === 'berish' ? 'blue' : 'green'}>
            {harakat.turi === 'berish' ? 'Berish' : 'Qaytarish'}
          </Badge>
        </div>
        <div className="truncate text-sm text-slate-600 dark:text-slate-300">{harakat.tavsif}</div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
          <span className="inline-flex items-center gap-1">
            <Icons.user className="h-3.5 w-3.5" /> {harakat.xodim}
          </span>
          <span>·</span>
          <span className="inline-flex items-center gap-1">
            <Icons.clock className="h-3.5 w-3.5" /> {formatDate(harakat.vaqt)}
          </span>
        </div>
      </div>
    </div>
  )
}

function TopBookRow({ kitob, orin }: { kitob: TopBook; orin: number }) {
  return (
    <div className="flex items-center gap-3 p-4">
      <Badge tone={medalTone(orin)}>#{orin}</Badge>
      <div className="min-w-0 flex-1">
        <Link
          to={`/books/${kitob.id}`}
          className="block truncate font-semibold text-brand-700 hover:underline dark:text-brand-400"
        >
          {kitob.nomi}
        </Link>
        <div className="truncate text-sm text-slate-500 dark:text-slate-400">{kitob.muallif}</div>
      </div>
      <div className="shrink-0 text-right">
        <div className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          {kitob.berishlar_soni}
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">marta o'qilgan</div>
      </div>
    </div>
  )
}

export function Overview() {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.dashboard,
  })

  const activity = useQuery({
    queryKey: ['stats', 'recent-activity'],
    queryFn: () => statsApi.recentActivity(8),
  })

  const topBooks = useQuery({
    queryKey: ['stats', 'top-books'],
    queryFn: () => statsApi.topBooks(5),
  })

  const faollik = useQuery({
    queryKey: ['stats', 'faollik-reytingi'],
    queryFn: statsApi.faollikReytingi,
  })

  const engFaolSinf = faollik.data?.sinflar[0]
  const engFaolOqituvchi = faollik.data?.faol_oqituvchilar[0]

  return (
    <div>
      <PageHeader
        title="Boshqaruv paneli"
        subtitle="Kutubxonangizning joriy holati va asosiy ko‘rsatkichlari"
      />

      <section className="mb-8 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-800 p-8 text-white">
        <h1 className="text-3xl font-bold sm:text-4xl">Kitoblarni boshqaring</h1>
        <p className="mt-3 max-w-2xl text-sm text-white/80">
          Kitoblar, a'zolar, berish va qaytarish jarayonlarini bitta joydan kuzatib boring.
        </p>
      </section>

      {data && <StartActions data={data} />}

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
          Kutubxona statistikasi
        </h2>

        {isLoading && <Spinner label="Statistika yuklanmoqda..." />}

        {isError && (
          <ErrorState
            title="Statistikani yuklab bo‘lmadi"
            message={errorMessage(error)}
            onRetry={() => void refetch()}
            retrying={isFetching}
          />
        )}

        {data && (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Jami kitoblar" value={data.jami_kitoblar} />
            <StatCard label="Jami nusxalar" value={data.jami_nusxalar} />
            <StatCard label="Mavjud nusxalar" value={data.mavjud_nusxalar} tone="green" />
            <StatCard label="Berilgan nusxalar" value={data.berilgan_nusxalar} tone="amber" />
            <StatCard
              label="Muddati o'tgan berishlar"
              value={data.muddati_otgan_berishlar}
              tone="red"
            />
            <StatCard label="Faol navbatlar" value={data.faol_navbatlar} />
            <StatCard
              label="To'lanmagan jarimalar"
              value={data.tolanmagan_jarimalar_soni}
              tone="red"
            />
            <StatCard
              label="Umumiy qarz"
              value={formatMoney(data.umumiy_qarz)}
              tone="amber"
            />
            {data.oquvchi_soni !== undefined && (
              <StatCard label="O'quvchilar" value={data.oquvchi_soni} />
            )}
            {data.oqituvchi_soni !== undefined && (
              <StatCard label="O'qituvchilar" value={data.oqituvchi_soni} />
            )}
            <StatCard
              label="Faol sinflar"
              value={faollik.data?.sinflar.length ?? 0}
              tone="amber"
              sub={engFaolSinf ? `Eng faoli: ${engFaolSinf.sinf}-sinf` : undefined}
            />
            <StatCard
              label="Faol o'qituvchilar"
              value={faollik.data?.faol_oqituvchilar.length ?? 0}
              tone="blue"
              sub={engFaolOqituvchi ? `Eng faoli: ${engFaolOqituvchi.fish}` : undefined}
            />
          </div>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
            <Icons.clock className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            So'ngi harakatlar
          </h2>

          {activity.isLoading && <Spinner label="Harakatlar yuklanmoqda..." />}

          {activity.isError && (
            <ErrorState
              title="Harakatlarni yuklab bo‘lmadi"
              message={errorMessage(activity.error)}
              onRetry={() => void activity.refetch()}
              retrying={activity.isFetching}
            />
          )}

          {activity.data && (
            <Card className="divide-y divide-slate-100 dark:divide-slate-700">
              {activity.data.length ? (
                activity.data.map((harakat) => (
                  <ActivityRow key={harakat.id} harakat={harakat} />
                ))
              ) : (
                <div className="p-4">
                  <EmptyState
                    icon={<Icons.inbox className="h-10 w-10" />}
                    title="Hali harakat yo‘q"
                    description="Kitob berilganda yoki qaytarilganda shu yerda ko‘rinadi."
                  />
                </div>
              )}
            </Card>
          )}
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
            <Icons.books className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            Eng ko'p o'qilgan kitoblar
          </h2>

          {topBooks.isLoading && <Spinner label="Kitoblar yuklanmoqda..." />}

          {topBooks.isError && (
            <ErrorState
              title="Kitoblarni yuklab bo‘lmadi"
              message={errorMessage(topBooks.error)}
              onRetry={() => void topBooks.refetch()}
              retrying={topBooks.isFetching}
            />
          )}

          {topBooks.data && (
            <Card className="divide-y divide-slate-100 dark:divide-slate-700">
              {topBooks.data.length ? (
                topBooks.data.map((kitob, i) => (
                  <TopBookRow key={kitob.id} kitob={kitob} orin={i + 1} />
                ))
              ) : (
                <div className="p-4">
                  <EmptyState
                    icon={<Icons.inbox className="h-10 w-10" />}
                    title="Hali ma'lumot yo‘q"
                    description="Kitob berilgach, eng ko'p o'qilganlar shu yerda ko‘rinadi."
                  />
                </div>
              )}
            </Card>
          )}
        </section>
      </div>
    </div>
  )
}
