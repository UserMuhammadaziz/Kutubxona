import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { loansApi, statsApi, telegramApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { Button, Card, EmptyState, ErrorState, PageHeader, ListSkeleton, PageSkeleton } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'
import { SetupChecklist } from '../components/SetupChecklist'
import { isAdmin, useAuthStore } from '../store/auth'

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
  const admin = isAdmin(useAuthStore((s) => s.user))
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.dashboard,
  })
  const top = useQuery({ queryKey: ['stats', 'top-books'], queryFn: () => statsApi.topBooks(5) })
  const bot = useQuery({ queryKey: ['telegram', 'settings'], queryFn: telegramApi.get, enabled: admin })
  const recent = useQuery({ queryKey: ['loans', 'recent'], queryFn: () => loansApi.list({ page: 1 }) })

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

  const topBooks = top.data ?? []
  const recentLoans = (recent.data?.results ?? []).slice(0, 6)

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" subtitle="Bugungi holat" />

      {admin && !recent.isLoading && !bot.isLoading && (
        <SetupChecklist
          steps={[
            { key: 'book', title: "Kitob qo'shing", hint: 'Kitoblar ro‘yxatiga birinchi kitobni kiriting.', to: '/books', action: "Kitob qo'shish", done: data.jami_kitoblar > 0 },
            { key: 'copy', title: "Nusxalarni qo'shing", hint: 'Berish uchun kitobning jismoniy nusxalari kerak.', to: '/copies', action: "Nusxa qo'shish", done: data.jami_nusxalar > 0 },
            { key: 'reader', title: "O'quvchi qo'shing", hint: 'Yoki o‘quvchilar Telegram bot orqali o‘zlari ariza yuboradi.', to: '/readers', action: "O'quvchi qo'shish", done: (data.oquvchi_soni || 0) > 0 },
            { key: 'bot', title: 'Telegram botni ulang', hint: 'Bot tokenini Kompaniya sahifasida kiriting.', to: '/company', action: 'Ulash', done: !!bot.data?.ulangan },
            { key: 'loan', title: 'Birinchi kitobni bering', hint: 'O‘quvchiga nusxa bering, muddat va jarima avtomatik hisoblanadi.', to: '/loans?berish=1', action: 'Kitob berish', done: (recent.data?.results?.length ?? 0) > 0 },
          ]}
        />
      )}

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

      {admin && (
        <div className="mt-3 grid grid-cols-2 gap-3">
          <StatCard label="O'quvchilar" value={data.oquvchi_soni || 0} hint="faol o'quvchilar" />
          <StatCard label="O'qituvchilar" value={data.oqituvchi_soni || 0} hint="faol o'qituvchilar" />
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel title="So‘nggi harakatlar" to="/loans">
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

        <Panel title="Eng ko‘p o‘qilgan kitoblar" to="/books">
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
      </div>
    </div>
  )
}
