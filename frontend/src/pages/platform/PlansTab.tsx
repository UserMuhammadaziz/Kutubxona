import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { platformApi, type PlanLimits, type PlatformPlan, type PlatformPlanForm } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { ActionMenu } from '../../components/ActionMenu'
import { Checkbox, Switch } from '../../components/controls'
import { useToast } from '../../components/Toast'
import { Badge, Button, ConfirmDialog, EmptyState, ErrorBanner, ErrorState, Field, Input, Label, Modal, ResponsiveList, Table, TableSkeleton, Textarea } from '../../components/ui'
import { bodyClass, formError, headClass, limitText, planPrice, usePlans } from './shared'

const LIMITS: { key: keyof PlanLimits; label: string; unit: string; initial: number }[] = [
  { key: 'max_staff', label: 'Xodimlar', unit: 'xodim', initial: 5 },
  { key: 'max_resources', label: 'Kitoblar', unit: 'kitob', initial: 1000 },
  { key: 'max_customers', label: 'Kitobxonlar', unit: 'kitobxon', initial: 1000 },
]

const emptyForm = (): PlatformPlanForm => ({
  nomi: '',
  tavsif: '',
  narx_oylik: '',
  max_staff: 5,
  max_resources: 1000,
  max_customers: 1000,
  faol: true,
})

const toForm = (p: PlatformPlan): PlatformPlanForm => ({
  nomi: p.nomi,
  tavsif: p.tavsif,
  narx_oylik: String(Math.round(Number(p.narx_oylik))),
  max_staff: p.max_staff,
  max_resources: p.max_resources,
  max_customers: p.max_customers,
  faol: p.faol,
})

const digits = (value: string, max: number) => value.replace(/\D/g, '').slice(0, max)
const grouped = (value: string) => (value ? Number(value).toLocaleString('uz-UZ') : '')

type Editing = { plan: PlatformPlan | null; form: PlatformPlanForm }

function PlanForm({ editing, onClose }: { editing: Editing; onClose: () => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const { plan } = editing
  const [form, setForm] = useState(editing.form)
  // Kept per limit, so unticking "Cheksiz" brings the typed number back.
  const [remembered, setRemembered] = useState<Partial<Record<keyof PlanLimits, number>>>({})

  const save = useMutation({
    mutationFn: () => {
      const payload = { ...form, nomi: form.nomi.trim(), tavsif: form.tavsif.trim(), narx_oylik: form.narx_oylik || '0' }
      return plan ? platformApi.updatePlan(plan.id, payload) : platformApi.createPlan(payload)
    },
    onSuccess: (saved) => {
      void qc.invalidateQueries({ queryKey: ['platform'] })
      toast.success(plan ? `«${saved.nomi}» tarifi saqlandi.` : `«${saved.nomi}» tarifi yaratildi.`)
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
      <ErrorBanner message={formError(save.error)} />
      {plan && plan.organization_count > 0 && (
        <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
          Bu tarifda {plan.organization_count} ta tashkilot bor. O'zgarish ularga darhol ta'sir qiladi.
        </p>
      )}
      <div className="grid gap-x-4 sm:grid-cols-2">
        <Field>
          <Label htmlFor="plan-name">Nomi</Label>
          <Input id="plan-name" required minLength={2} maxLength={80} autoFocus value={form.nomi} onChange={(e) => setForm({ ...form, nomi: e.target.value })} placeholder="Masalan, Standart" />
        </Field>
        <Field>
          <Label htmlFor="plan-price">Narxi, oyiga</Label>
          <div className="relative">
            <Input
              id="plan-price"
              inputMode="numeric"
              className="pr-14 tabular-nums"
              value={grouped(form.narx_oylik)}
              onChange={(e) => setForm({ ...form, narx_oylik: digits(e.target.value, 10) })}
              placeholder="0"
              aria-describedby="plan-price-hint"
            />
            <span aria-hidden className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-slate-600 dark:text-slate-300">so'm</span>
          </div>
          <p id="plan-price-hint" className="mt-1 text-xs text-slate-600 dark:text-slate-300">Bo'sh yoki 0 bo'lsa, bepul.</p>
        </Field>
      </div>
      <Field>
        <Label htmlFor="plan-description">Izoh (ixtiyoriy)</Label>
        <Textarea id="plan-description" rows={2} value={form.tavsif} onChange={(e) => setForm({ ...form, tavsif: e.target.value })} placeholder="Kimlar uchun mo'ljallangan" />
      </Field>

      <fieldset className="mb-4">
        <legend className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">Limitlar</legend>
        <div className="divide-y divide-slate-200 border-y border-slate-200 dark:divide-slate-700 dark:border-slate-700">
          {LIMITS.map(({ key, label, unit, initial }) => {
            const value = form[key]
            return (
              <div key={key} className="flex flex-wrap items-center gap-x-3 gap-y-2 py-2.5 sm:gap-x-4">
                <label htmlFor={`plan-${key}`} className="min-w-20 flex-1 text-sm text-slate-800 dark:text-slate-100">{label}</label>
                <Input
                  id={`plan-${key}`}
                  inputMode="numeric"
                  className="!w-24 text-right sm:!w-32 tabular-nums"
                  required={value != null}
                  disabled={value == null}
                  value={value == null ? '' : value ? grouped(String(value)) : ''}
                  placeholder={value == null ? 'Cheksiz' : unit}
                  onChange={(e) => setForm({ ...form, [key]: Number(digits(e.target.value, 9)) })}
                />
                <Checkbox
                  checked={value == null}
                  label="Cheksiz"
                  onChange={(unlimited) => {
                    if (unlimited) setRemembered({ ...remembered, [key]: value || initial })
                    setForm({ ...form, [key]: unlimited ? null : (remembered[key] ?? initial) })
                  }}
                />
              </div>
            )
          })}
        </div>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">
          Xodimlar limiti avtomatik cheklanadi. Kitob va kitobxon limiti hozircha faqat shu panelda ko'rsatiladi.
        </p>
      </fieldset>

      {!plan?.is_default && (
        <Switch checked={form.faol} onChange={(faol) => setForm({ ...form, faol })} label="Tashkilotlarga taklif qilinsin" />
      )}
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose}>Bekor qilish</Button>
        <Button type="submit" loading={save.isPending}>{plan ? 'Saqlash' : 'Tarif yaratish'}</Button>
      </div>
    </form>
  )
}

export function PlansTab({ onShowOrganizations }: { onShowOrganizations: (planCode: string) => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const plans = usePlans()
  const [editing, setEditing] = useState<Editing | null>(null)
  const [removing, setRemoving] = useState<PlatformPlan | null>(null)

  const refresh = () => void qc.invalidateQueries({ queryKey: ['platform'] })
  const fail = (e: unknown) => toast.error(errorMessage(e))

  const toggle = useMutation({
    mutationFn: (p: PlatformPlan) => platformApi.updatePlan(p.id, { faol: !p.faol }),
    onSuccess: (p) => {
      toast.success(
        p.faol
          ? `«${p.nomi}» tarifi yana taklif qilinadi.`
          : `«${p.nomi}» tarifi endi taklif qilinmaydi. Undagi tashkilotlar o'z tarifida qoladi.`,
      )
    },
    onError: fail,
    onSettled: refresh,
  })
  const move = useMutation({
    mutationFn: async ({ plan, step }: { plan: PlatformPlan; step: -1 | 1 }) => {
      const list = [...(plans.data ?? [])]
      const i = list.findIndex((p) => p.id === plan.id)
      list.splice(i + step, 0, ...list.splice(i, 1))
      for (const [index, p] of list.entries()) {
        if (p.tartib !== index + 1) await platformApi.updatePlan(p.id, { tartib: index + 1 })
      }
    },
    onError: fail,
    onSettled: refresh,
  })
  const remove = useMutation({
    mutationFn: (p: PlatformPlan) => platformApi.removePlan(p.id),
    onSuccess: (_, p) => {
      toast.success(`«${p.nomi}» tarifi o'chirildi.`)
      setRemoving(null)
      refresh()
    },
  })

  if (plans.isLoading) return <TableSkeleton rows={3} cols={6} />
  if (plans.isError || !plans.data)
    return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(plans.error)} onRetry={() => void plans.refetch()} retrying={plans.isFetching} />

  const list = plans.data
  const create = () => setEditing({ plan: null, form: emptyForm() })

  const menu = (p: PlatformPlan, i: number) => (
    <ActionMenu
      label={`«${p.nomi}» tarifi amallari`}
      items={[
        { label: 'Tahrirlash', onSelect: () => setEditing({ plan: p, form: toForm(p) }) },
        { label: 'Nusxa olish', onSelect: () => setEditing({ plan: null, form: { ...toForm(p), nomi: `${p.nomi} nusxasi`, faol: true } }) },
        { label: 'Yuqoriga surish', onSelect: () => move.mutate({ plan: p, step: -1 }), disabled: i === 0 || move.isPending },
        { label: 'Pastga surish', onSelect: () => move.mutate({ plan: p, step: 1 }), disabled: i === list.length - 1 || move.isPending },
        ...(p.is_default
          ? []
          : [{ label: p.organization_count ? "O'chirish (ishlatilmoqda)" : "O'chirish", danger: true, disabled: p.organization_count > 0, separated: true, onSelect: () => { remove.reset(); setRemoving(p) } }]),
      ]}
    />
  )
  const state = (p: PlatformPlan) =>
    p.is_default ? (
      <span className="text-sm text-slate-600 dark:text-slate-300">Doim yoqiq</span>
    ) : (
      <Switch
        checked={p.faol}
        disabled={toggle.isPending}
        onChange={() => toggle.mutate(p)}
        label={<><span className="sr-only">«{p.nomi}»: </span>{p.faol ? 'Yoqiq' : "O'chiq"}</>}
      />
    )
  const orgs = (p: PlatformPlan) =>
    p.organization_count ? (
      <button type="button" onClick={() => onShowOrganizations(p.code)} className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700 dark:text-brand-300">
        {p.organization_count} ta
      </button>
    ) : (
      <span className="text-slate-600 dark:text-slate-300">Yo'q</span>
    )
  const title = (p: PlatformPlan) => (
    <>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="font-medium text-slate-900 dark:text-slate-100">{p.nomi}</span>
        {p.is_default && <Badge tone="green">Boshlang'ich</Badge>}
      </div>
      {(p.tavsif || p.is_default) && (
        <div className="mt-0.5 max-w-[18rem] break-words text-xs text-slate-600 dark:text-slate-300">
          {p.tavsif || "Yangi tashkilotlarga avtomatik beriladi."}
        </div>
      )}
    </>
  )

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-[65ch] text-sm text-slate-600 dark:text-slate-300">
          Tarifni tashkilotga biriktirish: Tashkilotlar bo'limida «Obuna».
        </p>
        <Button className="shrink-0" onClick={create}>Yangi tarif</Button>
      </div>

      <ResponsiveList
        items={list}
        empty={<EmptyState title="Hali tarif yo'q" description="Narx va limitlarni belgilab birinchi tarifni yarating, keyin uni tashkilotlarga biriktiring." action={<Button onClick={create}>Yangi tarif</Button>} />}
        render={(p) => (
          <div>
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">{title(p)}</div>
              {menu(p, list.indexOf(p))}
            </div>
            <div className="mt-2 text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
              {planPrice(p.narx_oylik)}
              {Number(p.narx_oylik) > 0 && <span className="text-sm font-normal text-slate-600 dark:text-slate-300"> / oy</span>}
            </div>
            <dl className="mt-2 grid grid-cols-3 gap-2 text-sm">
              {LIMITS.map((l) => (
                <div key={l.key}>
                  <dt className="text-xs text-slate-600 dark:text-slate-300">{l.label}</dt>
                  <dd className="tabular-nums">{limitText(p[l.key])}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-3 flex items-center justify-between gap-2 text-sm">
              <span>Tashkilotlar: {orgs(p)}</span>
              {state(p)}
            </div>
          </div>
        )}
      >
        <Table>
          <thead className={headClass}>
            <tr>
              <th className="px-4 py-3">Tarif</th>
              <th className="px-4 py-3 text-right">Oyiga</th>
              {LIMITS.map((l) => (
                <th key={l.key} className="px-4 py-3 text-right">{l.label}</th>
              ))}
              <th className="px-4 py-3">Tashkilotlar</th>
              <th className="px-4 py-3">Taklif</th>
              <th className="px-4 py-3"><span className="sr-only">Amallar</span></th>
            </tr>
          </thead>
          <tbody className={bodyClass}>
            {list.map((p, i) => (
              <tr key={p.id}>
                <td className="px-4 py-3">{title(p)}</td>
                <td className="px-4 py-3 text-right font-medium whitespace-nowrap tabular-nums">{planPrice(p.narx_oylik)}</td>
                {LIMITS.map((l) => (
                  <td key={l.key} className="px-4 py-3 text-right tabular-nums">{limitText(p[l.key])}</td>
                ))}
                <td className="px-4 py-3 tabular-nums">{orgs(p)}</td>
                <td className="px-4 py-3 whitespace-nowrap">{state(p)}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <Button size="sm" variant="secondary" onClick={() => setEditing({ plan: p, form: toForm(p) })}>Tahrirlash</Button>
                    {menu(p, i)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </ResponsiveList>

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.plan ? 'Tarifni tahrirlash' : 'Yangi tarif'} description={editing?.plan?.nomi}>
        {editing && <PlanForm editing={editing} onClose={() => setEditing(null)} />}
      </Modal>

      <ConfirmDialog
        open={!!removing}
        title="Tarifni o'chirish"
        confirmLabel="O'chirish"
        loading={remove.isPending}
        message={
          removing && (
            <>
              <ErrorBanner message={remove.error ? errorMessage(remove.error) : null} />
              {`«${removing.nomi}» tarifi butunlay o'chiriladi.`}
            </>
          )
        }
        onConfirm={() => removing && remove.mutate(removing)}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}
