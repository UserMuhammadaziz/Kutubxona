import {
  useEffect,
  useRef,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react'
import clsx from 'clsx'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('rounded-xl border border-slate-200 bg-paper shadow-sm dark:border-slate-700 dark:bg-slate-800', className)} {...props} />
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md'
  loading?: boolean
}) {
  const variants = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-300 dark:disabled:bg-brand-800',
    secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600',
    danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300 dark:disabled:bg-red-800',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700',
  }
  const sizes = {
    sm: 'px-2.5 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
  }
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <SpinnerDot />}
      {children}
    </button>
  )
}

/** Tugma ichidagi kichik aylanuvchi indikator. */
function SpinnerDot() {
  return <span className="h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent opacity-70" />
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        'w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm outline-none placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:focus:border-brand-400 dark:focus:ring-brand-900',
        className,
      )}
      {...props}
    />
  )
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={clsx(
        'w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm outline-none placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:focus:border-brand-400 dark:focus:ring-brand-900',
        className,
      )}
      {...props}
    />
  )
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={clsx(
        'w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:focus:border-brand-400 dark:focus:ring-brand-900',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
      {children}
    </label>
  )
}

export function Field({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx('mb-4', className)}>{children}</div>
}

export function Badge({
  children,
  tone = 'slate',
}: {
  children: ReactNode
  tone?: 'slate' | 'green' | 'red' | 'amber' | 'blue'
}) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400',
    red: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
    amber: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400',
  }
  return (
    <span
      className={clsx(
        'inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium',
        tones[tone],
      )}
    >
      {children}
    </span>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl dark:text-slate-100">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div
      role="alert"
      className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800/60 dark:bg-red-950/50 dark:text-red-400"
    >
      {message}
    </div>
  )
}

export function Spinner({ label, className }: { label?: string; className?: string }) {
  return (
    <div
      className={clsx('flex flex-col items-center justify-center gap-3 py-12', className)}
      role="status"
    >
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600 dark:border-slate-600 dark:border-t-brand-400" />
      {label && <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>}
    </div>
  )
}

/** Jadval uchun loading skeleti — bo'sh joyga spinner emas, shakl ko'rsatadi. */
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-paper dark:border-slate-700 dark:bg-slate-800">
      <div className="animate-pulse">
        <div className="border-b border-slate-200 bg-canvas px-4 py-3 dark:border-slate-700 dark:bg-slate-800/60">
          <div className="h-3 w-32 rounded bg-slate-300 dark:bg-slate-600" />
        </div>
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 border-b border-slate-100 px-4 py-3.5 last:border-0 dark:border-slate-700/60"
          >
            {Array.from({ length: cols }).map((_, j) => (
              <div
                key={j}
                className="h-3 rounded bg-slate-200 dark:bg-slate-700"
                style={{ width: j === 0 ? '30%' : j === cols - 1 ? '18%' : '22%' }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

/** Ro'yxat (karta) ko'rinishidagi skelet — arizalar/jarimalar paneli uchun. */
export function ListSkeleton({ rows = 3, className }: { rows?: number; className?: string }) {
  return (
    <div className={clsx('animate-pulse space-y-3', className)} role="status" aria-label="Yuklanmoqda">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <div className="mb-2 h-3.5 w-1/3 rounded bg-slate-300 dark:bg-slate-600" />
          <div className="h-3 w-2/3 rounded bg-slate-200 dark:bg-slate-700" />
        </div>
      ))}
    </div>
  )
}

export function EmptyState({
  icon = '📭',
  title,
  description,
  action,
}: {
  icon?: string
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
      <span className="text-3xl" aria-hidden>
        {icon}
      </span>
      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{title}</p>
      {description && <p className="max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

/** Xatolik holati: sabab + "Qayta urinish" tugmasi. */
export function ErrorState({
  title = 'Xatolik yuz berdi',
  message,
  onRetry,
  retrying = false,
}: {
  title?: string
  message?: string
  onRetry?: () => void
  retrying?: boolean
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-10 text-center dark:border-red-800/60 dark:bg-red-950/40"
    >
      <span className="text-3xl" aria-hidden>
        ⚠️
      </span>
      <p className="text-sm font-medium text-red-800 dark:text-red-300">{title}</p>
      {message && <p className="max-w-sm text-sm text-red-700/90 dark:text-red-400/90">{message}</p>}
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} loading={retrying}>
          Qayta urinish
        </Button>
      )}
    </div>
  )
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
}) {
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-4 dark:bg-slate-950/70"
      onClick={onClose}
    >
      <div
        ref={boxRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-paper p-5 shadow-xl sm:max-w-lg sm:rounded-xl sm:p-6 dark:bg-slate-800 dark:shadow-black/40"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
            {description && (
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Yopish"
            className="-mr-1 shrink-0 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

/** alert() o'rniga — xabar yuborishni tasdiqlash oynasi. */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Tasdiqlash',
  cancelLabel = 'Bekor qilish',
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}: {
  open: boolean
  title: string
  message: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'primary' | 'danger'
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <div className="text-sm text-slate-600 dark:text-slate-300">{message}</div>
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onCancel} disabled={loading}>
          {cancelLabel}
        </Button>
        <Button variant={variant} onClick={onConfirm} loading={loading}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={clsx(
        'overflow-x-auto rounded-xl border border-slate-200 bg-paper dark:border-slate-700 dark:bg-slate-800',
        className,
      )}
    >
      <table className="w-full min-w-[36rem] text-left text-sm">{children}</table>
    </div>
  )
}

/**
 * Mobil ekranda jadval o'rniga vertikal karta ro'yxatini ko'rsatadi.
 * `render(card)` mobil kartasi, `children` esa jadval satrlari.
 */
export function ResponsiveList<T>({
  items,
  render,
  children,
  empty,
}: {
  items: T[]
  render: (item: T) => ReactNode
  children: ReactNode
  empty?: ReactNode
}) {
  if (!items.length && empty) return <>{empty}</>
  return (
    <>
      <div className="hidden md:block">{children}</div>
      <ul className="space-y-2 md:hidden">
        {items.map((item, i) => (
          <li
            key={i}
            className="rounded-xl border border-slate-200 bg-paper p-3 shadow-sm dark:border-slate-700 dark:bg-slate-800"
          >
            {render(item)}
          </li>
        ))}
      </ul>
    </>
  )
}

export function Pagination({
  count,
  page,
  pageSize = 20,
  onChange,
}: {
  count: number
  page: number
  pageSize?: number
  onChange: (page: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (totalPages <= 1) return null
  return (
    <div className="mt-4 flex flex-col items-center justify-between gap-2 text-sm text-slate-600 sm:flex-row dark:text-slate-300">
      <span>
        {count} ta natijadan {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, count)}
      </span>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          Oldingi
        </Button>
        <span className="flex items-center px-2">
          {page} / {totalPages}
        </span>
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
        >
          Keyingi
        </Button>
      </div>
    </div>
  )
}
