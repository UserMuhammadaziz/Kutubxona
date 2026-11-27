import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { statsApi, type PeriodLoan, type PeriodParams, type PeriodPreset, type PeriodReport } from '../api/resources'
import { errorMessage } from '../api/client'
import { BookUsagePanel } from '../components/BookUsagePanel'
import { DatePicker } from '../components/DatePicker'
import { Icons } from '../components/icons'
import { useToast } from '../components/Toast'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, PageSkeleton, ResponsiveList, Table } from '../components/ui'
import { formatDate, formatDateTime, formatMoney } from '../lib/format'
import { useOrganization } from '../hooks/useOrganization'
import { isSchool } from '../lib/organization'

const PRESETS: { key: PeriodPreset; label: string }[] = [
  { key: 'yesterday', label: 'Kecha' },
  { key: 'today', label: 'Bugun' },
  { key: 'tomorrow', label: 'Ertaga' },
  { key: 'week', label: 'Shu hafta' },
  { key: 'month', label: 'Shu oy' },
  { key: 'custom', label: 'Boshqa davr' },
]

type ListKey = 'not_returned' | 'overdue' | 'due' | 'issued' | 'returned' | 'fines'

const TABS: { key: ListKey; label: string }[] = [
  { key: 'not_returned', label: 'Olib kelmadi' },
  { key: 'overdue', label: 'Muddati o‘tganlar' },
  { key: 'due', label: 'Qaytarilishi kerak edi' },
  { key: 'issued', label: 'Berilgan' },
  { key: 'returned', label: 'Qaytgan' },
  { key: 'fines', label: 'Jarimalar' },
]

const th = 'px-4 py-3'
const td = 'px-4 py-3 align-top'

function Stat({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: string; tone?: 'red' | 'green' | 'amber' }) {
  const color =
    tone === 'red'
      ? 'text-red-600 dark:text-red-400'
      : tone === 'green'
        ? 'text-brand-700 dark:text-brand-300'
        : tone === 'amber'
          ? 'text-amber-600 dark:text-amber-400'
          : 'text-slate-900 dark:text-slate-100'
  return (
    <Card className="p-4">
      <div className="text-sm text-slate-500 dark:text-slate-400">{label}</div>
      <div className={clsx('mt-1 text-2xl font-semibold tabular-nums', color)}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{sub}</div>}
    </Card>
  )
}

function periodTitle(report: PeriodReport) {
  const { start, end } = report.period
  return start === end ? formatDate(start) : `${formatDate(start)} — ${formatDate(end)}`
}

function StatusBadge({ loan }: { loan: PeriodLoan }) {
  if (loan.status === 'on_time') return <Badge tone="green">Vaqtida qaytardi</Badge>
  if (loan.status === 'late') return <Badge tone="amber">Kechikib qaytardi ({loan.late_days} kun)</Badge>
  if (loan.late_days > 0) return <Badge tone="red">{loan.late_days} kun kechikmoqda</Badge>
  return <Badge>Qaytarilmagan</Badge>
}

function ReminderCell({ loan, onSend, sending }: { loan: PeriodLoan; onSend: (id: number) => void; sending: boolean }) {
  const r = loan.reminder
  const state = !loan.telegram_linked ? (
    <span className="text-xs text-slate-500 dark:text-slate-400">Telegram ulanmagan</span>
  ) : r ? (
    <span className={clsx('text-xs', r.delivered ? 'text-brand-700 dark:text-brand-300' : 'text-red-600 dark:text-red-400')}>
      {r.delivered ? 'Eslatma yuborilgan' : 'Yetib bormadi'}
      {r.sent_at ? ` · ${formatDateTime(r.sent_at)}` : ''}
    </span>
  ) : (
    <span className="text-xs text-slate-500 dark:text-slate-400">Eslatma yuborilmagan</span>
  )
  return (
    <div className="flex flex-col items-start gap-1.5">
      {state}
      {loan.status === 'not_returned' && loan.telegram_linked && (
        <Button size="sm" variant="secondary" loading={sending} onClick={() => onSend(loan.id)}>
          <Icons.send className="h-3.5 w-3.5" /> Eslatma yuborish
        </Button>
      )}
    </div>
  )
}

function ReaderCell({ loan }: { loan: PeriodLoan }) {
  return (
    <div>
      <Link to={`/readers/${loan.reader_id}`} className="font-medium text-slate-900 hover:text-brand-700 dark:text-slate-100 dark:hover:text-brand-300">
        {loan.reader}
      </Link>
      <div className="text-xs text-slate-500 dark:text-slate-400">
        {[loan.class_name, loan.phone].filter(Boolean).join(' · ') || '—'}
      </div>
    </div>
  )
}

function BookCell({ loan }: { loan: PeriodLoan }) {
  return (
    <div>
      <div className="text-slate-900 dark:text-slate-100">{loan.book}</div>
      {loan.inventory_number && <div className="text-xs text-slate-500 dark:text-slate-400">№ {loan.inventory_number}</div>}
    </div>
  )
}

function LoanList({
  rows,
  mode,
  empty,
  onRemind,
  remindingId,
}: {
  rows: PeriodLoan[]
  mode: 'pending' | 'issued' | 'returned'
  empty: string
  onRemind: (id: number) => void
  remindingId: number | null
}) {
  return (
    <ResponsiveList
      items={rows}
      empty={<EmptyState title={empty} />}
      render={(loan) => (
        <div className="space-y-2 text-sm">
          <ReaderCell loan={loan} />
          <BookCell loan={loan} />
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            Muddat: {formatDate(loan.due_date)} <StatusBadge loan={loan} />
          </div>
          {mode === 'pending' && <ReminderCell loan={loan} onSend={onRemind} sending={remindingId === loan.id} />}
        </div>
      )}
    >
      <Table>
        <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
          <tr>
            <th className={th}>Kitobxon</th>
            <th className={th}>Kitob</th>
            <th className={th}>{mode === 'issued' ? 'Berilgan' : 'Muddat'}</th>
            <th className={th}>Holat</th>
            <th className={th}>{mode === 'pending' ? 'Eslatma' : mode === 'issued' ? 'Bergan xodim' : 'Qabul qilgan'}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
          {rows.map((loan) => (
            <tr key={loan.id}>
              <td className={td}><ReaderCell loan={loan} /></td>
              <td className={td}><BookCell loan={loan} /></td>
              <td className={clsx(td, 'whitespace-nowrap')}>
                {formatDate(mode === 'issued' ? loan.issued_at : loan.due_date)}
                {mode === 'issued' && <div className="text-xs text-slate-500 dark:text-slate-400">Muddat: {formatDate(loan.due_date)}</div>}
              </td>
              <td className={td}><StatusBadge loan={loan} /></td>
              <td className={td}>
                {mode === 'pending' ? (
                  <ReminderCell loan={loan} onSend={onRemind} sending={remindingId === loan.id} />
                ) : (
                  (mode === 'issued' ? loan.issued_by : loan.received_by) || '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </ResponsiveList>
  )
}

function FineList({ report }: { report: PeriodReport }) {
  const rows = [
    ...report.fines_new.map((f) => ({ ...f, kind: 'Yangi' as const })),
    ...report.fines_paid.map((f) => ({ ...f, kind: 'To‘landi' as const })),
  ]
  return (
    <ResponsiveList
      items={rows}
      getKey={(f) => `${f.kind}-${f.id}`}
      empty={<EmptyState title="Bu davrda jarima yozilmagan va to‘lanmagan" />}
      render={(f) => (
        <div className="text-sm">
          <div className="font-medium text-slate-900 dark:text-slate-100">{f.reader}</div>
          <div className="text-slate-600 dark:text-slate-300">{f.book}</div>
          <div className="mt-1 flex items-center gap-2">
            <Badge tone={f.kind === 'Yangi' ? 'amber' : 'green'}>{f.kind}</Badge> {formatMoney(f.amount)}
          </div>
        </div>
      )}
    >
      <Table>
        <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
          <tr>
            <th className={th}>Tur</th>
            <th className={th}>Kitobxon</th>
            <th className={th}>Kitob</th>
            <th className={th}>Kechikish</th>
            <th className={th}>Summa</th>
            <th className={th}>Qabul qilgan</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
          {rows.map((f) => (
            <tr key={`${f.kind}-${f.id}`}>
              <td className={td}><Badge tone={f.kind === 'Yangi' ? 'amber' : 'green'}>{f.kind}</Badge></td>
              <td className={td}>
                <div className="font-medium text-slate-900 dark:text-slate-100">{f.reader}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">{f.class_name || '—'}</div>
              </td>
              <td className={td}>{f.book}</td>
              <td className={td}>{f.late_days} kun</td>
              <td className={clsx(td, 'whitespace-nowrap tabular-nums')}>{formatMoney(f.amount)}</td>
              <td className={td}>{f.received_by || '—'}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </ResponsiveList>
  )
}

export function Statistics() {
  const qc = useQueryClient()
  const toast = useToast()
  const [preset, setPreset] = useState<PeriodPreset>('today')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [tab, setTab] = useState<ListKey>('not_returned')
  const [exporting, setExporting] = useState(false)

  const customReady = preset !== 'custom' || (start && end)
  const params: PeriodParams = preset === 'custom' ? { preset, start, end } : { preset }
  const query = useQuery({
    queryKey: ['stats-period', params],
    queryFn: () => statsApi.period(params),
    enabled: Boolean(customReady),
  })

  const remind = useMutation({
    mutationFn: (loanId: number) => statsApi.remind(loanId),
    onSuccess: () => {
      toast.success('Eslatma yuborildi')
      qc.invalidateQueries({ queryKey: ['stats-period'] })
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  const download = async () => {
    setExporting(true)
    try {
      await statsApi.exportPeriod(params)
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setExporting(false)
    }
  }

  const report = query.data
  const { data: org } = useOrganization()
  // Libraries have no classes: the debtors-by-class card is school-only.
  const library = !!org && !isSchool(org)
  const s = report?.summary
  const returned = s ? s.returned_on_time + s.returned_late : 0
  const share = s && s.due ? Math.round((returned / s.due) * 100) : 0
  const future = report ? report.period.start > report.period.today : false

  const tabCount = (key: ListKey) => {
    if (!report) return 0
    if (key === 'fines') return report.fines_new.length + report.fines_paid.length
    return report[key].length
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Statistika"
        subtitle="Kim kitob olib keldi, kim olib kelmadi, nima berildi va qancha jarima yozildi."
        actions={
          <Button variant="secondary" loading={exporting} disabled={!report} onClick={download}>
            <Icons.download className="h-4 w-4" /> Excel yuklab olish
          </Button>
        }
      />

      <Card className="flex flex-wrap items-center gap-2 p-3">
        <div className="flex flex-wrap gap-1" role="group" aria-label="Davr">
          {PRESETS.map((p) => (
            <button
              key={p.key}
              type="button"
              aria-pressed={preset === p.key}
              onClick={() => setPreset(p.key)}
              className={clsx(
                'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                preset === p.key
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700',
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
        {preset === 'custom' && (
          <div className="flex flex-wrap items-center gap-2">
            <DatePicker aria-label="Boshlanish sanasi" value={start} onChange={setStart} max={end || undefined} />
            <span className="text-slate-400">—</span>
            <DatePicker aria-label="Tugash sanasi" value={end} onChange={setEnd} min={start || undefined} />
          </div>
        )}
        {report && <span className="ml-auto text-sm text-slate-500 dark:text-slate-400">{periodTitle(report)}</span>}
      </Card>

      {!customReady ? (
        <EmptyState title="Davrni tanlang" description="Boshlanish va tugash sanasini kiriting." />
      ) : query.isLoading ? (
        <PageSkeleton stats={4} panels={1} />
      ) : query.isError || !report || !s ? (
        <ErrorState message={errorMessage(query.error)} onRetry={() => query.refetch()} />
      ) : (
        <>
          <Card className="p-5">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {future ? 'Qaytarilishi kerak' : 'Qaytarilishi kerak edi'}: {s.due} ta kitob
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">Shu davrda qaytarish muddati tugaydigan kitoblar.</p>
              </div>
              <div className="flex gap-6 text-sm">
                <div>
                  <div className="text-2xl font-semibold tabular-nums text-brand-700 dark:text-brand-300">{returned}</div>
                  <div className="text-slate-500 dark:text-slate-400">Olib keldi{s.returned_late ? ` (${s.returned_late} tasi kechikib)` : ''}</div>
                </div>
                <div>
                  <div className={clsx('text-2xl font-semibold tabular-nums', s.not_returned ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-slate-100')}>
                    {s.not_returned}
                  </div>
                  <div className="text-slate-500 dark:text-slate-400">{future ? 'Hali qaytarilmagan' : 'Olib kelmadi'}</div>
                </div>
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700" aria-hidden="true">
              <div className="h-full rounded-full bg-brand-600" style={{ width: `${share}%` }} />
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Berildi" value={s.issued} sub="kitob" />
            <Stat label="Qaytdi" value={s.returned} sub="kitob" tone="green" />
            <Stat label="Muddati o‘tganlar" value={s.overdue_total} sub="hozirgi holat, jami" tone={s.overdue_total ? 'red' : undefined} />
            <Stat label="Eslatmalar" value={s.reminders_sent} sub={`${s.reminders_delivered} tasi yetib bordi`} />
            <Stat label="Yangi jarimalar" value={formatMoney(s.fines_new_amount)} sub={`${s.fines_new_count} ta`} tone={s.fines_new_count ? 'amber' : undefined} />
            <Stat label="To‘langan jarimalar" value={formatMoney(s.fines_paid_amount)} sub={`${s.fines_paid_count} ta`} tone="green" />
            <Stat label="To‘lanmagan qarz" value={formatMoney(s.fines_unpaid_amount)} sub="jami" />
            <Stat
              label="Yangi kitobxonlar"
              value={s.new_readers}
              sub={`Arizalar: ${s.applications_new}, tasdiqlangan: ${s.applications_approved} · Navbat: ${s.reservations_new}`}
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-[1fr_18rem]">
            <div className="min-w-0 space-y-3">
              <div className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-700" role="tablist">
                {TABS.map((t) => (
                  <button
                    key={t.key}
                    type="button"
                    role="tab"
                    aria-selected={tab === t.key}
                    onClick={() => setTab(t.key)}
                    className={clsx(
                      '-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium',
                      tab === t.key
                        ? 'border-brand-600 text-brand-700 dark:text-brand-300'
                        : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200',
                    )}
                  >
                    {t.key === 'not_returned' && future ? 'Hali qaytarilmagan' : t.label}{' '}
                    <span className="text-xs text-slate-400">{tabCount(t.key)}</span>
                  </button>
                ))}
              </div>
              {tab === 'fines' ? (
                <FineList report={report} />
              ) : (
                <LoanList
                  rows={report[tab]}
                  mode={tab === 'issued' ? 'issued' : tab === 'returned' ? 'returned' : 'pending'}
                  empty={tab === 'not_returned' ? 'Hamma kitoblar qaytarilgan' : 'Bu davrda yozuv yo‘q'}
                  onRemind={(id) => remind.mutate(id)}
                  remindingId={remind.isPending ? (remind.variables ?? null) : null}
                />
              )}
            </div>

            <div className="space-y-4">
{!library && (<Card className="p-4">
                <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">Sinflar bo‘yicha qarzdorlar</h3>
                {report.by_class.length ? (
                  <ul className="space-y-1.5 text-sm">
                    {report.by_class.map((c) => (
                      <li key={c.class_name} className="flex justify-between">
                        <span className="text-slate-700 dark:text-slate-300">{c.class_name}</span>
                        <span className="font-medium tabular-nums text-red-600 dark:text-red-400">{c.overdue}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400">Muddati o‘tgan kitob yo‘q.</p>
                )}
              </Card>)}
              <Card className="p-4">
                <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">Xodimlar</h3>
                {report.by_staff.length ? (
                  <table className="w-full text-sm">
                    <thead className="text-xs text-slate-500 dark:text-slate-400">
                      <tr>
                        <th className="pb-1 text-left font-normal">Xodim</th>
                        <th className="pb-1 text-right font-normal">Berdi</th>
                        <th className="pb-1 text-right font-normal">Qabul qildi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.by_staff.map((st) => (
                        <tr key={st.name}>
                          <td className="py-0.5 text-slate-700 dark:text-slate-300">{st.name}</td>
                          <td className="py-0.5 text-right tabular-nums">{st.issued}</td>
                          <td className="py-0.5 text-right tabular-nums">{st.received}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400">Bu davrda berish yoki qabul qilish yo‘q.</p>
                )}
              </Card>
              <Card className="p-4 text-sm text-slate-600 dark:text-slate-300">
                Har kungi Excel hisobot Telegramga avtomatik yuboriladi. Vaqtini{' '}
                <Link to="/company" className="font-medium text-brand-700 hover:underline dark:text-brand-300">
                  Kutubxona profili
                </Link>{' '}
                sahifasida o‘zgartirasiz.
              </Card>
            </div>
          </div>
          {report.books && <BookUsagePanel usage={report.books} />}
        </>
      )}
    </div>
  )
}
