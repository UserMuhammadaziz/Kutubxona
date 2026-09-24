import { useQuery } from '@tanstack/react-query'
import { statsApi } from '../api/resources'
import { Card, PageHeader, Spinner } from '../components/ui'
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
  const { data, isLoading } = useQuery({ queryKey: ['stats', 'dashboard'], queryFn: statsApi.dashboard })
  const { data: topBooks } = useQuery({ queryKey: ['stats', 'top-books'], queryFn: () => statsApi.topBooks(10) })

  if (isLoading || !data) return <Spinner />

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" subtitle="Kutubxona holati bo'yicha umumiy ko'rsatkichlar" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jami kitoblar" value={data.jami_kitoblar} />
        <StatCard label="Jami nusxalar" value={data.jami_nusxalar} />
        <StatCard label="Mavjud nusxalar" value={data.mavjud_nusxalar} />
        <StatCard label="Berilgan nusxalar" value={data.berilgan_nusxalar} />
        <StatCard label="Muddati o'tgan berishlar" value={data.muddati_otgan_berishlar} tone="red" />
        <StatCard label="Faol navbatlar" value={data.faol_navbatlar} />
        <StatCard label="To'lanmagan jarimalar" value={data.tolanmagan_jarimalar_soni} tone="amber" />
        <StatCard label="Umumiy qarzdorlik" value={formatMoney(data.umumiy_qarz)} tone="amber" />
      </div>

      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Eng ko'p o'qilgan kitoblar</h2>
        <Card className="p-4">
          {!topBooks?.length && <div className="py-6 text-center text-sm text-slate-500 dark:text-slate-400">Ma'lumot yo'q</div>}
          <ol className="divide-y divide-slate-100 dark:divide-slate-700">
            {topBooks?.map((b, i) => (
              <li key={b.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-50 text-sm font-semibold text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                    {i + 1}
                  </span>
                  <div>
                    <div className="font-medium text-slate-900 dark:text-slate-100">{b.nomi}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">{b.muallif}</div>
                  </div>
                </div>
                <div className="text-sm font-medium text-slate-600 dark:text-slate-300">{b.berishlar_soni} marta</div>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </div>
  )
}
