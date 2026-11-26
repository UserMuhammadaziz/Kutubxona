import { useMemo, useState } from 'react'
import { matchesSearch } from '../../lib/search'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { platformApi, type OrgStatus, type PlatformOrg, type PlatformOrgForm } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { ActionMenu, type ActionMenuItem } from '../../components/ActionMenu'
import { useToast } from '../../components/Toast'
import { Badge, Button, ConfirmDialog, EmptyState, ErrorBanner, ErrorState, Field, Input, Label, Modal, ResponsiveList, Select, Table, TableSkeleton, Textarea } from '../../components/ui'
import { formatDate } from '../../lib/format'
import { useAuthStore } from '../../store/auth'
import { emptyOrgForm, OrganizationForm } from './OrganizationForm'
import { OrganizationDetails } from './OrganizationDetails'
import { SubscriptionForm } from './SubscriptionForm'
import { bodyClass, headClass, limitText, ORG_STATUS, subscriptionSummary, usePlans } from './shared'

type Action = 'approve' | 'reject' | 'suspend' | 'activate' | 'archive'
type Pending = { org: PlatformOrg; action: Action }

const ACTION_TEXT: Record<Action, { title: string; confirm: string; danger: boolean; reason: boolean; effect: string; done: string }> = {
  approve: { title: 'Arizani tasdiqlash', confirm: 'Tasdiqlash', danger: false, reason: false, effect: 'Tashkilot faol bo‘ladi, xodimlari tizimga kira oladi.', done: 'tasdiqlandi' },
  reject: { title: 'Arizani rad etish', confirm: 'Rad etish', danger: true, reason: true, effect: 'Ariza rad etiladi. Keyin faollashtirish mumkin.', done: 'rad etildi' },
  suspend: { title: "Tashkilotni to'xtatish", confirm: "To'xtatish", danger: true, reason: true, effect: "Xodimlar darhol tizimdan foydalana olmaydi. Ma'lumotlar saqlanadi.", done: "to'xtatildi" },
  activate: { title: 'Tashkilotni faollashtirish', confirm: 'Faollashtirish', danger: false, reason: false, effect: 'Xodimlar yana tizimdan foydalana oladi.', done: 'faollashtirildi' },
  archive: { title: 'Tashkilotni arxivlash', confirm: 'Arxivlash', danger: true, reason: false, effect: "Xodimlar tizimdan foydalana olmaydi. Ma'lumotlar saqlanadi, keyin qayta faollashtirish mumkin.", done: 'arxivlandi' },
}

const FILTERS: { key: OrgStatus | 'all'; label: string }[] = [
  { key: 'all', label: 'Hammasi' },
  { key: 'pending', label: 'Kutilmoqda' },
  { key: 'active', label: 'Faol' },
  { key: 'suspended', label: "To'xtatilgan" },
  { key: 'rejected', label: 'Rad etilgan' },
  { key: 'archived', label: 'Arxivlangan' },
]

function Usage({ label, used, limit }: { label: string; used: number; limit?: number | null }) {
  const ratio = limit ? used / limit : 0
  return (
    <div className="flex items-baseline justify-between gap-3 whitespace-nowrap">
      <dt className="text-slate-600 dark:text-slate-300">{label}</dt>
      <dd
        className={clsx(
          'tabular-nums',
          ratio > 1 ? 'font-semibold text-red-700 dark:text-red-400' : ratio >= 0.8 ? 'font-semibold text-amber-800 dark:text-amber-300' : 'text-slate-900 dark:text-slate-100',
        )}
      >
        {used.toLocaleString('uz-UZ')}
        {limit != null && <span className="font-normal text-slate-600 dark:text-slate-300"> / {limitText(limit)}</span>}
        {ratio > 1 && <span className="sr-only"> (limitdan oshgan)</span>}
      </dd>
    </div>
  )
}

export function OrganizationsTab({ plan, onPlanChange }: { plan: string; onPlanChange: (code: string) => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const stats = useQuery({ queryKey: ['platform', 'stats'], queryFn: platformApi.stats })
  const plans = usePlans()
  const [filter, setFilter] = useState<OrgStatus | 'all'>('all')
  const [q, setQ] = useState('')
  const [pending, setPending] = useState<Pending | null>(null)
  const [reason, setReason] = useState('')
  const [planOrg, setPlanOrg] = useState<PlatformOrg | null>(null)
  const [editing, setEditing] = useState<{ id: number | null; form: PlatformOrgForm } | null>(null)
  const [deleting, setDeleting] = useState<PlatformOrg | null>(null)
  const [viewing, setViewing] = useState<PlatformOrg | null>(null)

  const refresh = () => void qc.invalidateQueries({ queryKey: ['platform'] })

  const statusMut = useMutation({
    mutationFn: ({ org, action }: Pending) => platformApi.setStatus(org.id, action, reason.trim()),
    onSuccess: (_, { org, action }) => {
      setPending(null)
      toast.success(`«${org.nomi}» ${ACTION_TEXT[action].done}.`)
      refresh()
      // The admin may be a member of this library: keep the own status in sync.
      void useAuthStore.getState().refresh().catch(() => undefined)
    },
  })
  const removeMut = useMutation({
    mutationFn: (org: PlatformOrg) => platformApi.remove(org.id),
    onSuccess: (_, org) => {
      setDeleting(null)
      toast.success(`«${org.nomi}» o'chirildi.`)
      refresh()
    },
  })
  const openEdit = useMutation({
    mutationFn: (org: PlatformOrg) => platformApi.get(org.id),
    onSuccess: (d, org) => setEditing({ id: org.id, form: { ...emptyOrgForm(), ...d, owner: undefined } }),
    onError: (e) => toast.error(errorMessage(e)),
  })

  function ask(org: PlatformOrg, action: Action) {
    statusMut.reset()
    setReason('')
    setPending({ org, action })
  }

  const rows = useMemo(() => {
    const needle = q.trim()
    return (stats.data?.tashkilotlar ?? [])
      .filter(
        (o) =>
          (filter === 'all' || o.status === filter) &&
          (!plan || o.subscription?.plan === plan) &&
          (!needle || matchesSearch([o.nomi, o.slug, o.egasi_ismi, o.telefon].join(' '), needle)),
      )
      // New applications wait for a decision, so they come first.
      .sort((a, b) => Number(b.status === 'pending') - Number(a.status === 'pending'))
  }, [stats.data, filter, q, plan])

  if (stats.isLoading) return <TableSkeleton rows={6} cols={6} />
  if (stats.isError || !stats.data)
    return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(stats.error)} onRetry={() => void stats.refetch()} retrying={stats.isFetching} />

  const { holatlar: counts, jami } = stats.data
  const create = () => setEditing({ id: null, form: emptyOrgForm() })
  const filtered = filter !== 'all' || !!q.trim() || !!plan
  const clear = () => {
    setFilter('all')
    setQ('')
    onPlanChange('')
  }
  const txt = pending ? ACTION_TEXT[pending.action] : null
  const statusError = statusMut.error ? errorMessage(statusMut.error) : null

  const primary = (o: PlatformOrg) =>
    o.status === 'pending' ? (
      <Button size="sm" onClick={() => ask(o, 'approve')}>Tasdiqlash</Button>
    ) : o.status === 'active' ? (
      <Button size="sm" variant="secondary" onClick={() => setPlanOrg(o)}>Obuna</Button>
    ) : (
      <Button size="sm" variant="secondary" onClick={() => ask(o, 'activate')}>Faollashtirish</Button>
    )

  const menu = (o: PlatformOrg) => {
    const items: ActionMenuItem[] = [{ label: 'Tahrirlash', onSelect: () => openEdit.mutate(o) }]
    if (o.status !== 'active') items.push({ label: 'Obuna', onSelect: () => setPlanOrg(o) })
    if (o.status === 'pending') items.push({ label: 'Rad etish', danger: true, separated: true, onSelect: () => ask(o, 'reject') })
    if (o.status === 'active') items.push({ label: "To'xtatish", danger: true, separated: true, onSelect: () => ask(o, 'suspend') })
    if (o.status !== 'archived') items.push({ label: 'Arxivlash', danger: true, separated: o.status !== 'active' && o.status !== 'pending', onSelect: () => ask(o, 'archive') })
    else items.push({ label: "O'chirish", danger: true, separated: true, onSelect: () => { removeMut.reset(); setDeleting(o) } })
    return <ActionMenu label={`«${o.nomi}» amallari`} items={items} />
  }

  const statusCell = (o: PlatformOrg) => (
    <>
      <Badge tone={ORG_STATUS[o.status]?.tone}>{ORG_STATUS[o.status]?.label ?? o.status}</Badge>
      {o.status_reason && <div className="mt-1 max-w-[14rem] break-words text-xs text-slate-600 dark:text-slate-300">{o.status_reason}</div>}
    </>
  )
  const planCell = (o: PlatformOrg) => {
    if (!o.subscription) return <span className="text-slate-600 dark:text-slate-300">Biriktirilmagan</span>
    const { text, tone } = subscriptionSummary(o.subscription)
    return (
      <>
        <div className="font-medium text-slate-900 dark:text-slate-100">{o.subscription.plan_name}</div>
        <div
          className={clsx(
            'text-xs whitespace-nowrap',
            tone === 'bad' ? 'text-red-700 dark:text-red-400' : tone === 'warn' ? 'text-amber-800 dark:text-amber-300' : 'text-slate-600 dark:text-slate-300',
          )}
        >
          {text}
        </div>
      </>
    )
  }
  const usageCell = (o: PlatformOrg, className: string) => (
    <dl className={clsx('text-xs', className)}>
      <Usage label="Kitob" used={o.kitoblar} limit={o.subscription?.limits.max_resources} />
      <Usage label="Kitobxon" used={o.oquvchilar} limit={o.subscription?.limits.max_customers} />
      <Usage label="Xodim" used={o.azoliklar} limit={o.subscription?.limits.max_staff} />
      <Usage label="Berish" used={o.berishlar} />
    </dl>
  )
  const nameButton = (o: PlatformOrg) => (
    <button
      type="button"
      onClick={() => setViewing(o)}
      className="break-words text-left font-medium text-slate-900 underline-offset-2 hover:text-brand-700 hover:underline dark:text-slate-100 dark:hover:text-brand-300"
    >
      {o.nomi}
    </button>
  )
  const meta = (o: PlatformOrg) => `${o.slug} · ${formatDate(o.yaratilgan)}${o.bot_ulangan ? ' · bot ulangan' : ''}`

  return (
    <div>
      <div className="-mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0" role="group" aria-label="Holat bo'yicha filtr">
        {FILTERS.map((f) => {
          const count = f.key === 'all' ? jami : (counts[f.key] ?? 0)
          const on = filter === f.key
          return (
            <button
              key={f.key}
              type="button"
              aria-pressed={on}
              onClick={() => setFilter(f.key)}
              className={clsx(
                'inline-flex min-h-9 shrink-0 items-center gap-2 rounded-full border px-3 text-sm font-medium whitespace-nowrap transition-colors',
                on
                  ? 'border-brand-700 bg-brand-50 text-brand-800 dark:border-brand-400 dark:bg-brand-900/40 dark:text-brand-200'
                  : 'border-slate-300 text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700',
              )}
            >
              {f.label}
              <span className={clsx('tabular-nums', f.key === 'pending' && count > 0 ? 'font-bold text-amber-800 dark:text-amber-300' : 'font-normal')}>{count}</span>
            </button>
          )
        })}
      </div>

      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="sm:w-72">
          <Input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nomi, egasi yoki telefon" aria-label="Tashkilotni qidirish" />
        </div>
        <div className="sm:w-52">
          <Select value={plan} onChange={(e) => onPlanChange(e.target.value)} aria-label="Tarif bo'yicha filtr">
            <option value="">Barcha tariflar</option>
            {(plans.data ?? []).map((p) => (
              <option key={p.code} value={p.code}>{p.nomi}</option>
            ))}
          </Select>
        </div>
        <Button className="sm:ml-auto" onClick={create}>Yangi tashkilot</Button>
      </div>

      <ResponsiveList
        items={rows}
        empty={
          filtered ? (
            <EmptyState title="Tashkilot topilmadi" description="Bu filtr bo'yicha tashkilot yo'q." action={<Button variant="secondary" onClick={clear}>Filtrni tozalash</Button>} />
          ) : (
            <EmptyState title="Hali tashkilot yo'q" description="Birinchi tashkilotni yarating yoki ariza kelishini kuting." action={<Button onClick={create}>Yangi tashkilot</Button>} />
          )
        }
        render={(o) => (
          <div>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                {nameButton(o)}
                <div className="break-words text-xs text-slate-600 dark:text-slate-300">{meta(o)}</div>
              </div>
              <div className="shrink-0 text-right">{statusCell(o)}</div>
            </div>
            {(o.egasi_ismi || o.telefon) && <div className="mt-2 text-sm">{[o.egasi_ismi, o.telefon].filter(Boolean).join(', ')}</div>}
            <div className="mt-2 text-sm">{planCell(o)}</div>
            {usageCell(o, 'mt-2 grid grid-cols-2 gap-x-6 gap-y-1')}
            <div className="mt-3 flex items-center justify-between gap-2">
              {primary(o)}
              {menu(o)}
            </div>
          </div>
        )}
      >
        <Table>
          <thead className={headClass}>
            <tr>
              <th className="px-4 py-3">Tashkilot</th>
              <th className="px-4 py-3">Egasi</th>
              <th className="px-4 py-3">Holat</th>
              <th className="px-4 py-3">Tarif</th>
              <th className="px-4 py-3">Foydalanish</th>
              <th className="px-4 py-3"><span className="sr-only">Amallar</span></th>
            </tr>
          </thead>
          <tbody className={bodyClass}>
            {rows.map((o) => (
              <tr key={o.id}>
                <td className="px-4 py-3">
                  {nameButton(o)}
                  <div className="text-xs text-slate-600 dark:text-slate-300">{meta(o)}</div>
                </td>
                <td className="px-4 py-3">
                  <div>{o.egasi_ismi || '—'}</div>
                  <div className="text-xs whitespace-nowrap text-slate-600 dark:text-slate-300">{o.telefon}</div>
                </td>
                <td className="px-4 py-3">{statusCell(o)}</td>
                <td className="px-4 py-3">{planCell(o)}</td>
                <td className="px-4 py-3">{usageCell(o, 'w-40')}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    {primary(o)}
                    {menu(o)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </ResponsiveList>

      <ConfirmDialog
        open={!!pending && !txt?.reason}
        title={txt?.title ?? ''}
        message={pending && <><ErrorBanner message={statusError} /><strong className="font-semibold">«{pending.org.nomi}».</strong> {txt?.effect}</>}
        confirmLabel={txt?.confirm}
        variant={txt?.danger ? 'danger' : 'primary'}
        loading={statusMut.isPending}
        onConfirm={() => pending && statusMut.mutate(pending)}
        onCancel={() => setPending(null)}
      />

      <Modal open={!!pending && !!txt?.reason} onClose={() => setPending(null)} title={txt?.title ?? ''} description={pending?.org.nomi}>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (pending) statusMut.mutate(pending)
          }}
        >
          <ErrorBanner message={statusError} />
          <p className="mb-4 text-sm text-slate-700 dark:text-slate-300">{txt?.effect}</p>
          <Field>
            <Label htmlFor="reason">Sabab (egasiga ko'rsatiladi)</Label>
            <Textarea id="reason" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
          </Field>
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={() => setPending(null)}>Bekor qilish</Button>
            <Button type="submit" variant="danger" loading={statusMut.isPending}>{txt?.confirm}</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!deleting}
        title="Tashkilotni o'chirish"
        variant="danger"
        confirmLabel="Butunlay o'chirish"
        loading={removeMut.isPending}
        message={deleting && <><ErrorBanner message={removeMut.error ? errorMessage(removeMut.error) : null} />«{deleting.nomi}» va uning barcha ma'lumotlari ({deleting.kitoblar} kitob, {deleting.oquvchilar} kitobxon) butunlay o'chiriladi. Bu amalni qaytarib bo'lmaydi.</>}
        onConfirm={() => deleting && removeMut.mutate(deleting)}
        onCancel={() => setDeleting(null)}
      />

      <Modal wide open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? 'Tashkilotni tahrirlash' : 'Yangi tashkilot'} description={editing?.id ? undefined : "Tashkilot darhol faol bo'ladi."}>
        {editing && <OrganizationForm id={editing.id} initial={editing.form} onClose={() => setEditing(null)} />}
      </Modal>

      <Modal wide open={!!viewing} onClose={() => setViewing(null)} title={viewing?.nomi ?? ''} description="Tashkilot haqida to'liq ma'lumot">
        {viewing && <OrganizationDetails id={viewing.id} actions={<>{primary(viewing)}{menu(viewing)}</>} />}
      </Modal>

      <Modal open={!!planOrg} onClose={() => setPlanOrg(null)} title="Obuna" description={planOrg?.nomi}>
        {planOrg && <SubscriptionForm org={planOrg} onClose={() => setPlanOrg(null)} />}
      </Modal>
    </div>
  )
}
