import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import clsx from 'clsx'

export type ToastKind = 'success' | 'error' | 'info'

interface Toast {
  id: number
  kind: ToastKind
  message: string
}

interface ToastApi {
  success: (message: string) => void
  error: (message: string) => void
  info: (message: string) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const KISQA = 4000
const UZUN = 7000
// Ekran bir vaqtda ko'rsatiladigan maksimal xabar soni. Chegara oshilganda
// eng eskisi chiqarib tashlanadi.
const MAX = 3

const usul: Record<ToastKind, { icon: string; ring: string; iconColor: string }> = {
  success: {
    icon: '✓',
    ring: 'border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-950/80',
    iconColor: 'bg-emerald-600 text-white dark:bg-emerald-500',
  },
  error: {
    icon: '!',
    ring: 'border-red-200 bg-red-50 dark:border-red-500/30 dark:bg-red-950/80',
    iconColor: 'bg-red-600 text-white dark:bg-red-500',
  },
  info: {
    icon: 'i',
    ring: 'border-blue-200 bg-blue-50 dark:border-blue-500/30 dark:bg-blue-950/80',
    iconColor: 'bg-blue-600 text-white dark:bg-blue-500',
  },
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const key = useRef(0)
  const timers = useRef(new Set<number>())

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // Provider unmount bo'lganda kutayotgan taymerlar to'xtatiladi — aks holda
  // ular yopilgan komponentga setToasts chaqirib, xotira oqib ketadi.
  useEffect(() => {
    const kutayotgan = timers.current
    return () => {
      kutayotgan.forEach((t) => window.clearTimeout(t))
      kutayotgan.clear()
    }
  }, [])

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = ++key.current
      setToasts((prev) => [...prev.slice(-(MAX - 1)), { id, kind, message }])
      const t = window.setTimeout(() => {
        timers.current.delete(t)
        dismiss(id)
      }, kind === 'error' ? UZUN : KISQA)
      timers.current.add(t)
    },
    [dismiss],
  )

  const api = useMemo<ToastApi>(
    () => ({
      success: (m) => push('success', m),
      error: (m) => push('error', m),
      info: (m) => push('info', m),
    }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className={clsx(
          'pointer-events-none fixed z-[100] flex flex-col gap-2',
          // Mobil: ekran pastida, to'liq kenglikda. Desktop: o'ng yuqorida.
          'inset-x-3 bottom-3 items-stretch sm:inset-x-auto sm:bottom-auto sm:right-4 sm:top-4 sm:w-96 sm:items-end',
        )}
      >
        {toasts.map((t) => {
          const u = usul[t.kind]
          return (
            <div
              key={t.id}
              role="status"
              className={clsx(
                'pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur',
                'animate-[toast-in_.18s_ease-out]',
                u.ring,
              )}
            >
              <span
                className={clsx(
                  'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold',
                  u.iconColor,
                )}
              >
                {u.icon}
              </span>
              <p className="min-w-0 flex-1 text-sm text-slate-800 dark:text-slate-100">{t.message}</p>
              <button
                onClick={() => dismiss(t.id)}
                aria-label="Yopish"
                className="-mr-1 shrink-0 rounded p-0.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>
          )
        })}
      </div>
      <style>{`@keyframes toast-in { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: none } }`}</style>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast faqat ToastProvider ichida ishlatilishi mumkin')
  return ctx
}
