import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { platformApi, type PlanLimits, type PlatformOrg, type SubscriptionStatus } from '../../api/resources'
import { DatePicker, parseISO, toISO } from '../../components/DatePicker'
import { useToast } from '../../components/Toast'
import { Button, ErrorBanner, Field, Label, Select } from '../../components/ui'
import { formError, limitText, planPrice, SUBSCRIPTION_LABELS, usePlans } from './shared'

const NO_DATE: SubscriptionStatus[] = ['canceled', 'expired']

const toLocalDate = (value: string | null) => (value ? toISO(new Date(value)) : '')

/** A period ends with the chosen day, not at its first minute. */
function endOfDay(value: string): string | null {
  const day = parseISO(value)
  return day ? new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59).toISOString() : null
}

/** Adds months to the current end, or to today when the period is over. Clamps 31 Jan + 1 to the last day of February. */
function extend(value: string, months: number): string {
  const now = new Date()
  const current = parseISO(value)
  const base = current && current > now ? current : now
  const last = new Date(base.getFullYear(), base.getMonth() + months + 1, 0).getDate()
  return toISO(new Date(base.getFullYear(), base.getMonth() + months, Math.min(base.getDate(), last)))
}

const USAGE: { key: keyof PlanLimits; label: string; used: (o: PlatformOrg) => number }[] = [
  { key: 'max_staff', label: 'Xodim', used: (o) => o.azoliklar },
  { key: 'max_resources', label: 'Kitob', used: (o) => o.kitoblar },
  { key: 'max_customers', label: 'Kitobxon', used: (o) => o.oquvchilar },
]

export function SubscriptionForm({ org, onClose }: { org: PlatformOrg; onClose: () => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const plans = usePlans()
  const sub = org.subscription
  const [chosen, setChosen] = useState(sub?.plan ?? '')
  const [status, setStatus] = useState<SubscriptionStatus>(sub?.status ?? 'active')
  const [date, setDate] = useState(sub ? toLocalDate(sub.status === 'trial' ? sub.trial_ends_at : sub.current_period_end) : '')

  const options = (plans.data ?? []).filter((p) => p.faol || p.code === sub?.plan)
  const planCode = chosen || options.find((p) => p.is_default)?.code || options[0]?.code || ''
  const plan = options.find((p) => p.code === planCode)
  const hasDate = !NO_DATE.includes(status)
  const past = hasDate && !!date && date < toISO(new Date())
  const over = plan ? USAGE.filter((u) => plan[u.key] != null && u.used(org) > plan[u.key]!) : []

  const save = useMutation({
    mutationFn: () => {
      const end = endOfDay(date)
      return platformApi.setSubscription(org.id, {
        plan: planCode || undefined,
        status,
        // Closed subscriptions keep the dates they had.
        ...(!hasDate ? {} : status === 'trial' ? { trial_ends_at: end, current_period_end: null } : { current_period_end: end }),
      })
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform'] })
      toast.success(`«${org.nomi}» obunasi saqlandi.`)
      onClose()
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate()
      }}
    >
      <ErrorBanner message={formError(save.error ?? plans.error)} />
      {sub?.effective_status === 'expired' && sub.status !== 'expired' && (
        <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
          Obuna muddati o'tib ketgan. Uzaytirish uchun yangi sanani tanlang.
        </p>
      )}
      <Field>
        <Label htmlFor="sub-plan">Tarif</Label>
        <Select id="sub-plan" value={planCode} onChange={(e) => setChosen(e.target.value)} disabled={plans.isLoading}>
          {options.map((p) => (
            <option key={p.code} value={p.code}>
              {`${p.nomi}${p.faol ? '' : ' (taklif qilinmaydi)'}, ${planPrice(p.narx_oylik)}${Number(p.narx_oylik) ? ' / oy' : ''}`}
            </option>
          ))}
        </Select>
        {plan && (
          <dl className="mt-2 grid grid-cols-3 gap-2 text-sm">
            {USAGE.map((u) => (
              <div key={u.key}>
                <dt className="text-xs text-slate-600 dark:text-slate-300">{u.label}</dt>
                <dd className={over.includes(u) ? 'font-medium tabular-nums text-red-700 dark:text-red-400' : 'tabular-nums'}>
                  {u.used(org).toLocaleString('uz-UZ')} / {limitText(plan[u.key])}
                </dd>
              </div>
            ))}
          </dl>
        )}
        {over.length > 0 && (
          <p className="mt-2 text-sm text-red-700 dark:text-red-400">
            Tashkilot bu tarif limitidan oshgan: {over.map((u) => u.label.toLowerCase()).join(', ')}.
          </p>
        )}
      </Field>
      <Field>
        <Label htmlFor="sub-status">Obuna holati</Label>
        <Select id="sub-status" value={status} onChange={(e) => setStatus(e.target.value as SubscriptionStatus)}>
          {Object.entries(SUBSCRIPTION_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
      </Field>
      {hasDate && (
        <Field>
          <Label htmlFor="sub-end">{status === 'trial' ? 'Sinov tugash sanasi' : 'Obuna tugash sanasi'}</Label>
          <DatePicker id="sub-end" value={date} onChange={setDate} />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {([[1, '+1 oy'], [3, '+3 oy'], [6, '+6 oy'], [12, '+1 yil']] as const).map(([months, label]) => (
              <Button key={months} type="button" size="sm" variant="secondary" onClick={() => setDate(extend(date, months))}>{label}</Button>
            ))}
          </div>
          <p className={past ? 'mt-2 text-sm text-amber-800 dark:text-amber-300' : 'mt-2 text-xs text-slate-600 dark:text-slate-300'}>
            {past ? "Bu sana o'tib ketgan: obuna muddati tugagan deb ko'rsatiladi." : "Sana bo'sh qolsa, obuna muddatsiz."}
          </p>
        </Field>
      )}
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose}>Bekor qilish</Button>
        <Button type="submit" loading={save.isPending} disabled={!planCode}>Saqlash</Button>
      </div>
    </form>
  )
}
