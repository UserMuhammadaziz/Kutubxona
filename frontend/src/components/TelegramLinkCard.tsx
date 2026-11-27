import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { telegramLinkApi, type TelegramLinkCode } from '../api/resources'
import { errorMessage } from '../api/client'
import { useToast } from './Toast'
import { Icons } from './icons'
import { Badge, Button, Card, ConfirmDialog, ErrorBanner } from './ui'

const STATUS_KEY = ['telegram-link-status']
const POLL_MS = 3000

/** Profile card: link the signed-in staff member's Telegram to the library bot. */
export function TelegramLinkCard() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [pending, setPending] = useState<TelegramLinkCode | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [confirmUnlink, setConfirmUnlink] = useState(false)
  const wasLinked = useRef<boolean | null>(null)

  const status = useQuery({
    queryKey: STATUS_KEY,
    queryFn: telegramLinkApi.status,
    // Poll only while a link code is waiting to be used in Telegram.
    refetchInterval: pending ? POLL_MS : false,
    refetchIntervalInBackground: true,
    retry: (count, err) => !(isAxiosError(err) && err.response?.status === 403) && count < 2,
  })
  const linked = status.data?.linked ?? false

  useEffect(() => {
    if (status.data === undefined) return
    if (pending && linked && wasLinked.current === false) {
      setPending(null)
      toast.success('Telegram muvaffaqiyatli ulandi.')
    }
    wasLinked.current = linked
  }, [status.data, linked, pending, toast])

  // Stop polling once the code expires.
  useEffect(() => {
    if (!pending) return
    const left = new Date(pending.expires).getTime() - Date.now()
    const timer = window.setTimeout(() => {
      setPending(null)
      setError("Kodning muddati tugadi. Qaytadan «Telegram botga ulanish» tugmasini bosing.")
    }, Math.max(left, 0))
    return () => window.clearTimeout(timer)
  }, [pending])

  const codeMut = useMutation({
    mutationFn: telegramLinkApi.code,
    onMutate: () => {
      setError(null)
      // Open the tab synchronously inside the click, otherwise popup blockers stop it.
      return { tab: window.open('', '_blank') }
    },
    onSuccess: (data, _vars, ctx) => {
      wasLinked.current = false
      setPending(data)
      if (ctx?.tab) ctx.tab.location.href = data.deep_link
    },
    onError: (err, _vars, ctx) => {
      ctx?.tab?.close()
      setError(errorMessage(err))
    },
  })

  const unlinkMut = useMutation({
    mutationFn: telegramLinkApi.unlink,
    onSuccess: (data) => {
      queryClient.setQueryData(STATUS_KEY, data)
      setConfirmUnlink(false)
      toast.success('Telegram uzildi.')
    },
    onError: (err) => {
      setConfirmUnlink(false)
      toast.error(errorMessage(err))
    },
  })

  const botUsername = status.data?.bot_username

  // Platform accounts without a library membership have nothing to link.
  if (isAxiosError(status.error) && status.error.response?.status === 403) return null

  return (
    <Card className="mb-5 p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
            <Icons.send className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            Telegram bot
            {status.data && (
              <Badge tone={linked ? 'green' : 'slate'}>{linked ? 'Ulangan' : 'Ulanmagan'}</Badge>
            )}
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {linked
              ? `Kunlik hisobotlar, yangiliklar va muhim xabarlar${botUsername ? ` @${botUsername}` : ''} botiga keladi.`
              : 'Hisobotlar, yangiliklar va ma\'lumot yangilanishlarini Telegram orqali olish uchun botga ulaning.'}
          </p>
        </div>
        {status.isLoading ? null : linked ? (
          <Button variant="secondary" onClick={() => setConfirmUnlink(true)}>
            Uzish
          </Button>
        ) : botUsername ? (
          <Button onClick={() => codeMut.mutate()} loading={codeMut.isPending}>
            Telegram botga ulanish
          </Button>
        ) : null}
      </div>

      {status.isError && <div className="mt-3"><ErrorBanner message={errorMessage(status.error)} /></div>}
      {status.data && !linked && !botUsername && (
        <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-900/20 dark:text-amber-200">
          Kutubxonaning Telegram boti hali ulanmagan. Administrator uni «Kutubxona profili» sahifasida ulashi kerak.
        </p>
      )}
      {error && <div className="mt-3"><ErrorBanner message={error} /></div>}

      {pending && !linked && (
        <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50 p-4 text-sm dark:border-brand-800 dark:bg-brand-900/20">
          <div className="flex items-center gap-2 font-medium text-slate-800 dark:text-slate-100">
            <span className="h-2 w-2 animate-pulse rounded-full bg-brand-600" />
            Telegramda «Start» tugmasini bosing — ulanish kutilmoqda…
          </div>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            Telegram ochilmadimi?{' '}
            <a
              href={pending.deep_link}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-brand-700 underline dark:text-brand-300"
            >
              Botni ochish
            </a>{' '}
            yoki @{pending.bot_username} botiga quyidagini yuboring:
          </p>
          <code className="mt-2 block break-all rounded bg-paper px-2 py-1 text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-100">
            /ulash {pending.code}
          </code>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Kod 15 daqiqa amal qiladi va bir marta ishlatiladi.</p>
        </div>
      )}

      <ConfirmDialog
        open={confirmUnlink}
        title="Telegramni uzish"
        message="Shundan keyin hisobot va xabarlar Telegramga kelmaydi. Davom etasizmi?"
        confirmLabel="Uzish"
        loading={unlinkMut.isPending}
        onConfirm={() => unlinkMut.mutate()}
        variant="danger"
        onCancel={() => setConfirmUnlink(false)}
      />
    </Card>
  )
}
