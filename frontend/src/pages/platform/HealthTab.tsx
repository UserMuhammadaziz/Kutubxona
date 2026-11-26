import { useQuery } from '@tanstack/react-query'
import { healthApi, type HealthState } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { Badge, EmptyState, ErrorState, StatsSkeleton, Table } from '../../components/ui'
import { formatDateTime } from '../../lib/format'

const HEALTH_TONE: Record<HealthState, 'green' | 'red' | 'amber'> = { ok: 'green', down: 'red', stale: 'amber', missing: 'red' }
const HEALTH_LABEL: Record<HealthState, string> = { ok: 'Ishlayapti', down: 'Ishlamayapti', stale: 'Kechikmoqda', missing: 'Signal yo‘q' }
const COMPONENT_LABEL: Record<string, string> = {
  celery: 'Fon vazifalari (celery + beat)',
  bot_check: 'Bot tekshiruvi',
}

function ago(seconds: number | null) {
  if (seconds == null) return 'hech qachon'
  if (seconds < 90) return `${seconds} soniya oldin`
  if (seconds < 5400) return `${Math.round(seconds / 60)} daqiqa oldin`
  return `${Math.round(seconds / 3600)} soat oldin`
}

export function HealthTab() {
  const { data, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } = useQuery({
    queryKey: ['platform', 'health'],
    queryFn: healthApi.platform,
    refetchInterval: 30_000,
  })
  if (isLoading) return <StatsSkeleton count={4} />
  if (isError || !data) return <ErrorState title="Holatni olib bo‘lmadi" message={errorMessage(error)} onRetry={() => void refetch()} retrying={isFetching} />

  const items: { label: string; status: HealthState; hint: string }[] = [
    { label: 'Veb-server', status: data.web.status, hint: 'So‘rovlarga javob beryapti' },
    { label: 'Ma’lumotlar bazasi', status: data.database.status, hint: data.database.error || 'PostgreSQL' },
    { label: 'Kesh (Redis)', status: data.cache.status, hint: data.cache.error || 'Javob vaqti normal' },
    ...data.heartbeats.map((h) => ({
      label: COMPONENT_LABEL[h.name] ?? h.name,
      status: h.status,
      hint: h.status === 'missing' ? 'Hali signal kelmagan: worker/beat ishga tushirilmagan bo‘lishi mumkin' : `Oxirgi signal: ${ago(h.age_seconds)}`,
    })),
  ]
  const bad = items.filter((i) => i.status !== 'ok').length

  return (
    <div>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-300" aria-live="polite">
        {bad ? `${bad} ta komponentda muammo bor.` : 'Hamma komponent normal ishlayapti.'} Har 30 soniyada yangilanadi
        {dataUpdatedAt ? ` (${formatDateTime(new Date(dataUpdatedAt).toISOString())})` : ''}.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((i) => (
          <div key={i.label} className="rounded-xl border border-slate-200 bg-paper p-4 dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{i.label}</div>
              <Badge tone={HEALTH_TONE[i.status]}>{HEALTH_LABEL[i.status]}</Badge>
            </div>
            <div className="mt-1.5 text-xs text-slate-600 dark:text-slate-300">{i.hint}</div>
          </div>
        ))}
      </div>

      <h2 className="mb-2 mt-8 text-base font-semibold text-slate-900 dark:text-slate-100">Telegram botlar</h2>
      {!data.bots.length ? (
        <EmptyState title="Ulangan bot yo'q" description="Tashkilotlar bot ulagach shu yerda ko'rinadi." />
      ) : (
        <Table>
          <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Tashkilot</th>
              <th className="px-4 py-3">Bot</th>
              <th className="px-4 py-3">Holat</th>
              <th className="px-4 py-3">Oxirgi tekshiruv</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.bots.map((b) => {
              const good = b.state === 'ulangan' && b.webhook
              return (
                <tr key={b.organization + b.username}>
                  <td className="px-4 py-2.5">{b.organization}</td>
                  <td className="px-4 py-2.5 text-slate-600 dark:text-slate-300">{b.username ? `@${b.username}` : '—'}</td>
                  <td className="px-4 py-2.5">
                    <Badge tone={good ? 'green' : 'red'}>{good ? 'Ulangan' : b.state}</Badge>
                    {b.last_error && <div className="mt-1 text-xs text-red-600 dark:text-red-400">{b.last_error}</div>}
                  </td>
                  <td className="px-4 py-2.5 whitespace-nowrap">
                    {b.last_check ? formatDateTime(b.last_check) : 'hali tekshirilmagan'}
                    {b.stale && <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">eskirgan</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </Table>
      )}
    </div>
  )
}
