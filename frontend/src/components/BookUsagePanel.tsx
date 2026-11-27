import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import type { BookUsage, BookUsageRow } from '../api/resources'
import { formatDate } from '../lib/format'
import { Badge, Button, Card, EmptyState } from './ui'

type Key = 'popular' | 'on_loan' | 'unread' | 'never_read'

const TABS: { key: Key; label: string; empty: string }[] = [
  { key: 'popular', label: 'Ko‘p o‘qilgan', empty: 'Bu davrda kitob berilmagan' },
  { key: 'on_loan', label: 'Hozir qo‘lda', empty: 'Hozir hech kimda kitob yo‘q' },
  { key: 'unread', label: 'Davrda o‘qilmagan', empty: 'Bu davrda hamma kitob o‘qilgan' },
  { key: 'never_read', label: 'Hech o‘qilmagan', empty: 'Har bir kitob kamida bir marta berilgan' },
]

const PAGE = 30
const th = 'px-4 py-2.5 text-left font-medium'
const td = 'px-4 py-2.5 align-top'

function BookLink({ id, title, author }: { id: number; title: string; author?: string }) {
  return (
    <div>
      <Link to={`/books/${id}`} className="font-medium text-slate-900 hover:text-brand-700 hover:underline dark:text-slate-100 dark:hover:text-brand-300">
        {title}
      </Link>
      {author && <div className="text-xs text-slate-500 dark:text-slate-400">{author}</div>}
    </div>
  )
}

function Rating({ row }: { row: BookUsageRow }) {
  if (row.rating == null) return <span className="text-slate-400">—</span>
  return (
    <span className="whitespace-nowrap">
      <span className="text-amber-500">★</span> <span className="tabular-nums">{row.rating}</span>
      <span className="text-xs text-slate-500"> ({row.rating_count})</span>
    </span>
  )
}

function Table({ head, children }: { head: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
          <tr>{head.map((h) => <th key={h} className={th}>{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">{children}</tbody>
      </table>
    </div>
  )
}

/** Which books are read in the period, which are out now, and which nobody takes. */
export function BookUsagePanel({ usage }: { usage: BookUsage }) {
  const [tab, setTab] = useState<Key>('popular')
  const [all, setAll] = useState(false)
  const s = usage.summary
  const counts: Record<Key, number> = {
    popular: s.read_in_period,
    on_loan: s.on_loan,
    unread: s.unread_in_period,
    never_read: s.never_read,
  }
  const rows = usage[tab]
  const shown = all ? rows : rows.slice(0, PAGE)
  const current = TABS.find((t) => t.key === tab)!
  const share = s.total ? Math.round((s.read_in_period / s.total) * 100) : 0

  return (
    <Card className="mt-5 p-0">
      <div className="flex flex-wrap items-baseline justify-between gap-2 px-5 pt-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Kitoblar: o‘qilayotgan va o‘qilmayotgan</h2>
        <span className="text-sm text-slate-600 dark:text-slate-300">
          {s.total} ta kitobdan <b className="text-slate-900 dark:text-slate-100">{s.read_in_period}</b> tasi bu davrda o‘qildi ({share}%)
        </span>
      </div>
      <div className="mt-3 flex gap-1 overflow-x-auto border-b border-slate-200 px-3 dark:border-slate-700" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => { setTab(t.key); setAll(false) }}
            className={clsx(
              '-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium',
              tab === t.key
                ? 'border-brand-600 text-brand-700 dark:text-brand-300'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200',
            )}
          >
            {t.label} <span className="text-xs text-slate-400">{counts[t.key]}</span>
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <EmptyState title={current.empty} />
      ) : tab === 'on_loan' ? (
        <Table head={['Kitob', 'Kitobxon', 'Berilgan', 'Muddat']}>
          {usage.on_loan.slice(0, all ? undefined : PAGE).map((r, i) => (
            <tr key={`${r.book_id}-${i}`}>
              <td className={td}><BookLink id={r.book_id} title={r.title} /></td>
              <td className={td}>
                <div className="text-slate-900 dark:text-slate-100">{r.reader}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">{r.class_name || '—'}</div>
              </td>
              <td className={clsx(td, 'whitespace-nowrap')}>{formatDate(r.issued_at)}</td>
              <td className={clsx(td, 'whitespace-nowrap')}>
                {formatDate(r.due_date)} {r.late_days > 0 && <Badge tone="red">{r.late_days} kun kechikdi</Badge>}
              </td>
            </tr>
          ))}
        </Table>
      ) : (
        <Table head={tab === 'popular' ? ['Kitob', 'Berildi', 'Baho'] : tab === 'unread' ? ['Kitob', 'Oxirgi berilgan', 'Baho'] : ['Kitob', 'Qo‘shilgan']}>
          {(shown as BookUsageRow[]).map((r) => (
            <tr key={r.id}>
              <td className={td}><BookLink id={r.id} title={r.title} author={r.author} /></td>
              {tab === 'popular' && <td className={clsx(td, 'tabular-nums')}>{r.loans} marta</td>}
              {tab === 'unread' && (
                <td className={clsx(td, 'whitespace-nowrap')}>{r.last_loan ? formatDate(r.last_loan) : <Badge tone="slate">Hech qachon</Badge>}</td>
              )}
              {tab === 'never_read' ? (
                <td className={clsx(td, 'whitespace-nowrap')}>{r.added_at ? formatDate(r.added_at) : '—'}</td>
              ) : (
                <td className={td}><Rating row={r} /></td>
              )}
            </tr>
          ))}
        </Table>
      )}

      {rows.length > PAGE && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-5 py-3 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          <span>{all ? rows.length : PAGE} / {counts[tab]} ta ko‘rsatilmoqda. To‘liq ro‘yxat Excel faylda.</span>
          <Button size="sm" variant="secondary" onClick={() => setAll((v) => !v)}>
            {all ? 'Qisqartirish' : 'Hammasini ko‘rsatish'}
          </Button>
        </div>
      )}
    </Card>
  )
}
