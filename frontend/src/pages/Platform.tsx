import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  healthApi,
  platformApi,
  type HealthState,
  type OrgStatus,
  type PlatformOrg,
  type PlatformOrgForm,
} from '../api/resources'
import { errorMessage } from '../api/client'
import { Badge, Button, ConfirmDialog, EmptyState, ErrorBanner, ErrorState, Field, Input, Label, Modal, PageHeader, PageSkeleton, Select, StatsSkeleton, Table, TableSkeleton, Textarea } from '../components/ui'
import { formatDate, formatDateTime } from '../lib/format'

const STATUS: Record<OrgStatus, { label: string; tone: 'slate' | 'green' | 'red' | 'amber' | 'blue' }> = {
  pending: { label: 'Kutilmoqda', tone: 'amber' },
  active: { label: 'Faol', tone: 'green' },
  rejected: { label: 'Rad etilgan', tone: 'red' },
  suspended: { label: "To'xtatilgan", tone: 'red' },
  archived: { label: 'Arxivlangan', tone: 'slate' },
}

const ORG_TYPES: [string, string][] = [
  ['library', 'Kutubxona'],
  ['school', "Maktab / ta'lim muassasasi"],
  ['university', 'Universitet / kollej'],
  ['office', 'Ofis / tashkilot'],
  ['other', 'Boshqa'],
]

const emptyOrgForm = (): PlatformOrgForm => ({
  nomi: '',
  slug: '',
  turi: 'library',
  tavsif: '',
  telefon: '',
  email: '',
  manzil: '',
  logo_url: '',
  muddat_kun: 14,
  kunlik_jarima: 5000,
  limit_kitob: 3,
  owner: { telefon: '+998', full_name: '', password: '' },
})

const SUB_STATUS = [
  ['trial', 'Sinov muddati'],
  ['active', 'Faol'],
  ['past_due', "To'lov kechikkan"],
  ['canceled', 'Bekor qilingan'],
  ['expired', 'Muddati tugagan'],
] as const

type Pending = { org: PlatformOrg; action: 'approve' | 'reject' | 'suspend' | 'activate' | 'archive' }

const ACTION_TEXT: Record<Pending['action'], { title: string; confirm: string; danger: boolean; reason: boolean }> = {
  approve: { title: 'Arizani tasdiqlash', confirm: 'Tasdiqlash', danger: false, reason: false },
  reject: { title: 'Arizani rad etish', confirm: 'Rad etish', danger: true, reason: true },
  suspend: { title: "Tashkilotni to'xtatish", confirm: "To'xtatish", danger: true, reason: true },
  activate: { title: 'Tashkilotni faollashtirish', confirm: 'Faollashtirish', danger: false, reason: false },
  archive: { title: 'Tashkilotni arxivlash', confirm: 'Arxivlash', danger: true, reason: false },
}

function OrgsTab() {
  const qc = useQueryClient()
  const stats = useQuery({ queryKey: ['platform', 'stats'], queryFn: platformApi.stats })
  const plans = useQuery({ queryKey: ['platform', 'plans'], queryFn: platformApi.plans })
  const [filter, setFilter] = useState<OrgStatus | 'all'>('all')
  const [q, setQ] = useState('')
  const [pending, setPending] = useState<Pending | null>(null)
  const [reason, setReason] = useState('')
  const [planOrg, setPlanOrg] = useState<PlatformOrg | null>(null)
  const [plan, setPlan] = useState('')
  const [subStatus, setSubStatus] = useState('trial')
  const [error, setError] = useState<string | null>(null)
  const [orgForm, setOrgForm] = useState<PlatformOrgForm | null>(null)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteOrg, setDeleteOrg] = useState<PlatformOrg | null>(null)

  const refresh = () => void qc.invalidateQueries({ queryKey: ['platform'] })

  const statusMut = useMutation({
    mutationFn: ({ org, action }: Pending) => platformApi.setStatus(org.id, action, reason.trim()),
    onSuccess: () => {
      setPending(null)
      setReason('')
      setError(null)
      refresh()
    },
    onError: (e) => setError(errorMessage(e)),
  })
  const subMut = useMutation({
    mutationFn: () => platformApi.setSubscription(planOrg!.id, { plan: plan || undefined, status: subStatus }),
    onSuccess: () => {
      setPlanOrg(null)
      setError(null)
      refresh()
    },
    onError: (e) => setError(errorMessage(e)),
  })

  const saveMut = useMutation({
    mutationFn: (f: PlatformOrgForm) => {
      const { owner, slug, ...rest } = f
      return editId
        ? platformApi.update(editId, { ...rest, slug: slug || undefined })
        : platformApi.create({ ...rest, slug: slug || undefined, owner })
    },
    onSuccess: () => {
      setOrgForm(null)
      setEditId(null)
      setError(null)
      refresh()
    },
    onError: (e) => setError(errorMessage(e)),
  })
  const removeMut = useMutation({
    mutationFn: (id: number) => platformApi.remove(id),
    onSuccess: () => {
      setDeleteOrg(null)
      setError(null)
      refresh()
    },
    onError: (e) => setError(errorMessage(e)),
  })

  async function openEdit(o: PlatformOrg) {
    setError(null)
    try {
      const d = await platformApi.get(o.id)
      setEditId(o.id)
      setOrgForm({ ...emptyOrgForm(), ...d, owner: undefined })
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (stats.data?.tashkilotlar ?? []).filter(
      (o) =>
        (filter === 'all' || o.status === filter) &&
        (!needle || [o.nomi, o.slug, o.egasi_ismi, o.telefon].some((v) => v?.toLowerCase().includes(needle))),
    )
  }, [stats.data, filter, q])

  if (stats.isLoading) return <PageSkeleton stats={4} panels={1} />
  if (stats.isError || !stats.data)
    return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(stats.error)} onRetry={() => void stats.refetch()} retrying={stats.isFetching} />

  const counts = stats.data.holatlar
  const tiles: { key: OrgStatus | 'all'; label: string; value: number }[] = [
    { key: 'all', label: 'Hammasi', value: stats.data.jami },
    { key: 'pending', label: 'Kutilmoqda', value: counts.pending ?? 0 },
    { key: 'active', label: 'Faol', value: counts.active ?? 0 },
    { key: 'suspended', label: "To'xtatilgan", value: counts.suspended ?? 0 },
    { key: 'rejected', label: 'Rad etilgan', value: counts.rejected ?? 0 },
  ]
  const txt = pending ? ACTION_TEXT[pending.action] : null

  return (
    <div>
      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
        {tiles.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setFilter(t.key)}
            aria-pressed={filter === t.key}
            className={clsx(
              'rounded-xl border p-3 text-left transition-colors',
              filter === t.key
                ? 'border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-900/30'
                : 'border-slate-200 bg-paper hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700',
            )}
          >
            <div className="text-xs font-medium text-slate-600 dark:text-slate-300">{t.label}</div>
            <div className={clsx('text-2xl font-bold tabular-nums', t.key === 'pending' && t.value > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-900 dark:text-slate-100')}>
              {t.value}
            </div>
          </button>
        ))}
      </div>

      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="sm:w-full sm:max-w-sm">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nomi, egasi yoki telefon bo'yicha qidirish" aria-label="Qidirish" />
        </div>
        <Button onClick={() => { setEditId(null); setOrgForm(emptyOrgForm()); setError(null) }}>+ Yangi tashkilot</Button>
      </div>
      {!orgForm && !deleteOrg && !pending && !planOrg && <ErrorBanner message={error} />}

      {!rows.length ? (
        <EmptyState title="Tashkilot topilmadi" description="Filtr yoki qidiruvni o'zgartirib ko'ring." />
      ) : (
        <Table className="min-w-[56rem]">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Tashkilot</th>
              <th className="px-4 py-3">Egasi</th>
              <th className="px-4 py-3">Holat</th>
              <th className="px-4 py-3 text-right">Kitob / O'quvchi / Berish</th>
              <th className="px-4 py-3">Bot</th>
              <th className="px-4 py-3">Sana</th>
              <th className="px-4 py-3 text-right">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {rows.map((o) => (
              <tr key={o.id}>
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900 dark:text-slate-100">{o.nomi}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{o.slug}</div>
                </td>
                <td className="px-4 py-3">
                  <div>{o.egasi_ismi || '—'}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{o.telefon}</div>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={STATUS[o.status]?.tone}>{STATUS[o.status]?.label ?? o.status}</Badge>
                  {o.status_reason && <div className="mt-1 max-w-[14rem] truncate text-xs text-slate-500 dark:text-slate-400" title={o.status_reason}>{o.status_reason}</div>}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {o.kitoblar} / {o.oquvchilar} / {o.berishlar}
                </td>
                <td className="px-4 py-3">{o.bot_ulangan ? <Badge tone="green">Ulangan</Badge> : <Badge>Yo'q</Badge>}</td>
                <td className="px-4 py-3 whitespace-nowrap text-slate-600 dark:text-slate-300">{formatDate(o.yaratilgan)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap justify-end gap-1.5">
                    {o.status === 'pending' && (
                      <>
                        <Button size="sm" onClick={() => setPending({ org: o, action: 'approve' })}>Tasdiqlash</Button>
                        <Button size="sm" variant="secondary" onClick={() => setPending({ org: o, action: 'reject' })}>Rad etish</Button>
                      </>
                    )}
                    {o.status === 'active' && (
                      <Button size="sm" variant="secondary" onClick={() => setPending({ org: o, action: 'suspend' })}>To'xtatish</Button>
                    )}
                    {(o.status === 'suspended' || o.status === 'rejected' || o.status === 'archived') && (
                      <Button size="sm" variant="secondary" onClick={() => setPending({ org: o, action: 'activate' })}>Faollashtirish</Button>
                    )}
                    <Button size="sm" variant="secondary" onClick={() => void openEdit(o)}>Tahrirlash</Button>
                    {o.status !== 'archived' && (
                      <Button size="sm" variant="secondary" onClick={() => setPending({ org: o, action: 'archive' })}>Arxivlash</Button>
                    )}
                    {o.status === 'archived' && (
                      <Button size="sm" variant="danger" onClick={() => { setDeleteOrg(o); setError(null) }}>O'chirish</Button>
                    )}
                    <Button size="sm" variant="secondary" onClick={() => { setPlanOrg(o); setPlan(''); setSubStatus('trial'); setError(null) }}>Obuna</Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <ConfirmDialog
        open={!!pending && !txt?.reason}
        title={txt?.title ?? ''}
        message={pending && <>«{pending.org.nomi}» tashkiloti uchun amal bajariladi.<ErrorBanner message={error} /></>}
        confirmLabel={txt?.confirm}
        variant={txt?.danger ? 'danger' : 'primary'}
        loading={statusMut.isPending}
        onConfirm={() => pending && statusMut.mutate(pending)}
        onCancel={() => { setPending(null); setError(null) }}
      />

      <Modal open={!!pending && !!txt?.reason} onClose={() => { setPending(null); setReason(''); setError(null) }} title={txt?.title ?? ''} description={pending?.org.nomi}>
        <ErrorBanner message={error} />
        <Field>
          <Label htmlFor="reason">Sabab (egasiga ko'rsatiladi)</Label>
          <Textarea id="reason" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={() => { setPending(null); setReason('') }}>Bekor qilish</Button>
          <Button variant="danger" loading={statusMut.isPending} onClick={() => pending && statusMut.mutate(pending)}>{txt?.confirm}</Button>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteOrg}
        title="Tashkilotni o'chirish"
        variant="danger"
        confirmLabel="O'chirish"
        loading={removeMut.isPending}
        message={deleteOrg && <>«{deleteOrg.nomi}» va uning barcha ma'lumotlari butunlay o'chiriladi. Bu amalni qaytarib bo'lmaydi.<ErrorBanner message={error} /></>}
        onConfirm={() => deleteOrg && removeMut.mutate(deleteOrg.id)}
        onCancel={() => { setDeleteOrg(null); setError(null) }}
      />

      <Modal
        open={!!orgForm}
        onClose={() => { setOrgForm(null); setEditId(null); setError(null) }}
        title={editId ? 'Tashkilotni tahrirlash' : 'Yangi tashkilot'}
        description={editId ? undefined : "Tashkilot darhol faol bo'ladi."}
      >
        {orgForm && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              setError(null)
              saveMut.mutate(orgForm)
            }}
          >
            <ErrorBanner message={error} />
            <Field>
              <Label htmlFor="o-nomi">Nomi</Label>
              <Input id="o-nomi" required value={orgForm.nomi} onChange={(e) => setOrgForm({ ...orgForm, nomi: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="o-slug">Slug (ixtiyoriy)</Label>
              <Input id="o-slug" value={orgForm.slug ?? ''} onChange={(e) => setOrgForm({ ...orgForm, slug: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="o-turi">Turi</Label>
              <Select id="o-turi" value={orgForm.turi} onChange={(e) => setOrgForm({ ...orgForm, turi: e.target.value })}>
                {ORG_TYPES.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </Field>
            <Field>
              <Label htmlFor="o-tel">Telefon</Label>
              <Input id="o-tel" value={orgForm.telefon} onChange={(e) => setOrgForm({ ...orgForm, telefon: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="o-email">Email</Label>
              <Input id="o-email" type="email" value={orgForm.email} onChange={(e) => setOrgForm({ ...orgForm, email: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="o-manzil">Manzil</Label>
              <Input id="o-manzil" value={orgForm.manzil} onChange={(e) => setOrgForm({ ...orgForm, manzil: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="o-tavsif">Tavsif</Label>
              <Textarea id="o-tavsif" rows={2} value={orgForm.tavsif} onChange={(e) => setOrgForm({ ...orgForm, tavsif: e.target.value })} />
            </Field>
            <div className="grid grid-cols-3 gap-2">
              <Field>
                <Label htmlFor="o-muddat">Muddat (kun)</Label>
                <Input id="o-muddat" type="number" min={1} max={365} value={orgForm.muddat_kun} onChange={(e) => setOrgForm({ ...orgForm, muddat_kun: Number(e.target.value) })} />
              </Field>
              <Field>
                <Label htmlFor="o-jarima">Jarima / kun</Label>
                <Input id="o-jarima" type="number" min={0} value={orgForm.kunlik_jarima} onChange={(e) => setOrgForm({ ...orgForm, kunlik_jarima: Number(e.target.value) })} />
              </Field>
              <Field>
                <Label htmlFor="o-limit">Kitob limiti</Label>
                <Input id="o-limit" type="number" min={1} max={100} value={orgForm.limit_kitob} onChange={(e) => setOrgForm({ ...orgForm, limit_kitob: Number(e.target.value) })} />
              </Field>
            </div>
            {!editId && orgForm.owner && (
              <fieldset className="mt-3 rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                <legend className="px-1 text-sm font-medium text-slate-700 dark:text-slate-300">Egasi (login — telefon)</legend>
                <Field>
                  <Label htmlFor="ow-tel">Telefon</Label>
                  <Input id="ow-tel" required value={orgForm.owner.telefon} onChange={(e) => setOrgForm({ ...orgForm, owner: { ...orgForm.owner!, telefon: e.target.value } })} />
                </Field>
                <Field>
                  <Label htmlFor="ow-name">To'liq ism</Label>
                  <Input id="ow-name" value={orgForm.owner.full_name} onChange={(e) => setOrgForm({ ...orgForm, owner: { ...orgForm.owner!, full_name: e.target.value } })} />
                </Field>
                <Field>
                  <Label htmlFor="ow-pass">Parol (kamida 8 belgi)</Label>
                  <Input id="ow-pass" type="password" autoComplete="new-password" value={orgForm.owner.password} onChange={(e) => setOrgForm({ ...orgForm, owner: { ...orgForm.owner!, password: e.target.value } })} />
                </Field>
              </fieldset>
            )}
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button type="button" variant="secondary" onClick={() => { setOrgForm(null); setEditId(null); setError(null) }}>Bekor qilish</Button>
              <Button type="submit" loading={saveMut.isPending}>Saqlash</Button>
            </div>
          </form>
        )}
      </Modal>

      <Modal open={!!planOrg} onClose={() => setPlanOrg(null)} title="Obunani o'zgartirish" description={planOrg?.nomi}>
        <ErrorBanner message={error} />
        <Field>
          <Label htmlFor="plan">Tarif</Label>
          <Select id="plan" value={plan} onChange={(e) => setPlan(e.target.value)}>
            <option value="">O'zgartirmaslik</option>
            {(plans.data ?? []).map((p) => (
              <option key={p.code} value={p.code}>{p.nomi}</option>
            ))}
          </Select>
        </Field>
        <Field>
          <Label htmlFor="sub-status">Obuna holati</Label>
          <Select id="sub-status" value={subStatus} onChange={(e) => setSubStatus(e.target.value)}>
            {SUB_STATUS.map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </Select>
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={() => setPlanOrg(null)}>Bekor qilish</Button>
          <Button loading={subMut.isPending} onClick={() => subMut.mutate()}>Saqlash</Button>
        </div>
      </Modal>
    </div>
  )
}

function AuditTab() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['platform', 'audit', page],
    queryFn: () => platformApi.audit(page),
  })
  if (isLoading) return <TableSkeleton rows={6} cols={5} />
  if (isError || !data) return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(error)} onRetry={() => void refetch()} retrying={isFetching} />
  if (!data.results.length) return <EmptyState title="Jurnal bo'sh" description="Platforma amallari shu yerda yoziladi." />
  return (
    <div>
      <Table>
        <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
          <tr>
            <th className="px-4 py-3">Vaqt</th>
            <th className="px-4 py-3">Amal</th>
            <th className="px-4 py-3">Tashkilot</th>
            <th className="px-4 py-3">Kim</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
          {data.results.map((a) => (
            <tr key={a.id}>
              <td className="px-4 py-2.5 whitespace-nowrap text-slate-600 dark:text-slate-300">{formatDateTime(a.yaratilgan)}</td>
              <td className="px-4 py-2.5 font-mono text-xs">{a.action}</td>
              <td className="px-4 py-2.5">{a.organization_nomi || '—'}</td>
              <td className="px-4 py-2.5">{a.actor_username || '—'}</td>
            </tr>
          ))}
        </tbody>
      </Table>
      <div className="mt-3 flex items-center justify-end gap-2">
        <Button size="sm" variant="secondary" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Oldingi</Button>
        <span className="text-sm text-slate-600 dark:text-slate-300">{page}</span>
        <Button size="sm" variant="secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Keyingi</Button>
      </div>
    </div>
  )
}

const HEALTH_TONE: Record<HealthState, 'green' | 'red' | 'amber'> = { ok: 'green', down: 'red', stale: 'amber', missing: 'red' }
const HEALTH_LABEL: Record<HealthState, string> = { ok: 'Ishlayapti', down: 'Ishlamayapti', stale: 'Kechikmoqda', missing: 'Signal yo‘q' }
const COMPONENT_LABEL: Record<string, string> = {
  celery: 'Fon vazifalari (celery + beat)',
  bot_check: 'Bot tekshiruvi',
}

function ago(seconds: number | null) {
  if (seconds == null) return 'hech qachon'
  if (seconds < 90) return `${seconds} soniya oldin`
  if (seconds < 5400) return `${Math.round(seconds / 60)} daqiqa oldin`
  return `${Math.round(seconds / 3600)} soat oldin`
}

function HealthTab() {
  const { data, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } = useQuery({
    queryKey: ['platform', 'health'],
    queryFn: healthApi.platform,
    refetchInterval: 30_000,
  })
  if (isLoading) return <StatsSkeleton count={4} />
  if (isError || !data) return <ErrorState title="Holatni olib bo‘lmadi" message={errorMessage(error)} onRetry={() => void refetch()} retrying={isFetching} />

  const items: { label: string; status: HealthState; hint: string }[] = [
    { label: 'Veb-server', status: data.web.status, hint: 'So‘rovlarga javob beryapti' },
    { label: 'Ma’lumotlar bazasi', status: data.database.status, hint: data.database.error || 'PostgreSQL' },
    { label: 'Kesh (Redis)', status: data.cache.status, hint: data.cache.error || 'Javob vaqti normal' },
    ...data.heartbeats.map((h) => ({
      label: COMPONENT_LABEL[h.name] ?? h.name,
      status: h.status,
      hint: h.status === 'missing' ? 'Hali signal kelmagan: worker/beat ishga tushirilmagan bo‘lishi mumkin' : `Oxirgi signal: ${ago(h.age_seconds)}`,
    })),
  ]
  const bad = items.filter((i) => i.status !== 'ok').length

  return (
    <div>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-300" aria-live="polite">
        {bad ? `${bad} ta komponentda muammo bor.` : 'Hamma komponent normal ishlayapti.'} Har 30 soniyada yangilanadi
        {dataUpdatedAt ? ` (${formatDateTime(new Date(dataUpdatedAt).toISOString())})` : ''}.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((i) => (
          <div key={i.label} className="rounded-xl border border-slate-200 bg-paper p-4 dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{i.label}</div>
              <Badge tone={HEALTH_TONE[i.status]}>{HEALTH_LABEL[i.status]}</Badge>
            </div>
            <div className="mt-1.5 text-xs text-slate-600 dark:text-slate-300">{i.hint}</div>
          </div>
        ))}
      </div>

      <h2 className="mb-2 mt-8 text-base font-semibold text-slate-900 dark:text-slate-100">Telegram botlar</h2>
      {!data.bots.length ? (
        <EmptyState title="Ulangan bot yo'q" description="Tashkilotlar bot ulagach shu yerda ko'rinadi." />
      ) : (
        <Table>
          <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Tashkilot</th>
              <th className="px-4 py-3">Bot</th>
              <th className="px-4 py-3">Holat</th>
              <th className="px-4 py-3">Oxirgi tekshiruv</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.bots.map((b) => {
              const good = b.state === 'ulangan' && b.webhook
              return (
                <tr key={b.organization + b.username}>
                  <td className="px-4 py-2.5">{b.organization}</td>
                  <td className="px-4 py-2.5 text-slate-600 dark:text-slate-300">{b.username ? `@${b.username}` : '—'}</td>
                  <td className="px-4 py-2.5">
                    <Badge tone={good ? 'green' : 'red'}>{good ? 'Ulangan' : b.state}</Badge>
                    {b.last_error && <div className="mt-1 text-xs text-red-600 dark:text-red-400">{b.last_error}</div>}
                  </td>
                  <td className="px-4 py-2.5 whitespace-nowrap">
                    {b.last_check ? formatDateTime(b.last_check) : 'hali tekshirilmagan'}
                    {b.stale && <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">eskirgan</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </Table>
      )}
    </div>
  )
}

export function Platform() {
  const [tab, setTab] = useState<'orgs' | 'health' | 'audit'>('orgs')
  return (
    <div>
      <PageHeader title="Platforma" subtitle="Barcha tashkilotlar, arizalar va obunalar" />
      <div className="mb-5 flex gap-1 border-b border-slate-200 dark:border-slate-700" role="tablist">
        {([['orgs', 'Tashkilotlar'], ['health', 'Tizim holati'], ['audit', 'Harakatlar jurnali']] as const).map(([k, l]) => (
          <button
            key={k}
            role="tab"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={clsx(
              '-mb-px border-b-2 px-4 py-2 text-sm font-medium',
              tab === k ? 'border-brand-600 text-brand-700 dark:text-brand-400' : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-300',
            )}
          >
            {l}
          </button>
        ))}
      </div>
      {tab === 'orgs' ? <OrgsTab /> : tab === 'health' ? <HealthTab /> : <AuditTab />}
    </div>
  )
}
