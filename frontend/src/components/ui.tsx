import type { ButtonHTMLAttributes, HTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import clsx from 'clsx'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('rounded-xl border border-slate-200 bg-paper shadow-sm dark:border-slate-700 dark:bg-slate-800', className)} {...props} />
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md'
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
      {...props}
    />
  )
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        'w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder:text-slate-400 dark:focus:border-brand-400 dark:focus:ring-brand-900',
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

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{children}</label>
}

export function Field({ children }: { children: ReactNode }) {
  return <div className="mb-4">{children}</div>
}

export function Badge({ children, tone = 'slate' }: { children: ReactNode; tone?: 'slate' | 'green' | 'red' | 'amber' | 'blue' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400',
    red: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
    amber: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400',
  }
  return <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', tones[tone])}>{children}</span>
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800/60 dark:bg-red-950/50 dark:text-red-400">{message}</div>
  )
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600 dark:border-slate-600" />
    </div>
  )
}

export function EmptyState({ text }: { text: string }) {
  return <div className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">{text}</div>
}

export function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 dark:bg-slate-950/70" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-paper p-6 shadow-xl dark:bg-slate-800 dark:shadow-black/40"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-300"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-paper dark:border-slate-700 dark:bg-slate-800">
      <table className="w-full text-left text-sm">{children}</table>
    </div>
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
    <div className="mt-4 flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
      <span>
        {count} ta natijadan {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, count)}
      </span>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          Oldingi
        </Button>
        <span className="flex items-center px-2">
          {page} / {totalPages}
        </span>
        <Button variant="secondary" size="sm" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
          Keyingi
        </Button>
      </div>
    </div>
  )
}