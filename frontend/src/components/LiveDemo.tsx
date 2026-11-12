import { useState } from 'react'
import clsx from 'clsx'

/*
 * Landing preview: a small working copy of the dashboard and the loans screen.
 * Pure local state, no API calls. Uses the same tokens as the real app, so it
 * stays in sync with the design instead of going stale like a screenshot.
 */

interface Loan {
  id: number
  book: string
  reader: string
  daysLeft: number // negative = overdue
  returned: boolean
}

const FINE_PER_DAY = 5000

const SEED: Loan[] = [
  { id: 1, book: 'O‘tkan kunlar', reader: 'Dilnoza Karimova', daysLeft: -6, returned: false },
  { id: 2, book: 'Sarob', reader: 'Aziz Rahimov', daysLeft: -2, returned: false },
  { id: 3, book: 'Dunyoning ishlari', reader: 'Malika Tursunova', daysLeft: 5, returned: false },
  { id: 4, book: 'Matematika 5-sinf', reader: 'Jasur Aliyev', daysLeft: 9, returned: false },
]

const TOTAL_COPIES = 24

export function LiveDemo() {
  const [tab, setTab] = useState<'panel' | 'loans'>('panel')
  const [loans, setLoans] = useState(SEED)
  const [last, setLast] = useState<string | null>(null)

  const active = loans.filter((l) => !l.returned)
  const overdue = active.filter((l) => l.daysLeft < 0)
  const debt = overdue.reduce((s, l) => s + -l.daysLeft * FINE_PER_DAY, 0)

  function giveBack(l: Loan) {
    setLoans(loans.map((x) => (x.id === l.id ? { ...x, returned: true } : x)))
    setLast(
      l.daysLeft < 0
        ? `${l.book} qaytdi. Jarima: ${(-l.daysLeft * FINE_PER_DAY).toLocaleString('uz-UZ')} so‘m`
        : `${l.book} qaytdi. Jarima yo‘q`,
    )
  }

  const stats = [
    { label: 'Muddati o‘tgan', value: overdue.length, tone: overdue.length ? 'text-red-600' : 'text-slate-900' },
    { label: 'Qarz', value: `${debt.toLocaleString('uz-UZ')} so‘m`, tone: debt ? 'text-amber-600' : 'text-slate-900' },
    { label: 'Javonda', value: TOTAL_COPIES - active.length, tone: 'text-slate-900' },
    { label: 'O‘quvchilarda', value: active.length, tone: 'text-slate-900' },
  ]

  return (
    <div className="overflow-hidden rounded-[16px] bg-canvas text-left text-slate-900 shadow-sm">
      {/* window bar */}
      <div className="flex items-center gap-1.5 border-b border-slate-200 bg-paper px-3 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="ml-3 text-xs text-slate-500">Namuna. Bosib ko‘ring, hech narsa saqlanmaydi</span>
      </div>

      <div className="grid sm:grid-cols-[11rem_1fr]">
        <nav className="flex gap-1 border-b border-slate-200 bg-paper p-2 sm:flex-col sm:border-b-0 sm:border-r" aria-label="Namuna bo‘limlari">
          {(
            [
              ['panel', 'Boshqaruv paneli'],
              ['loans', 'Berish / Qaytarish'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              aria-pressed={tab === id}
              className={clsx(
                'rounded-lg px-3 py-2 text-left text-sm font-medium transition',
                tab === id ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100',
              )}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="min-h-[19rem] p-4 sm:p-5">
          {tab === 'panel' ? (
            <>
              <h3 className="text-lg font-semibold">Boshqaruv paneli</h3>
              <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
                {stats.map((s) => (
                  <div key={s.label} className="rounded-xl border border-slate-200 bg-paper p-3">
                    <div className="text-xs text-slate-500">{s.label}</div>
                    <div className={clsx('mt-1 text-xl font-bold tabular-nums', s.tone)}>{s.value}</div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm text-slate-600">
                Raqamlar jonli. “Berish / Qaytarish” bo‘limiga o‘tib, kitobni qaytaring. Bu yerda hammasi o‘zgaradi.
              </p>
              <button
                onClick={() => setTab('loans')}
                className="mt-3 rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
              >
                Kitob qaytarib ko‘rish
              </button>
            </>
          ) : (
            <>
              <h3 className="text-lg font-semibold">Berish / Qaytarish</h3>
              <ul className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-paper">
                {active.length === 0 && <li className="p-4 text-sm text-slate-500">Hammasi qaytdi.</li>}
                {active.map((l) => (
                  <li key={l.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{l.book}</div>
                      <div className="text-xs text-slate-500">{l.reader}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={clsx(
                          'rounded-full px-2 py-0.5 text-xs font-medium',
                          l.daysLeft < 0 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700',
                        )}
                      >
                        {l.daysLeft < 0 ? `${-l.daysLeft} kun kechikkan` : `${l.daysLeft} kun qoldi`}
                      </span>
                      <button
                        onClick={() => giveBack(l)}
                        className="rounded-lg border border-brand-600 px-3 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-50"
                      >
                        Qaytarish
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
              <div aria-live="polite" className="mt-3 min-h-5 text-sm text-slate-700">
                {last}
              </div>
              {loans.some((l) => l.returned) && (
                <button
                  onClick={() => {
                    setLoans(SEED)
                    setLast(null)
                  }}
                  className="mt-1 text-xs font-medium text-slate-500 underline"
                >
                  Qaytadan boshlash
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
