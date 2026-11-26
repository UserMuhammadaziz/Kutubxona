import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { MoreHorizontal } from 'lucide-react'

export interface ActionMenuItem {
  label: ReactNode
  onSelect: () => void
  danger?: boolean
  disabled?: boolean
  /** Draws a divider above the item. */
  separated?: boolean
}

/** "More actions" button with a popup menu, portalled so scrolling tables never clip it. */
export function ActionMenu({ label, items }: { label: string; items: ActionMenuItem[] }) {
  const id = useId()
  const button = useRef<HTMLButtonElement>(null)
  const menu = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ right: number; top?: number; bottom?: number } | null>(null)

  useLayoutEffect(() => {
    if (!open || !button.current) return
    const r = button.current.getBoundingClientRect()
    const below = window.innerHeight - r.bottom
    const flip = below < items.length * 40 + 24 && r.top > below
    const right = document.documentElement.clientWidth - r.right
    setPos({ right, ...(flip ? { bottom: window.innerHeight - r.top + 6 } : { top: r.bottom + 6 }) })
  }, [open, items.length])

  useEffect(() => {
    if (!open || !pos) return
    menu.current?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus({ preventScroll: true })
  }, [open, pos])

  useEffect(() => {
    if (!open) return
    const close = (e: Event) => {
      const t = e.target
      if (t instanceof Node && (menu.current?.contains(t) || button.current?.contains(t))) return
      setOpen(false)
    }
    document.addEventListener('mousedown', close)
    window.addEventListener('resize', close)
    window.addEventListener('scroll', close, true)
    return () => {
      document.removeEventListener('mousedown', close)
      window.removeEventListener('resize', close)
      window.removeEventListener('scroll', close, true)
    }
  }, [open])

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape' || e.key === 'Tab') {
      e.preventDefault()
      e.stopPropagation()
      setOpen(false)
      button.current?.focus()
      return
    }
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) return
    e.preventDefault()
    const list = [...(menu.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    const i = list.indexOf(document.activeElement as HTMLButtonElement)
    const next = e.key === 'Home' ? 0 : e.key === 'End' ? list.length - 1 : (i + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length
    list[next]?.focus()
  }

  return (
    <>
      <button
        ref={button}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => setOpen((o) => !o)}
        className={clsx(
          'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-slate-100',
          open && 'bg-slate-100 text-slate-900 dark:bg-slate-700 dark:text-slate-100',
        )}
      >
        <MoreHorizontal className="h-5 w-5" aria-hidden="true" />
      </button>
      {open && pos && createPortal(
        <div
          ref={menu}
          id={id}
          role="menu"
          aria-label={label}
          onKeyDown={onKeyDown}
          style={{ position: 'fixed', ...pos }}
          className="animate-pop z-[90] min-w-44 max-w-[90vw] rounded-popup border border-slate-200 bg-paper p-1 shadow-pop dark:border-slate-600 dark:bg-slate-800"
        >
          {items.map((item, i) => (
            <div key={i} className={clsx(item.separated && i > 0 && 'mt-1 border-t border-slate-200 pt-1 dark:border-slate-700')} role="none">
              <button
                type="button"
                role="menuitem"
                disabled={item.disabled}
                onClick={() => {
                  setOpen(false)
                  button.current?.focus()
                  item.onSelect()
                }}
                className={clsx(
                  'flex min-h-9 w-full items-center rounded-lg px-3 py-1.5 text-left text-sm disabled:opacity-40',
                  item.danger
                    ? 'text-red-700 hover:bg-red-50 focus-visible:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10 dark:focus-visible:bg-red-500/10'
                    : 'text-slate-800 hover:bg-slate-100 focus-visible:bg-slate-100 dark:text-slate-100 dark:hover:bg-slate-700 dark:focus-visible:bg-slate-700',
                )}
              >
                {item.label}
              </button>
            </div>
          ))}
        </div>,
        document.body,
      )}
    </>
  )
}
