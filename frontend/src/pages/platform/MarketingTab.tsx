import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { marketingApi, type MarketingReport } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { Badge, EmptyState, ErrorState, Select, StatsSkeleton, Table } from '../../components/ui'
import { formatDateTime } from '../../lib/format'
import { bodyClass, headClass, ORG_STATUS } from './shared'

const PERIODS = [7, 30, 90, 365] as const

const SOURCE_LABELS: Record<string, string> = {
  direct: 'To‘g‘ridan-to‘g‘ri',
  unknown: 'Noma’lum (kuzatuvdan oldin)',
  google: 'Google',
  yandex: 'Yandex',
  telegram: 'Telegram',
  instagram: 'Instagram',
  facebook: 'Facebook',
  youtube: 'YouTube',
  tiktok: 'TikTok',
}
const MEDIUM_LABELS: Record<string, string> = {
  cpc: 'reklama',
  ppc: 'reklama',
  paid: 'reklama',
  organic: 'qidiruv',
  social: 'ijtimoiy tarmoq',
  referral: 'havola',
  email: 'e-mail',
  none: '',
}

const sourceLabel = (s: string) => SOURCE_LABELS[s] ?? s
const mediumLabel = (m: string) => (m in MEDIUM_LABELS ? MEDIUM_LABELS[m] : m)
const num = (n: number) => n.toLocaleString('uz-UZ')

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-paper p-4 dark:border-slate-700 dark:bg-slate-800">
      <div className="text-xs font-medium text-slate-600 dark:text-slate-300">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-slate-900 dark:text-slate-50">{value}</div>
      <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{hint}</div>
    </div>
  )
}

/** Daily visitors (bars) with signups marked on top. */
function DailyChart({ daily }: { daily: MarketingReport['daily'] }) {
  if (!daily.length) return null
  const max = Math.max(1, ...daily.map((d) => d.visitors))
  return (
    <div className="rounded-xl border border-slate-200 bg-paper p-4 dark:border-slate-700 dark:bg-slate-800">
      <div className="mb-3 flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-300">
        <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-brand-500" />Tashrif buyuruvchilar</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-accent-500" />Ro‘yxatdan o‘tganlar</span>
      </div>
      <div className="flex h-36 items-end gap-[3px]" role="img" aria-label="Kunlik tashriflar va ro‘yxatdan o‘tishlar grafigi">
        {daily.map((d) => (
          <div key={d.date} className="group relative flex h-full flex-1 flex-col justify-end" title={`${d.date}: ${d.visitors} kishi, ${d.signups} ro‘yxat`}>
            {d.signups > 0 && <span className="mx-auto mb-1 h-2 w-2 shrink-0 rounded-full bg-accent-500" />}
            <div className="min-h-[2px] rounded-t-sm bg-brand-500/80 group-hover:bg-brand-600" style={{ height: `${(d.visitors / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="mt-1.5 flex justify-between text-[11px] text-slate-500 dark:text-slate-400">
        <span>{daily[0].date}</span>
        <span>{daily[daily.length - 1].date}</span>
      </div>
    </div>
  )
}

export function MarketingTab() {
  const [days, setDays] = useState<number>(30)
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['platform', 'marketing', days],
    queryFn: () => marketingApi.report(days),
  })

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm text-slate-600 dark:text-slate-300">
          Saytga qayerdan kelishgani va kim ro‘yxatdan o‘tgani. Reklama havolalariga{' '}
          <code className="rounded bg-slate-100 px-1 text-xs dark:bg-slate-700">?utm_source=google&utm_medium=cpc&utm_campaign=nom</code> qo‘shing.
        </p>
        <Select aria-label="Davr" value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-40">
          {PERIODS.map((p) => (
            <option key={p} value={p}>{p === 365 ? 'Oxirgi 1 yil' : `Oxirgi ${p} kun`}</option>
          ))}
        </Select>
      </div>

      {isLoading ? (
        <StatsSkeleton count={4} />
      ) : isError || !data ? (
        <ErrorState title="Hisobotni olib bo‘lmadi" message={errorMessage(error)} onRetry={() => void refetch()} retrying={isFetching} />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Tashrif buyuruvchilar" value={num(data.totals.visitors)} hint={`${num(data.totals.visits)} ta tashrif`} />
            <Stat label="Ro‘yxatdan o‘tganlar" value={num(data.totals.signups)} hint="yangi tashkilot arizalari" />
            <Stat label="Tasdiqlanganlar" value={num(data.totals.approved)} hint="faol tashkilotga aylangan" />
            <Stat label="Konversiya" value={`${data.totals.conversion}%`} hint="ro‘yxat / tashrif buyuruvchi" />
          </div>

          <DailyChart daily={data.daily} />

          <section>
            <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Manbalar</h2>
            {!data.sources.length ? (
              <EmptyState title="Hali tashrif yo‘q" description="Saytga birinchi tashriflar shu yerda ko‘rinadi." />
            ) : (
              <Table>
                <thead className={headClass}>
                  <tr>
                    <th className="px-4 py-3">Manba</th>
                    <th className="px-4 py-3 text-right">Kishi</th>
                    <th className="px-4 py-3 text-right">Ro‘yxat</th>
                    <th className="px-4 py-3 text-right">Tasdiqlangan</th>
                    <th className="px-4 py-3 text-right">Konversiya</th>
                  </tr>
                </thead>
                <tbody className={bodyClass}>
                  {data.sources.map((r) => (
                    <tr key={`${r.source}|${r.medium}`}>
                      <td className="px-4 py-2.5">
                        <span className="font-medium text-slate-900 dark:text-slate-100">{sourceLabel(r.source)}</span>
                        {mediumLabel(r.medium) && <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">{mediumLabel(r.medium)}</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{num(r.visitors)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{num(r.signups)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{num(r.approved)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{r.visitors ? `${r.conversion}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </section>

          {data.campaigns.length > 0 && (
            <section>
              <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Kampaniyalar</h2>
              <Table>
                <thead className={headClass}>
                  <tr>
                    <th className="px-4 py-3">Kampaniya</th>
                    <th className="px-4 py-3">Manba</th>
                    <th className="px-4 py-3 text-right">Kishi</th>
                    <th className="px-4 py-3 text-right">Ro‘yxat</th>
                    <th className="px-4 py-3 text-right">Konversiya</th>
                  </tr>
                </thead>
                <tbody className={bodyClass}>
                  {data.campaigns.map((c) => (
                    <tr key={`${c.source}|${c.medium}|${c.campaign}`}>
                      <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-slate-100">{c.campaign}</td>
                      <td className="px-4 py-2.5 text-slate-600 dark:text-slate-300">{sourceLabel(c.source)}{c.medium ? ` / ${c.medium}` : ''}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{num(c.visitors)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{num(c.signups)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{c.visitors ? `${c.conversion}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </section>
          )}

          <section>
            <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Oxirgi ro‘yxatdan o‘tganlar</h2>
            {!data.recent_signups.length ? (
              <EmptyState title="Manbasi ma’lum ro‘yxat yo‘q" description="Kuzatuv yoqilgandan keyingi yangi tashkilotlar shu yerda chiqadi." />
            ) : (
              <Table>
                <thead className={headClass}>
                  <tr>
                    <th className="px-4 py-3">Tashkilot</th>
                    <th className="px-4 py-3">Birinchi manba</th>
                    <th className="px-4 py-3">Oxirgi manba</th>
                    <th className="px-4 py-3">Sana</th>
                  </tr>
                </thead>
                <tbody className={bodyClass}>
                  {data.recent_signups.map((s) => {
                    const st = ORG_STATUS[s.status as keyof typeof ORG_STATUS]
                    return (
                      <tr key={s.organization_id}>
                        <td className="px-4 py-2.5">
                          <div className="font-medium text-slate-900 dark:text-slate-100">{s.organization_name}</div>
                          {st && <Badge tone={st.tone}>{st.label}</Badge>}
                        </td>
                        <td className="px-4 py-2.5">
                          {sourceLabel(s.source)}
                          {s.medium && s.medium !== 'none' && <span className="text-slate-500 dark:text-slate-400"> / {s.medium}</span>}
                          {s.campaign && <div className="text-xs text-slate-500 dark:text-slate-400">{s.campaign}</div>}
                        </td>
                        <td className="px-4 py-2.5 text-slate-600 dark:text-slate-300">
                          {sourceLabel(s.last_source)}{s.last_medium && s.last_medium !== 'none' ? ` / ${s.last_medium}` : ''}
                        </td>
                        <td className="px-4 py-2.5 whitespace-nowrap">{formatDateTime(s.created_at)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </Table>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
