import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { billingApi, type BillingPayment, type PaymentStatus, type SubscriptionStatus } from '../api/resources'
import { errorMessage } from '../api/client'
import { useToast } from '../components/Toast'
import { Badge, Button, Card, ErrorBanner, ErrorState, PageHeader, PageSkeleton, Table } from '../components/ui'
import { formatDate, formatDateTime, formatMoney } from '../lib/format'

const POLL_MS = 4000

const STATUS: Record<SubscriptionStatus, { label: string; tone: 'green' | 'amber' | 'red' | 'slate' }> = {
  trial: { label: 'Sinov muddati', tone: 'amber' },
  active: { label: 'Faol', tone: 'green' },
  past_due: { label: "To'lov kechikkan", tone: 'red' },
  canceled: { label: 'Bekor qilingan', tone: 'slate' },
  expired: { label: 'Muddati tugagan', tone: 'red' },
}

const PAYMENT_STATUS: Record<PaymentStatus, { label: string; tone: 'green' | 'amber' | 'slate' }> = {
  pending: { label: 'Kutilmoqda', tone: 'amber' },
  paid: { label: "To'langan", tone: 'green' },
  cancelled: { label: 'Bekor qilingan', tone: 'slate' },
}

const periodLabel = (months: number) => (months === 12 ? '1 yil' : `${months} oy`)

function daysLeft(end: string | null): number | null {
  if (!end) return null
  return Math.ceil((new Date(end).getTime() - Date.now()) / 86_400_000)
}

/** Owner/admin page: subscription state, paying for 1/3/6/12 months through Taps, payment history. */
export function Billing() {
  const toast = useToast()
  const qc = useQueryClient()
  const overview = useQuery({ queryKey: ['billing'], queryFn: billingApi.overview })
  const [months, setMonths] = useState(1)
  const [method, setMethod] = useState('click')
  const [pending, setPending] = useState<BillingPayment | null>(null)
  const [error, setError] = useState<string | null>(null)

  const watch = useQuery({
    queryKey: ['billing-payment', pending?.id],
    queryFn: () => billingApi.payment(pending!.id),
    enabled: !!pending,
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: true,
  })

  useEffect(() => {
    const status = watch.data?.status
    if (!pending || !status || status === 'pending') return
    setPending(null)
    void qc.invalidateQueries({ queryKey: ['billing'] })
    void qc.invalidateQueries({ queryKey: ['organization-info'] })
    if (status === 'paid') toast.success("To'lov qabul qilindi. Obuna uzaytirildi.")
    else setError("To'lov bekor qilindi yoki muddati o'tdi. Qaytadan urinib ko'ring.")
  }, [watch.data?.status, pending, qc, toast])

  const pay = useMutation({
    mutationFn: () => billingApi.checkout({ plan: plan?.code, months, method }),
    onMutate: () => {
      setError(null)
      // Open the tab inside the click, otherwise popup blockers stop it.
      return { tab: window.open('', '_blank') }
    },
    onSuccess: (payment, _vars, ctx) => {
      setPending(payment)
      if (ctx?.tab) ctx.tab.location.href = payment.checkout_url
    },
    onError: (err, _vars, ctx) => {
      ctx?.tab?.close()
      setError(errorMessage(err))
    },
  })

  if (overview.isLoading) return <PageSkeleton stats={2} panels={2} />
  if (overview.isError) return <ErrorState message={errorMessage(overview.error)} onRetry={() => void overview.refetch()} />
  const data = overview.data!
  const plan = data.plans[0]
  const sub = data.subscription
  const end = sub.status === 'trial' ? sub.trial_ends_at : sub.current_period_end
  const left = daysLeft(end)
  const chosen = plan?.periods.find((p) => p.months === months)

  return (
    <div>
      <PageHeader title="Obuna" subtitle="Kutubxona obunasini to'lash va to'lovlar tarixi" />

      <Card className="mb-5 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{sub.plan_name}</h2>
          <Badge tone={STATUS[sub.status].tone}>{STATUS[sub.status].label}</Badge>
        </div>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {end
            ? left !== null && left >= 0
              ? `${formatDate(end)} gacha amal qiladi (${left} kun qoldi).`
              : `${formatDate(end)} da tugagan.`
            : "Tugash sanasi belgilanmagan."}
        </p>
        {data.enforced && sub.status === 'expired' && (
          <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
            Obuna tugagani uchun ma'lumotlarni faqat ko'rish mumkin. To'lovdan keyin hammasi darhol ochiladi.
          </p>
        )}
      </Card>

      {plan ? (
        <Card className="mb-5 p-5">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">Obunani uzaytirish</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            «{plan.name}» tarifi: oyiga {formatMoney(plan.monthly_price)}. Qolgan kunlaringiz saqlanadi, yangi muddat ularning ustiga qo'shiladi.
          </p>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {plan.periods.map((p) => (
              <button
                key={p.months}
                type="button"
                onClick={() => setMonths(p.months)}
                className={clsx(
                  'rounded-xl border p-4 text-left transition',
                  p.months === months
                    ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600 dark:bg-brand-900/20'
                    : 'border-slate-200 hover:border-brand-300 dark:border-slate-700',
                )}
              >
                <div className="flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-200">
                  {periodLabel(p.months)}
                  {p.discount > 0 && <Badge tone="green">-{p.discount}%</Badge>}
                </div>
                <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{formatMoney(p.amount)}</div>
                {p.months > 1 && (
                  <div className="text-xs text-slate-500 dark:text-slate-400">oyiga {formatMoney(Math.round(p.amount / p.months))}</div>
                )}
              </button>
            ))}
          </div>

          <h3 className="mt-5 text-sm font-medium text-slate-700 dark:text-slate-200">To'lov usuli</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {data.methods.map((m) => (
              <button
                key={m.code}
                type="button"
                onClick={() => setMethod(m.code)}
                className={clsx(
                  'rounded-lg border px-3 py-1.5 text-sm transition',
                  m.code === method
                    ? 'border-brand-600 bg-brand-600 text-white'
                    : 'border-slate-200 text-slate-700 hover:border-brand-300 dark:border-slate-700 dark:text-slate-200',
                )}
              >
                {m.name}
              </button>
            ))}
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button onClick={() => pay.mutate()} loading={pay.isPending} disabled={!!pending}>
              {chosen ? `${formatMoney(chosen.amount)} to'lash` : "To'lash"}
            </Button>
            <span className="text-xs text-slate-500 dark:text-slate-400">To'lov Taps orqali xavfsiz amalga oshiriladi.</span>
          </div>
          {error && <div className="mt-3"><ErrorBanner message={error} /></div>}

          {pending && (
            <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50 p-4 text-sm dark:border-brand-800 dark:bg-brand-900/20">
              <div className="flex items-center gap-2 font-medium text-slate-800 dark:text-slate-100">
                <span className="h-2 w-2 animate-pulse rounded-full bg-brand-600" />
                To'lov kutilmoqda: {formatMoney(pending.amount)}, {periodLabel(pending.months)}
              </div>
              <p className="mt-2 text-slate-600 dark:text-slate-300">
                Ochilgan sahifada to'lovni yakunlang. Bu sahifa to'lovni o'zi tekshiradi.{' '}
                <a href={pending.checkout_url} target="_blank" rel="noreferrer" className="font-medium text-brand-700 underline dark:text-brand-300">
                  To'lov sahifasini ochish
                </a>
              </p>
              <button type="button" className="mt-2 text-xs text-slate-500 underline" onClick={() => setPending(null)}>
                Kutishni to'xtatish
              </button>
            </div>
          )}
        </Card>
      ) : (
        <Card className="mb-5 p-5 text-sm text-slate-500">Hozircha pullik tarif yo'q. Platforma administratoriga murojaat qiling.</Card>
      )}

      <Card className="p-0">
        <h2 className="px-5 pt-5 font-semibold text-slate-900 dark:text-slate-100">To'lovlar tarixi</h2>
        {data.payments.length ? (
          <Table className="mt-3">
            <thead>
              <tr className="text-left text-xs uppercase text-slate-500">
                <th className="px-5 py-3">Sana</th>
                <th className="px-5 py-3">Muddat</th>
                <th className="px-5 py-3">Summa</th>
                <th className="px-5 py-3">Usul</th>
                <th className="px-5 py-3">Holat</th>
              </tr>
            </thead>
            <tbody>
              {data.payments.map((p) => (
                <tr key={p.id} className="border-t border-slate-100 text-sm dark:border-slate-700">
                  <td className="px-5 py-3">{formatDateTime(p.created_at)}</td>
                  <td className="px-5 py-3">{periodLabel(p.months)}</td>
                  <td className="px-5 py-3">{formatMoney(p.amount)}</td>
                  <td className="px-5 py-3">{p.method_name}</td>
                  <td className="px-5 py-3"><Badge tone={PAYMENT_STATUS[p.status].tone}>{PAYMENT_STATUS[p.status].label}</Badge></td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <p className="px-5 pb-5 pt-2 text-sm text-slate-500 dark:text-slate-400">Hali to'lov qilinmagan.</p>
        )}
      </Card>
    </div>
  )
}
