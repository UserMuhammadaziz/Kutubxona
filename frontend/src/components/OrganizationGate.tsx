import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { isAxiosError } from 'axios'
import clsx from 'clsx'
import { api, errorMessage } from '../api/client'
import { authApi, type OrganizationInfo } from '../api/resources'
import { useOrganizationBlock, type BlockStatus, type OrganizationBlock } from '../hooks/useOrganizationBlock'
import { formatDate } from '../lib/format'
import { askPushPermission, pushSupported, subscribeToPush } from '../lib/push'
import { useAuthStore } from '../store/auth'
import { useThemeStore } from '../store/theme'
import { Icons } from './icons'
import { LogoMark } from './Logo'
import { useToast } from './Toast'
import { Button, ErrorBanner, Label, Textarea } from './ui'

const POLL_MS = 20_000

const CONTENT: Record<BlockStatus, { title: string; text: string; icon: keyof typeof Icons; tone: string }> = {
  pending: {
    title: 'Kutubxonangiz hali faollashtirilmagan',
    text: "Arizangizni platforma administratori ko'rib chiqadi. Tasdiqlangach, tizim shu oynada o'zi ochiladi: sahifani yangilash yoki qayta kirish shart emas.",
    icon: 'clock',
    tone: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  },
  suspended: {
    title: "Kutubxona faoliyati to'xtatilgan",
    text: "Platforma administratori kutubxonangizga kirishni yopgan. Ma'lumotlaringiz saqlanib turibdi. Qayta faollashtirilganda tizim shu oynada o'zi ochiladi.",
    icon: 'lock',
    tone: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  },
  rejected: {
    title: 'Ariza rad etilgan',
    text: "Savolingiz bo'lsa yoki ma'lumotni to'g'rilash kerak bo'lsa, platformaga yozing. Qaror o'zgarsa, tizim shu oynada o'zi ochiladi.",
    icon: 'xCircle',
    tone: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300',
  },
  archived: {
    title: 'Kutubxona arxivlangan',
    text: "Kutubxona arxivga olingan, unda ishlab bo'lmaydi. Qayta ochish uchun platformaga yozing.",
    icon: 'package',
    tone: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
  },
  none: {
    title: 'Sizga kutubxona biriktirilmagan',
    text: "Hisobingiz hech bir kutubxonaga a'zo emas. Kutubxona egasi sizni xodimlar ro'yxatiga qo'shsa, tizim shu oynada o'zi ochiladi.",
    icon: 'building',
    tone: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
  },
}

/**
 * Stops the whole app while the selected library is not active. Pages are not
 * mounted underneath, so nothing sends requests that could only fail.
 */
export function OrganizationGate({ children }: { children: ReactNode }) {
  const block = useOrganizationBlock()
  const user = useAuthStore((s) => s.user)
  const organizationId = useAuthStore((s) => s.organizationId)
  const { pathname } = useLocation()
  const queryClient = useQueryClient()
  const toast = useToast()
  const previous = useRef<OrganizationBlock | null>(null)
  const key = block ? `${block.id}:${block.status}` : null

  useEffect(() => {
    const before = previous.current
    previous.current = block
    if (!before || block) return
    // Drop answers that were refused while the library was blocked.
    void queryClient.invalidateQueries()
    if (before.id === null || before.id === organizationId) {
      toast.success('Kutubxona faollashtirildi. Ishlashingiz mumkin.')
    }
    // `key` stands for `block`, which is a new object on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  // Platform users manage organizations even when their own library is frozen.
  const platformPage = !!user?.is_platform && /^\/(platform|profile)(\/|$)/.test(pathname)
  if (block && !platformPage) return <StatusScreen key={block.id ?? 'none'} block={block} />

  // Several libraries, none chosen: the picker covers the screen, do not load pages under it.
  if ((user?.kutubxonalar?.length ?? 0) > 1 && organizationId === null) return <ShellBackdrop />

  return <>{children}</>
}

/** Motionless outline of the app, so it is clear the workspace is there but closed. */
function ShellBackdrop() {
  // The page reserves a scrollbar gutter; here it would be a bright strip beside the dimmed screen.
  useEffect(() => {
    const root = document.documentElement
    root.style.scrollbarGutter = 'auto'
    return () => {
      root.style.scrollbarGutter = ''
    }
  }, [])
  const bar = 'rounded bg-slate-300/60 dark:bg-slate-700/60'
  return (
    <div aria-hidden className="fixed inset-0 flex overflow-hidden bg-canvas dark:bg-slate-900">
      <div className="hidden w-64 shrink-0 border-r border-slate-200 bg-paper p-5 lg:block dark:border-slate-700 dark:bg-slate-800">
        <div className={clsx(bar, 'h-7 w-36')} />
        {[28, 36, 24, 32, 28, 40, 30].map((w, i) => (
          <div key={i} className={clsx(bar, 'mt-5 h-4')} style={{ width: `${w * 4}px` }} />
        ))}
      </div>
      <div className="flex-1 p-8">
        <div className={clsx(bar, 'h-8 w-56')} />
        <div className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-paper dark:bg-slate-800" />
          ))}
        </div>
        <div className="mt-4 h-[60vh] rounded-xl bg-paper dark:bg-slate-800" />
      </div>
    </div>
  )
}

function StatusScreen({ block }: { block: OrganizationBlock }) {
  const user = useAuthStore((s) => s.user)
  const refresh = useAuthStore((s) => s.refresh)
  const logout = useAuthStore((s) => s.logout)
  const pickerOpen = useAuthStore((s) => s.tenantPickerOpen)
  const openTenantPicker = useAuthStore((s) => s.openTenantPicker)
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggle)
  const [contactOpen, setContactOpen] = useState(false)
  const [checkedByHand, setCheckedByHand] = useState(false)
  const titleId = useId()
  const textId = useId()
  const titleRef = useRef<HTMLHeadingElement>(null)

  const status = useQuery({
    queryKey: ['organization-status', block.id],
    queryFn: async () => {
      // The only request sent while blocked. The profile is read again only after a change;
      // once the library is active this screen unmounts by itself.
      try {
        const current = await authApi.organization()
        if ((current?.id ?? null) !== block.id || (current && current.status !== block.status)) await refresh()
        return current
      } catch (err) {
        // Membership was removed, or a second library was added.
        if (!isAxiosError(err) || ![400, 403].includes(err.response?.status ?? 0)) throw err
        await refresh()
        return null
      }
    },
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: 'always',
    refetchOnReconnect: 'always',
    // Never show another library's reason while this one loads.
    placeholderData: undefined,
    staleTime: 0,
    retry: false,
  })
  const org = status.data?.id === block.id ? (status.data as OrganizationInfo) : null
  const content = CONTENT[block.status]
  const reason = org?.status_reason?.trim()
  const severalLibraries = (user?.kutubxonalar?.length ?? 0) > 1
  const hasFooter =
    !contactOpen || user?.is_platform || severalLibraries || !!org?.support?.phone || !!org?.support?.telegram
  const offline = status.fetchStatus === 'paused'

  useEffect(() => titleRef.current?.focus(), [block.status])

  const iconButton =
    'flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700'

  return (
    <>
      <ShellBackdrop />
      <div inert={pickerOpen} className="fixed inset-0 z-[90] overflow-y-auto bg-slate-900/50 dark:bg-slate-950/70">
        <div className="flex min-h-full items-center justify-center sm:p-6">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={textId}
            className="animate-pop flex min-h-dvh w-full flex-col bg-paper sm:min-h-0 sm:max-w-2xl sm:rounded-2xl sm:shadow-2xl dark:bg-slate-800"
          >
            <header className="pwa-safe-top flex items-center gap-2 border-b border-slate-200 px-5 py-3 sm:px-8 dark:border-slate-700">
              <LogoMark className="mr-1 h-8 w-8 shrink-0" />
              <p className="min-w-0 flex-1 truncate text-base font-semibold text-slate-900 dark:text-slate-100" title={block.name}>
                {block.name || 'Kutubxona'}
              </p>
              <button
                type="button"
                onClick={toggleTheme}
                aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
                className={iconButton}
              >
                {theme === 'dark' ? <Icons.sun className="h-5 w-5" /> : <Icons.moon className="h-5 w-5" />}
              </button>
              <button
                type="button"
                onClick={logout}
                className="-mr-3 min-h-11 shrink-0 rounded-lg px-3 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Chiqish
              </button>
            </header>

            <div className="flex-1 px-5 py-7 sm:px-8 sm:py-9">
              <span className={clsx('flex h-14 w-14 items-center justify-center rounded-2xl', content.tone)}>
                {Icons[content.icon]({ className: 'h-7 w-7' })}
              </span>
              <h1
                id={titleId}
                ref={titleRef}
                tabIndex={-1}
                className="mt-5 text-balance text-2xl font-semibold tracking-tight text-slate-900 outline-none! sm:text-3xl dark:text-slate-100"
              >
                {content.title}
              </h1>
              <p id={textId} className="mt-3 max-w-[60ch] text-base leading-relaxed text-slate-700 dark:text-slate-300">
                {content.text}
              </p>

              {block.status === 'pending' && <PendingSteps sentAt={org?.yaratilgan} />}

              {reason && block.status !== 'pending' && (
                <dl className="mt-6 rounded-xl bg-canvas px-4 py-3 dark:bg-slate-900/60">
                  <dt className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Sabab{org?.status_changed_at ? `, ${formatDate(org.status_changed_at)}` : ''}
                  </dt>
                  <dd className="mt-1 whitespace-pre-line break-words text-base text-slate-900 dark:text-slate-100">
                    {reason}
                  </dd>
                </dl>
              )}

              <div className="mt-6 flex flex-wrap items-center gap-x-4 text-sm text-slate-600 dark:text-slate-400">
                <p>
                  {offline || status.isError
                    ? "Hozir holatni tekshirib bo'lmadi. Aloqa tiklansa, yana tekshiramiz."
                    : "Holat har 20 soniyada o'zi tekshiriladi."}
                </p>
                <button
                  type="button"
                  disabled={status.isFetching}
                  onClick={() => {
                    setCheckedByHand(false)
                    void status.refetch().then(() => setCheckedByHand(true))
                  }}
                  className="min-h-11 rounded font-medium text-brand-700 underline underline-offset-4 hover:text-brand-600 disabled:opacity-60 sm:min-h-0 dark:text-brand-300 dark:hover:text-brand-200"
                >
                  Hozir tekshirish
                </button>
                <span role="status" className="text-slate-700 dark:text-slate-300">
                  {checkedByHand && !status.isFetching && !status.isError && !offline ? "Tekshirildi, hali o'zgarmagan." : ''}
                </span>
              </div>

              {block.status === 'pending' && <PushButton />}

              {contactOpen && <ContactForm status={block.status} onClose={() => setContactOpen(false)} />}
            </div>

            {hasFooter && (
              <footer className="flex flex-col gap-2 border-t border-slate-200 px-5 py-4 sm:flex-row sm:flex-wrap sm:items-center sm:px-8 dark:border-slate-700">
                {user?.is_platform ? (
                  <Link
                    to="/platform"
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 text-sm font-medium text-white hover:bg-brand-700"
                  >
                    <Icons.shield className="h-4 w-4" />
                    Platforma boshqaruvi
                  </Link>
                ) : (
                  <>
                    {!contactOpen && (
                      <Button type="button" className="min-h-11" onClick={() => setContactOpen(true)}>
                        <Icons.send className="h-4 w-4 rotate-45" />
                        Platformaga yozish
                      </Button>
                    )}
                    <SupportLinks support={org?.support} />
                  </>
                )}
                {severalLibraries && (
                  <Button type="button" variant="secondary" className="min-h-11 sm:ml-auto" onClick={openTenantPicker}>
                    Boshqa kutubxona
                  </Button>
                )}
              </footer>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

function PendingSteps({ sentAt }: { sentAt?: string }) {
  const steps = [
    { label: 'Ariza yuborildi', note: sentAt ? formatDate(sentAt) : '', state: 'done' },
    { label: "Administrator ko'rib chiqadi", note: 'Hozir shu bosqichda', state: 'current' },
    { label: 'Kutubxona ochiladi', note: 'Avtomatik', state: 'next' },
  ] as const
  return (
    <ol className="mt-7 grid gap-4 sm:grid-cols-3 sm:gap-3">
      {steps.map((s) => (
        <li
          key={s.label}
          aria-current={s.state === 'current' ? 'step' : undefined}
          className="flex gap-3 sm:block"
        >
          <span
            aria-hidden
            className={clsx(
              'w-1 shrink-0 rounded-full sm:block sm:h-1 sm:w-full',
              s.state === 'done' && 'bg-brand-600 dark:bg-brand-400',
              s.state === 'current' && 'bg-amber-500 dark:bg-amber-400',
              s.state === 'next' && 'bg-slate-300 dark:bg-slate-600',
            )}
          />
          <span className="block sm:mt-3">
            <span className="block text-sm font-semibold text-slate-900 dark:text-slate-100">{s.label}</span>
            <span className="block text-sm text-slate-600 dark:text-slate-400">{s.note}</span>
          </span>
        </li>
      ))}
    </ol>
  )
}

function SupportLinks({ support }: { support?: { phone: string; telegram: string } }) {
  const link =
    'inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium text-slate-800 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700'
  if (!support?.phone && !support?.telegram) return null
  return (
    <div className="flex flex-wrap justify-center gap-1">
      {support.phone && (
        <a href={`tel:${support.phone.replace(/[^+\d]/g, '')}`} className={link}>
          <Icons.phone className="h-4 w-4" />
          {support.phone}
        </a>
      )}
      {support.telegram && (
        <a href={`https://t.me/${encodeURIComponent(support.telegram)}`} target="_blank" rel="noreferrer" className={link}>
          <Icons.chat className="h-4 w-4" />
          Telegram
        </a>
      )}
    </div>
  )
}

/** Offered only when the browser has not been asked yet. */
function PushButton() {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const [hidden, setHidden] = useState(!pushSupported() || Notification.permission !== 'default')
  if (hidden) return null

  async function enable() {
    setBusy(true)
    const granted = await askPushPermission()
    const done = granted && (await subscribeToPush())
    setBusy(false)
    if (done) toast.success('Tasdiqlanganda bildirishnoma keladi.')
    setHidden(granted || Notification.permission === 'denied')
  }

  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => void enable()}
      className="mt-1 inline-flex min-h-11 items-center gap-2 rounded text-sm font-medium text-brand-700 underline underline-offset-4 hover:text-brand-600 disabled:opacity-60 dark:text-brand-300 dark:hover:text-brand-200"
    >
      <Icons.bell className="h-4 w-4" />
      Tasdiqlanganda bildirishnoma olish
    </button>
  )
}

function ContactForm({ status, onClose }: { status: BlockStatus; onClose: () => void }) {
  const toast = useToast()
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fieldId = useId()

  useEffect(() => document.getElementById(fieldId)?.focus(), [fieldId])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = message.trim()
    if (!text || sending) {
      if (!text) setError('Xabar matnini yozing.')
      return
    }
    setSending(true)
    setError(null)
    try {
      await api.post('/issue-reports/', {
        category: 'other',
        module: 'organization',
        message: `[${status}] ${text}`,
        page_url: window.location.href.slice(0, 500),
        user_agent: navigator.userAgent.slice(0, 300),
        console_errors: [],
        failed_requests: [],
        screenshot: '',
      })
      toast.success('Xabar platforma administratoriga yuborildi.')
      onClose()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={send} className="mt-6 border-t border-slate-200 pt-6 dark:border-slate-700">
      <ErrorBanner message={error} />
      <Label htmlFor={fieldId}>Platforma administratoriga xabar</Label>
      <Textarea
        id={fieldId}
        rows={4}
        maxLength={1500}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Masalan: to'lov qilindi, kutubxonani faollashtirib bering."
      />
      <div className="mt-3 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" className="min-h-11" onClick={onClose} disabled={sending}>
          Bekor qilish
        </Button>
        <Button type="submit" className="min-h-11" loading={sending}>
          Yuborish
        </Button>
      </div>
    </form>
  )
}
