import { useState } from 'react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import { Card } from './ui'

export type SetupStep = {
  key: string
  title: string
  hint: string
  to: string
  action: string
  done: boolean
}

const DISMISS_KEY = 'setup-checklist-dismissed'

function readDismissed() {
  try {
    return localStorage.getItem(DISMISS_KEY) === '1'
  } catch {
    return false
  }
}

/** First-run guide for a new organization: shows what to do next, hides itself when finished. */
export function SetupChecklist({ steps }: { steps: SetupStep[] }) {
  const [dismissed, setDismissed] = useState(readDismissed)
  const doneCount = steps.filter((s) => s.done).length
  if (dismissed || doneCount === steps.length) return null
  const next = steps.find((s) => !s.done)

  function dismiss() {
    try {
      localStorage.setItem(DISMISS_KEY, '1')
    } catch {
      /* ignore */
    }
    setDismissed(true)
  }

  return (
    <Card className="mb-6 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Kutubxonani sozlash</h2>
          <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
            {doneCount} / {steps.length} qadam bajarildi. Keyingisi: {next?.title.toLowerCase()}.
          </p>
        </div>
        <button type="button" onClick={dismiss} className="text-sm text-slate-500 hover:text-slate-700 hover:underline dark:text-slate-400">
          Yashirish
        </button>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700" role="progressbar" aria-valuemin={0} aria-valuemax={steps.length} aria-valuenow={doneCount}>
        <div className="h-full rounded-full bg-brand-600 transition-[width] duration-500" style={{ width: `${(doneCount / steps.length) * 100}%` }} />
      </div>
      <ol className="mt-4 divide-y divide-slate-100 dark:divide-slate-700">
        {steps.map((s, i) => (
          <li key={s.key} className="flex items-center gap-3 py-3">
            <span
              className={clsx(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
                s.done ? 'bg-brand-600 text-white' : s === next ? 'bg-brand-50 text-brand-700 ring-1 ring-brand-500 dark:bg-brand-900/30 dark:text-brand-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
              )}
              aria-hidden="true"
            >
              {s.done ? (
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
              ) : (
                i + 1
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div className={clsx('text-sm font-medium', s.done ? 'text-slate-500 line-through dark:text-slate-400' : 'text-slate-900 dark:text-slate-100')}>{s.title}</div>
              {!s.done && <div className="text-xs text-slate-600 dark:text-slate-300">{s.hint}</div>}
            </div>
            {!s.done && (
              <Link
                to={s.to}
                className={clsx(
                  'shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium',
                  s === next ? 'bg-brand-600 text-white hover:bg-brand-700' : 'border border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700',
                )}
              >
                {s.action}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </Card>
  )
}
