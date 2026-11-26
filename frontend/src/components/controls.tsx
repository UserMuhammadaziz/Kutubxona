import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { Check, ChevronDown, X } from 'lucide-react'

/* Custom boshqaruv elementlari (Ant Design uslubi, index.css dagi tokenlar bilan). */

export interface SelectOption {
  value: string
  label: ReactNode
  disabled?: boolean
}

/** Custom dropdown select. Drop-in alternative to <Select>: value is a string, "" = nothing selected. */
export function SelectBox({
  value,
  onChange,
  options,
  placeholder = 'Tanlang',
  allowClear,
  disabled,
  id,
  className,
  'aria-label': ariaLabel,
}: {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  allowClear?: boolean
  disabled?: boolean
  id?: string
  className?: string
  'aria-label'?: string
}) {
  const uid = useId()
  const root = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const list = useRef<HTMLUListElement>(null)
  const [pos, setPos] = useState<{ left: number; width: number; top?: number; bottom?: number } | null>(null)
  const current = options.find((o) => o.value === value)

  // The list is portalled to <body> (fixed), so modals/tables with overflow never clip it.
  useLayoutEffect(() => {
    if (!open || !root.current) return
    const r = root.current.getBoundingClientRect()
    const below = window.innerHeight - r.bottom
    const flip = below < 240 && r.top > below
    setPos({ left: r.left, width: r.width, ...(flip ? { bottom: window.innerHeight - r.top + 6 } : { top: r.bottom + 6 }) })
  }, [open])

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node
      if (!root.current?.contains(t) && !list.current?.contains(t)) setOpen(false)
    }
    const onMove = (e: Event) => {
      // resize targets `window`, which is not a Node
      if (!(e.target instanceof Node) || !list.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    window.addEventListener('resize', onMove)
    window.addEventListener('scroll', onMove, true)
    return () => {
      document.removeEventListener('mousedown', onDown)
      window.removeEventListener('resize', onMove)
      window.removeEventListener('scroll', onMove, true)
    }
  }, [open])

  function toggle() {
    if (disabled) return
    setActive(Math.max(0, options.findIndex((o) => o.value === value)))
    setOpen((o) => !o)
  }

  function choose(o: SelectOption) {
    if (o.disabled) return
    onChange(o.value)
    setOpen(false)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      if (!open) return
      // Closes the list only, not the modal around it.
      e.stopPropagation()
      return setOpen(false)
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      if (!open) return toggle()
      const step = e.key === 'ArrowDown' ? 1 : -1
      setActive((i) => (i + step + options.length) % options.length)
    }
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      if (!open) return toggle()
      if (options[active]) choose(options[active])
    }
  }

  return (
    <div ref={root} className={clsx('relative', className)}>
      <button
        type="button"
        id={id}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={`${uid}-list`}
        disabled={disabled}
        onClick={toggle}
        onKeyDown={onKeyDown}
        className={clsx(
          'flex h-10 w-full items-center justify-between gap-2 rounded-control border bg-paper px-3 text-left text-sm shadow-control transition-colors dark:bg-slate-700',
          open
            ? 'border-primary ring-2 ring-brand-100 dark:border-brand-400 dark:ring-brand-900'
            : 'border-slate-300 hover:border-primary-hover dark:border-slate-600',
          disabled && 'cursor-not-allowed opacity-60',
        )}
      >
        <span className={clsx('truncate', current ? 'dark:text-slate-100' : 'text-slate-400')}>{current ? current.label : placeholder}</span>
        {allowClear && value && !disabled ? (
          <span
            role="button"
            aria-label="Tozalash"
            onClick={(e) => {
              e.stopPropagation()
              onChange('')
            }}
            className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </span>
        ) : (
          <ChevronDown className={clsx('h-4 w-4 shrink-0 text-slate-400 transition-transform', open && 'rotate-180')} aria-hidden="true" />
        )}
      </button>
      {open && pos && createPortal(
        <ul
          ref={list}
          id={`${uid}-list`}
          role="listbox"
          style={{ position: 'fixed', left: pos.left, top: pos.top, bottom: pos.bottom, minWidth: pos.width }}
          className="animate-pop z-[100] max-h-64 w-max max-w-[90vw] overflow-auto rounded-popup border border-slate-200 bg-paper p-1 shadow-pop dark:border-slate-600 dark:bg-slate-800"
        >
          {options.map((o, i) => {
            const selected = o.value === value
            return (
              <li
                key={o.value}
                role="option"
                aria-selected={selected}
                aria-disabled={o.disabled}
                onMouseEnter={() => setActive(i)}
                onClick={() => choose(o)}
                className={clsx(
                  'flex cursor-pointer items-center justify-between gap-2 rounded px-3 py-1.5 text-sm dark:text-slate-100',
                  selected && 'bg-primary-bg font-semibold dark:bg-slate-700',
                  active === i && !selected && 'bg-slate-100 dark:bg-slate-700/60',
                  o.disabled && 'cursor-not-allowed opacity-40',
                )}
              >
                <span className="truncate">{o.label}</span>
                {selected && <Check className="h-4 w-4 text-primary" aria-hidden="true" />}
              </li>
            )
          })}
        </ul>,
        document.body,
      )}
    </div>
  )
}

/** On/off switch. */
export function Switch({
  checked,
  onChange,
  disabled,
  label,
  id,
}: {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  label?: ReactNode
  id?: string
}) {
  return (
    <label className={clsx('inline-flex items-center gap-2 text-sm dark:text-slate-100', disabled && 'cursor-not-allowed opacity-60')}>
      <button
        type="button"
        id={id}
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={clsx(
          'relative h-[22px] w-[44px] shrink-0 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
          checked ? 'bg-primary hover:bg-primary-hover' : 'bg-slate-300 hover:bg-slate-400 dark:bg-slate-600',
        )}
      >
        <span
          className={clsx(
            'absolute top-[2px] h-[18px] w-[18px] rounded-full bg-white shadow transition-all duration-200',
            checked ? 'left-[24px]' : 'left-[2px]',
          )}
        />
      </button>
      {label}
    </label>
  )
}

/** Checkbox with a custom box. */
export function Checkbox({
  checked,
  onChange,
  disabled,
  label,
  id,
}: {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  label?: ReactNode
  id?: string
}) {
  return (
    <label className={clsx('inline-flex cursor-pointer items-center gap-2 text-sm dark:text-slate-100', disabled && 'cursor-not-allowed opacity-60')}>
      <input id={id} type="checkbox" className="peer sr-only" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span
        aria-hidden="true"
        className={clsx(
          'flex h-4 w-4 items-center justify-center rounded-sm border transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary',
          checked ? 'border-primary bg-primary' : 'border-slate-300 bg-paper hover:border-primary dark:border-slate-500 dark:bg-slate-700',
        )}
      >
        {checked && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
      </span>
      {label}
    </label>
  )
}

/** Radio group (single choice). */
export function RadioGroup({
  value,
  onChange,
  options,
  name,
}: {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  name?: string
}) {
  const uid = useId()
  return (
    <div role="radiogroup" className="flex flex-wrap gap-x-5 gap-y-2">
      {options.map((o) => (
        <label key={o.value} className={clsx('inline-flex cursor-pointer items-center gap-2 text-sm dark:text-slate-100', o.disabled && 'cursor-not-allowed opacity-60')}>
          <input type="radio" className="peer sr-only" name={name ?? uid} checked={o.value === value} disabled={o.disabled} onChange={() => onChange(o.value)} />
          <span
            aria-hidden="true"
            className={clsx(
              'flex h-4 w-4 items-center justify-center rounded-full border transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary',
              o.value === value ? 'border-primary' : 'border-slate-300 hover:border-primary dark:border-slate-500',
            )}
          >
            {o.value === value && <span className="h-2 w-2 rounded-full bg-primary" />}
          </span>
          {o.label}
        </label>
      ))}
    </div>
  )
}
