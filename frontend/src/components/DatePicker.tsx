import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { Calendar, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, X } from 'lucide-react'

/*
 * Custom DatePicker (Ant Design style). Value is an ISO date "YYYY-MM-DD" ("" = empty),
 * exactly like <input type="date">, so it is a drop-in replacement.
 * Input is masked as DD.MM.YYYY; the popup has date / month / year panels.
 */

const MONTHS = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
const WEEKDAYS = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya']

const pad = (n: number) => String(n).padStart(2, '0')
export const toISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

export function parseISO(s: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s)
  if (!m) return null
  const d = new Date(+m[1], +m[2] - 1, +m[3])
  return d.getFullYear() === +m[1] && d.getMonth() === +m[2] - 1 && d.getDate() === +m[3] ? d : null
}

const display = (iso: string) => {
  const d = parseISO(iso)
  return d ? `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}` : ''
}

/** Digits -> "DD.MM.YYYY" while typing. */
function maskDate(raw: string): string {
  const d = raw.replace(/\D/g, '').slice(0, 8)
  return [d.slice(0, 2), d.slice(2, 4), d.slice(4, 8)].filter(Boolean).join('.')
}

function fromDisplay(text: string): string {
  const m = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(text)
  if (!m) return ''
  const iso = `${m[3]}-${m[2]}-${m[1]}`
  return parseISO(iso) ? iso : ''
}

type Panel = 'date' | 'month' | 'year'

export interface DatePickerProps {
  value: string
  onChange: (value: string) => void
  min?: string
  max?: string
  placeholder?: string
  disabled?: boolean
  allowClear?: boolean
  id?: string
  className?: string
  'aria-label'?: string
}

export function DatePicker({
  value,
  onChange,
  min,
  max,
  placeholder = 'KK.OO.YYYY',
  disabled,
  allowClear = true,
  id,
  className,
  'aria-label': ariaLabel,
}: DatePickerProps) {
  const uid = useId()
  const root = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState<{ left: number; top?: number; bottom?: number } | null>(null)
  const [text, setText] = useState(display(value))
  const [panel, setPanel] = useState<Panel>('date')
  const selected = parseISO(value)
  const today = new Date()
  const [view, setView] = useState(() => ({ y: (selected ?? today).getFullYear(), m: (selected ?? today).getMonth() }))

  useEffect(() => setText(display(value)), [value])

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!(e.target instanceof Node) || (!root.current?.contains(e.target) && !panelRef.current?.contains(e.target))) close()
    }
    document.addEventListener('mousedown', onDown)
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      document.removeEventListener('mousedown', onDown)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // The panel is portalled to <body> (fixed), so modals with overflow never clip it.
  function place() {
    const r = root.current?.getBoundingClientRect()
    if (!r) return
    const left = Math.max(8, Math.min(r.left, document.documentElement.clientWidth - 288 - 8))
    const up = window.innerHeight - r.bottom < 360 && r.top > 360
    setPos({ left, ...(up ? { bottom: window.innerHeight - r.top + 6 } : { top: r.bottom + 6 }) })
  }

  useLayoutEffect(() => {
    if (open) place()
  }, [open])

  const outOfRange = (iso: string) => (min !== undefined && min !== '' && iso < min) || (max !== undefined && max !== '' && iso > max)

  function openPanel() {
    if (disabled) return
    const base = parseISO(value) ?? new Date()
    setView({ y: base.getFullYear(), m: base.getMonth() })
    setPanel('date')
    setOpen(true)
  }

  function close() {
    setOpen(false)
    setText(display(value))
  }

  function pick(iso: string) {
    if (outOfRange(iso)) return
    onChange(iso)
    setText(display(iso))
    setOpen(false)
  }

  function onType(raw: string) {
    const masked = maskDate(raw)
    setText(masked)
    if (masked === '') return onChange('')
    const iso = fromDisplay(masked)
    if (iso && !outOfRange(iso)) {
      onChange(iso)
      const d = parseISO(iso)!
      setView({ y: d.getFullYear(), m: d.getMonth() })
    }
  }

  // 6x7 grid, week starts on Monday.
  const cells = useMemo(() => {
    const first = new Date(view.y, view.m, 1)
    const lead = (first.getDay() + 6) % 7
    return Array.from({ length: 42 }, (_, i) => new Date(view.y, view.m, 1 - lead + i))
  }, [view])

  const shiftMonth = (delta: number) => {
    const d = new Date(view.y, view.m + delta, 1)
    setView({ y: d.getFullYear(), m: d.getMonth() })
  }
  const decade = Math.floor(view.y / 10) * 10

  const navBtn =
    'flex h-7 w-7 items-center justify-center rounded text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100'
  const todayISO = toISO(today)

  return (
    <div ref={root} className={clsx('relative', className)}>
      <div
        className={clsx(
          'group flex items-center gap-2 rounded-control border bg-paper px-3 text-sm shadow-control transition-colors dark:bg-slate-700',
          'h-10',
          open
            ? 'border-primary ring-2 ring-brand-100 dark:border-brand-400 dark:ring-brand-900'
            : 'border-slate-300 hover:border-primary-hover dark:border-slate-600',
          disabled && 'cursor-not-allowed opacity-60',
        )}
      >
        <input
          id={id}
          aria-label={ariaLabel}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls={`${uid}-panel`}
          disabled={disabled}
          inputMode="numeric"
          autoComplete="off"
          placeholder={placeholder}
          value={text}
          onFocus={openPanel}
          onClick={() => !open && openPanel()}
          onChange={(e) => onType(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape' && open) {
              // Closes the calendar only, not the modal around it.
              e.stopPropagation()
              close()
            }
            if (e.key === 'Enter') {
              e.preventDefault()
              const iso = fromDisplay(text)
              if (iso) pick(iso)
            }
          }}
          className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-slate-400 dark:text-slate-100"
        />
        {allowClear && value && !disabled ? (
          <button
            type="button"
            aria-label="Tozalash"
            onClick={() => {
              onChange('')
              setText('')
            }}
            className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </button>
        ) : (
          <Calendar className="h-4 w-4 text-slate-400" aria-hidden="true" />
        )}
      </div>

      {open && pos && createPortal(
        <div
          ref={panelRef}
          onKeyDown={(e) => {
            if (e.key !== 'Escape') return
            e.stopPropagation()
            close()
          }}
          style={{ position: 'fixed', ...pos }}
          id={`${uid}-panel`}
          role="dialog"
          aria-label="Sana tanlash"
          className={clsx(
            'animate-pop z-[110] w-[288px] rounded-popup border border-slate-200 bg-paper p-3 shadow-pop dark:border-slate-600 dark:bg-slate-800',
          )}
        >
          <div className="mb-2 flex items-center justify-between">
            <div className="flex">
              <button type="button" aria-label="Oldingi yil" className={navBtn} onClick={() => (panel === 'year' ? setView({ ...view, y: view.y - 10 }) : setView({ ...view, y: view.y - 1 }))}>
                <ChevronsLeft className="h-4 w-4" />
              </button>
              {panel === 'date' && (
                <button type="button" aria-label="Oldingi oy" className={navBtn} onClick={() => shiftMonth(-1)}>
                  <ChevronLeft className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
              {panel === 'year' ? (
                <span>
                  {decade} – {decade + 9}
                </span>
              ) : (
                <>
                  <button type="button" className="rounded px-1.5 py-0.5 hover:text-primary" onClick={() => setPanel('year')}>
                    {view.y}
                  </button>
                  {panel === 'date' && (
                    <button type="button" className="rounded px-1.5 py-0.5 hover:text-primary" onClick={() => setPanel('month')}>
                      {MONTHS[view.m]}
                    </button>
                  )}
                </>
              )}
            </div>
            <div className="flex">
              {panel === 'date' && (
                <button type="button" aria-label="Keyingi oy" className={navBtn} onClick={() => shiftMonth(1)}>
                  <ChevronRight className="h-4 w-4" />
                </button>
              )}
              <button type="button" aria-label="Keyingi yil" className={navBtn} onClick={() => (panel === 'year' ? setView({ ...view, y: view.y + 10 }) : setView({ ...view, y: view.y + 1 }))}>
                <ChevronsRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {panel === 'date' && (
            <>
              <div className="grid grid-cols-7 text-center text-xs text-slate-400">
                {WEEKDAYS.map((w) => (
                  <div key={w} className="flex h-8 items-center justify-center">
                    {w}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 text-center text-sm">
                {cells.map((d) => {
                  const iso = toISO(d)
                  const inMonth = d.getMonth() === view.m
                  const isSel = iso === value
                  const isToday = iso === todayISO
                  const dis = outOfRange(iso)
                  return (
                    <div key={iso} className="flex h-9 items-center justify-center">
                      <button
                        type="button"
                        disabled={dis}
                        aria-label={display(iso)}
                        aria-pressed={isSel}
                        onClick={() => pick(iso)}
                        className={clsx(
                          'h-7 w-7 rounded transition-colors',
                          isSel
                            ? 'bg-primary font-semibold text-white'
                            : clsx(
                                inMonth ? 'text-slate-900 dark:text-slate-100' : 'text-slate-300 dark:text-slate-500',
                                !dis && 'hover:bg-primary-bg-hover dark:hover:bg-slate-700',
                                isToday && 'ring-1 ring-inset ring-primary',
                              ),
                          dis && 'cursor-not-allowed opacity-40',
                        )}
                      >
                        {d.getDate()}
                      </button>
                    </div>
                  )
                })}
              </div>
              <div className="mt-1 flex justify-center border-t border-slate-200 pt-2 dark:border-slate-600">
                <button
                  type="button"
                  disabled={outOfRange(todayISO)}
                  onClick={() => pick(todayISO)}
                  className="text-sm font-medium text-primary hover:text-primary-hover disabled:opacity-40"
                >
                  Bugun
                </button>
              </div>
            </>
          )}

          {panel === 'month' && (
            <div className="grid grid-cols-3 gap-y-2 py-1">
              {MONTHS.map((name, i) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => {
                    setView({ ...view, m: i })
                    setPanel('date')
                  }}
                  className={clsx(
                    'mx-auto h-9 w-[84px] rounded text-sm transition-colors',
                    i === view.m ? 'bg-primary font-semibold text-white' : 'hover:bg-primary-bg-hover dark:text-slate-100 dark:hover:bg-slate-700',
                  )}
                >
                  {name.slice(0, 3)}
                </button>
              ))}
            </div>
          )}

          {panel === 'year' && (
            <div className="grid grid-cols-3 gap-y-2 py-1">
              {Array.from({ length: 12 }, (_, i) => decade - 1 + i).map((y) => (
                <button
                  key={y}
                  type="button"
                  onClick={() => {
                    setView({ ...view, y })
                    setPanel('month')
                  }}
                  className={clsx(
                    'mx-auto h-9 w-[84px] rounded text-sm transition-colors',
                    y === view.y ? 'bg-primary font-semibold text-white' : 'hover:bg-primary-bg-hover dark:text-slate-100 dark:hover:bg-slate-700',
                    (y < decade || y > decade + 9) && y !== view.y && 'text-slate-300 dark:text-slate-500',
                  )}
                >
                  {y}
                </button>
              ))}
            </div>
          )}
        </div>,
        document.body,
      )}
    </div>
  )
}
