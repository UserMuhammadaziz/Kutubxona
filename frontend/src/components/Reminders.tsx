import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { holdsApi, loansApi } from '../api/resources'

/** Ctrl+K panelida: bugun e'tibor talab qiladigan ishlar (muddati o'tganlar, kutayotgan bandlar). */
export function Reminders({ onNavigate }: { onNavigate: () => void }) {
  const overdue = useQuery({ queryKey: ['loans', 'overdue-count'], queryFn: loansApi.overdue, refetchInterval: 120_000 })
  const holds = useQuery({
    queryKey: ['holds', 'pending-count'],
    queryFn: () => holdsApi.list({ holati: 'kutmoqda' }),
    refetchInterval: 120_000,
  })
  const o = overdue.data?.length ?? 0
  const h = holds.data?.count ?? 0
  if (!o && !h) return null
  const chip =
    'rounded-full bg-white/70 px-3 py-1 font-medium hover:bg-white dark:bg-slate-900/40 dark:hover:bg-slate-900/70'
  return (
    <div
      role="status"
      className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800 dark:border-brand-900 dark:bg-brand-900/30 dark:text-brand-200"
    >
      <span className="font-semibold">Bugun:</span>
      {o > 0 && (
        <Link to="/loans?kechikkan=1" onClick={onNavigate} className={chip}>
          {o} ta kitobning muddati o‘tgan
        </Link>
      )}
      {h > 0 && (
        <Link to="/bandlar" onClick={onNavigate} className={chip}>
          {h} ta band so‘rovi tasdiqlashni kutmoqda
        </Link>
      )}
    </div>
  )
}
