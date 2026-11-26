import { useState, type FormEvent } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Navigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi, telegramApi, type OrganizationInfo, type TelegramBotState } from '../api/resources'
import { Switch } from '../components/controls'
import { errorMessage } from '../api/client'
import { canManageCompany, useOrganization } from '../hooks/useOrganization'
import { useToast } from '../components/Toast'
import { Icons } from '../components/icons'
import {
  DASHBOARD_WIDGET_INFO,
  ORG_TYPE_LABELS,
  ORG_TYPE_OPTIONS,
  type DashboardWidget,
  type OrganizationType,
} from '../lib/organization'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  ErrorBanner,
  Field,
  Input,
  Label,
  PageHeader,
  PhoneInput,
  Textarea,
  ListSkeleton,
  PageSkeleton,
} from '../components/ui'

function NumberField({
  id,
  label,
  hint,
  value,
  onChange,
  min,
  max,
  suffix,
}: {
  id: string
  label: string
  hint: string
  value: string
  onChange: (v: string) => void
  min: number
  max: number
  suffix: string
}) {
  return (
    <Field>
      <Label htmlFor={id}>{label}</Label>
      <div className="flex items-center gap-2">
        <Input
          id={id}
          type="number"
          inputMode="numeric"
          min={min}
          max={max}
          required
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="max-w-40"
        />
        <span className="text-sm text-slate-500 dark:text-slate-400">{suffix}</span>
      </div>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</p>
    </Field>
  )
}

/** Library owner/admin edits their own organization: profile, logo, fines and loan rules. */
function SettingsForm({ org }: { org: OrganizationInfo }) {
  const qc = useQueryClient()
  const toast = useToast()
  const initial = {
    nomi: org.nomi ?? '',
    tavsif: org.tavsif ?? '',
    telefon: org.telefon ?? '',
    email: org.email ?? '',
    manzil: org.manzil ?? '',
    logo_url: org.logo_url ?? '',
    muddat_kun: String(org.muddat_kun ?? 14),
    kunlik_jarima: String(Math.round(Number(org.kunlik_jarima ?? 5000))),
    limit_kitob: String(org.limit_kitob ?? 3),
    taklif_soat: String(org.taklif_soat ?? 24),
    eslatma_kunlar_oldin: String(org.eslatma_kunlar_oldin ?? 2),
    kitob_xabarlari_yoqilgan: org.kitob_xabarlari_yoqilgan ?? true,
  }
  const [form, setForm] = useState(initial)
  const dirty = JSON.stringify(form) !== JSON.stringify(initial)
  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) => setForm((f) => ({ ...f, [key]: value }))

  const mut = useMutation({
    mutationFn: () =>
      authApi.updateOrganization(org.id, {
        nomi: form.nomi.trim(),
        tavsif: form.tavsif,
        telefon: form.telefon,
        email: form.email.trim(),
        manzil: form.manzil,
        logo_url: form.logo_url.trim(),
        muddat_kun: Number(form.muddat_kun),
        kunlik_jarima: form.kunlik_jarima,
        limit_kitob: Number(form.limit_kitob),
        taklif_soat: Number(form.taklif_soat),
        eslatma_kunlar_oldin: Number(form.eslatma_kunlar_oldin),
        kitob_xabarlari_yoqilgan: form.kitob_xabarlari_yoqilgan,
      }),
    onSuccess: (next) => {
      qc.setQueryData(['organization-info'], next)
      toast.success('Sozlamalar saqlandi')
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  // Logo is uploaded right away; the server checks and re-encodes the image.
  const logoMut = useMutation({
    mutationFn: (file: File | null) => (file ? authApi.uploadLogo(org.id, file) : authApi.deleteLogo(org.id)),
    onSuccess: (next, file) => {
      qc.setQueryData(['organization-info'], next)
      setForm((f) => ({ ...f, logo_url: next.logo_url ?? '' }))
      toast.success(file ? 'Logo yangilandi' : 'Logo o‘chirildi')
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    mut.mutate()
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <Card className="p-5">
        <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Kutubxona ma‘lumotlari</h2>
        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
          Turi: {ORG_TYPE_LABELS[org.type] ?? org.type}. Bu ma‘lumotlarni faqat siz o‘zgartira olasiz.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field className="sm:col-span-2">
            <Label htmlFor="c-nomi">Nomi</Label>
            <Input id="c-nomi" required maxLength={160} value={form.nomi} onChange={(e) => set('nomi', e.target.value)} />
          </Field>
          <Field className="sm:col-span-2">
            <Label htmlFor="c-tavsif">Tavsif</Label>
            <Textarea id="c-tavsif" rows={3} value={form.tavsif} onChange={(e) => set('tavsif', e.target.value)} />
          </Field>
          <Field>
            <Label htmlFor="c-telefon">Telefon</Label>
            <PhoneInput id="c-telefon" value={form.telefon} onValueChange={(v) => set('telefon', v)} />
          </Field>
          <Field>
            <Label htmlFor="c-email">Email</Label>
            <Input id="c-email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </Field>
          <Field className="sm:col-span-2">
            <Label htmlFor="c-manzil">Manzil</Label>
            <Input id="c-manzil" maxLength={255} value={form.manzil} onChange={(e) => set('manzil', e.target.value)} />
          </Field>
          <Field className="sm:col-span-2">
            <Label htmlFor="c-logo-file">Logo</Label>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-canvas dark:border-slate-600">
                {form.logo_url ? (
                  <img src={form.logo_url} alt="Logo ko‘rinishi" className="h-full w-full object-contain" />
                ) : (
                  <Icons.books className="h-6 w-6 text-slate-400" aria-hidden="true" />
                )}
              </div>
              <label
                htmlFor="c-logo-file"
                className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-paper px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-within:ring-2 focus-within:ring-brand-500 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                {logoMut.isPending ? 'Yuklanmoqda…' : form.logo_url ? 'Boshqa rasm tanlash' : 'Rasm yuklash'}
                <input
                  id="c-logo-file"
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  className="sr-only"
                  disabled={logoMut.isPending}
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    e.target.value = ''
                    if (!file) return
                    if (file.size > 2 * 1024 * 1024) {
                      toast.error('Logo hajmi 2 MB dan oshmasligi kerak.')
                      return
                    }
                    logoMut.mutate(file)
                  }}
                />
              </label>
              {form.logo_url && (
                <Button type="button" variant="secondary" disabled={logoMut.isPending} onClick={() => logoMut.mutate(null)}>
                  O‘chirish
                </Button>
              )}
            </div>
            <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
              PNG, JPG yoki WEBP, 2 MB gacha. Kvadrat rasm yaxshi ko‘rinadi. Yon panelda va ilovada chiqadi.
            </p>
          </Field>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Berish va jarima qoidalari</h2>
        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">Yangi berishlar va hisoblanadigan jarimalarga qo‘llanadi.</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <NumberField id="c-muddat" label="Qaytarish muddati" suffix="kun" min={1} max={365} value={form.muddat_kun} onChange={(v) => set('muddat_kun', v)} hint="Kitob berilganda standart muddat." />
          <NumberField id="c-jarima" label="Kunlik jarima" suffix="so‘m" min={0} max={1000000} value={form.kunlik_jarima} onChange={(v) => set('kunlik_jarima', v)} hint="Muddati o‘tgan har bir kun uchun." />
          <NumberField id="c-limit" label="Bir vaqtda kitoblar soni" suffix="ta" min={1} max={100} value={form.limit_kitob} onChange={(v) => set('limit_kitob', v)} hint="O‘quvchi qo‘lida bo‘la oladigan kitoblar." />
          <NumberField id="c-taklif" label="Navbat taklifi muddati" suffix="soat" min={1} max={720} value={form.taklif_soat} onChange={(v) => set('taklif_soat', v)} hint="Navbatdagi o‘quvchi kitobni olishi uchun vaqt." />
          <NumberField id="c-eslatma" label="Eslatma" suffix="kun oldin" min={0} max={30} value={form.eslatma_kunlar_oldin} onChange={(v) => set('eslatma_kunlar_oldin', v)} hint="Muddatdan necha kun oldin Telegram eslatmasi yuboriladi." />
          <Field>
            <Label htmlFor="c-xabar">Kitob xabarlari</Label>
            <Switch
              id="c-xabar"
              checked={form.kitob_xabarlari_yoqilgan}
              onChange={(v) => set('kitob_xabarlari_yoqilgan', v)}
              label={form.kitob_xabarlari_yoqilgan ? 'Yoqilgan' : 'O‘chirilgan'}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Berish va qaytarish haqida o‘quvchiga Telegram xabari.</p>
          </Field>
        </div>
      </Card>

      <div className="flex items-center justify-end gap-2">
        {dirty && (
          <Button type="button" variant="secondary" onClick={() => setForm(initial)}>
            Bekor qilish
          </Button>
        )}
        <Button type="submit" loading={mut.isPending} disabled={!dirty}>
          Saqlash
        </Button>
      </div>
    </form>
  )
}

/** Owner picks library or school: it decides what the bot and reader forms ask for. */
function OrganizationTypeSection({ org }: { org: OrganizationInfo }) {
  const qc = useQueryClient()
  const toast = useToast()
  const isOwner = org.rol === 'egasi'
  const [pending, setPending] = useState<OrganizationType | null>(null)
  const mut = useMutation({
    mutationFn: (type: OrganizationType) => authApi.updateOrganization(org.id, { type }),
    onSuccess: (next) => {
      qc.setQueryData(['organization-info'], next)
      qc.invalidateQueries({ queryKey: ['stats', 'dashboard'] })
      toast.success(`Tashkilot turi: ${ORG_TYPE_LABELS[next.type]}`)
      setPending(null)
    },
    onError: (e) => {
      toast.error(errorMessage(e))
      setPending(null)
    },
  })
  return (
    <Card className="p-5">
      <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Tashkilot turi</h2>
      <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
        Telegram bot va kitobxon qo‘shish formasi shu turga qarab ma‘lumot so‘raydi.
        {!isOwner && ' Turni faqat tashkilot egasi o‘zgartira oladi.'}
      </p>
      <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Tashkilot turi">
        {ORG_TYPE_OPTIONS.map((option) => {
          const active = org.type === option.value
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={active}
              disabled={!isOwner || mut.isPending}
              onClick={() => !active && setPending(option.value)}
              className={
                'rounded-lg border p-4 text-left transition disabled:cursor-not-allowed ' +
                (active
                  ? 'border-brand-500 bg-brand-50 ring-1 ring-brand-500 dark:bg-brand-900/20'
                  : 'border-slate-200 hover:border-slate-300 disabled:opacity-60 dark:border-slate-600')
              }
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-slate-900 dark:text-slate-100">{option.label}</span>
                {active && <Badge tone="green">Joriy</Badge>}
              </div>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{option.hint}</p>
            </button>
          )
        })}
      </div>
      <ConfirmDialog
        open={pending !== null}
        title="Tashkilot turini o‘zgartirasizmi?"
        message={
          pending
            ? `Tur «${ORG_TYPE_LABELS[pending]}» bo‘ladi. Yangi arizalar va kitobxon formasi shunga moslashadi; mavjud kitobxonlar o‘zgarmaydi.`
            : ''
        }
        confirmLabel="O‘zgartirish"
        variant="primary"
        loading={mut.isPending}
        onConfirm={() => pending && mut.mutate(pending)}
        onCancel={() => setPending(null)}
      />
    </Card>
  )
}

/** Owner/admin chooses which dashboard widgets the whole organization sees, and their order. */
function DashboardWidgetsSection({ org }: { org: OrganizationInfo }) {
  const qc = useQueryClient()
  const toast = useToast()
  const available = (org.available_dashboard_widgets ?? []).filter((key) => key in DASHBOARD_WIDGET_INFO)
  const initial = (org.dashboard_widgets ?? available).filter((key) => available.includes(key))
  const [enabled, setEnabled] = useState<DashboardWidget[]>(initial)
  // Enabled widgets first in their saved order, then the switched-off ones in catalogue order.
  const rows = [...enabled, ...available.filter((key) => !enabled.includes(key))]
  const dirty = JSON.stringify(enabled) !== JSON.stringify(initial)

  const toggle = (key: DashboardWidget, on: boolean) =>
    setEnabled((list) => (on ? [...list, key] : list.filter((k) => k !== key)))
  const move = (index: number, delta: number) =>
    setEnabled((list) => {
      const next = [...list]
      const [item] = next.splice(index, 1)
      next.splice(index + delta, 0, item)
      return next
    })

  const mut = useMutation({
    mutationFn: () => authApi.updateOrganization(org.id, { dashboard_widgets: enabled }),
    onSuccess: (next) => {
      qc.setQueryData(['organization-info'], next)
      qc.invalidateQueries({ queryKey: ['stats', 'dashboard'] })
      toast.success('Dashboard sozlamalari saqlandi')
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  return (
    <Card className="p-5">
      <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Dashboard widgetlari</h2>
      <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
        Bosh sahifada qaysi statistikalar chiqishini tanlang va tartibini belgilang. Sozlama tashkilotdagi barcha xodimlarga qo‘llanadi.
      </p>
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 dark:divide-slate-700 dark:border-slate-600">
        {rows.map((key) => {
          const info = DASHBOARD_WIDGET_INFO[key]
          const index = enabled.indexOf(key)
          const on = index !== -1
          return (
            <li key={key} className="flex items-center gap-3 px-3 py-2.5">
              <div className="flex flex-col">
                <button
                  type="button"
                  aria-label={`${info.label}: yuqoriga`}
                  disabled={!on || index === 0}
                  onClick={() => move(index, -1)}
                  className="rounded p-0.5 text-slate-400 hover:text-slate-700 disabled:invisible dark:hover:text-slate-200"
                >
                  <ChevronUp className="h-4 w-4" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  aria-label={`${info.label}: pastga`}
                  disabled={!on || index === enabled.length - 1}
                  onClick={() => move(index, 1)}
                  className="rounded p-0.5 text-slate-400 hover:text-slate-700 disabled:invisible dark:hover:text-slate-200"
                >
                  <ChevronDown className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
              <div className="min-w-0 flex-1">
                <div className={'text-sm font-medium ' + (on ? 'text-slate-900 dark:text-slate-100' : 'text-slate-400')}>
                  {info.label}
                  {info.kind === 'panel' && <span className="ml-2 text-xs font-normal text-slate-400">ro‘yxat</span>}
                </div>
                <div className="truncate text-xs text-slate-500 dark:text-slate-400">{info.hint}</div>
              </div>
              <Switch checked={on} onChange={(v) => toggle(key, v)} label={on ? 'Ko‘rinadi' : 'Yashirin'} />
            </li>
          )
        })}
      </ul>
      <div className="mt-4 flex items-center justify-end gap-2">
        {dirty && (
          <Button type="button" variant="secondary" onClick={() => setEnabled(initial)}>
            Bekor qilish
          </Button>
        )}
        <Button type="button" variant="secondary" onClick={() => setEnabled(available)} disabled={mut.isPending}>
          Hammasini ko‘rsatish
        </Button>
        <Button type="button" loading={mut.isPending} disabled={!dirty} onClick={() => mut.mutate()}>
          Saqlash
        </Button>
      </div>
    </Card>
  )
}

function BotSection() {
  const qc = useQueryClient()
  const toast = useToast()
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [confirmDisconnect, setConfirmDisconnect] = useState(false)

  const { data, isLoading, isError, error: loadError } = useQuery({
    queryKey: ['telegram-bot'],
    queryFn: telegramApi.get,
    retry: false,
  })

  const onDone = (state: TelegramBotState, message: string) => {
    qc.setQueryData(['telegram-bot'], state)
    setToken('')
    setError(null)
    toast.success(message)
  }

  const connectMut = useMutation({
    mutationFn: (value: string) => telegramApi.connect(value),
    onSuccess: (state) => onDone(state, 'Bot ulandi'),
    onError: (err) => setError(errorMessage(err)),
  })
  const actionMut = useMutation({
    mutationFn: (action: 'test' | 'webhook') => telegramApi.action(action),
    onSuccess: (state, action) =>
      onDone(state, action === 'test' ? 'Bot tekshirildi' : 'Webhook qayta o‘rnatildi'),
    onError: (err) => setError(errorMessage(err)),
  })
  const disconnectMut = useMutation({
    mutationFn: telegramApi.disconnect,
    onSuccess: (state) => {
      setConfirmDisconnect(false)
      onDone(state, 'Bot uzildi')
    },
    onError: (err) => {
      setConfirmDisconnect(false)
      setError(errorMessage(err))
    },
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const value = token.trim()
    if (!value) {
      setError('Bot tokenini kiriting.')
      return
    }
    connectMut.mutate(value)
  }

  const bot = data?.bot
  const connected = !!data?.ulangan

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
          <span aria-hidden>{Icons.bot({ className: 'h-5 w-5' })}</span>
          Telegram bot
        </h2>
        {!isLoading && !isError && (
          <Badge tone={connected ? 'green' : 'slate'}>{connected ? 'Ulangan' : 'Ulanmagan'}</Badge>
        )}
      </div>

      {isLoading && <ListSkeleton rows={3} />}
      {isError && <ErrorBanner message={errorMessage(loadError)} />}

      {!isLoading && !isError && (
        <>
          {bot && (
            <dl className="mb-5 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500 dark:text-slate-400">Bot</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">@{bot.username}</dd>
              </div>
              <div>
                <dt className="text-slate-500 dark:text-slate-400">Webhook</dt>
                <dd>
                  <Badge tone={bot.webhook_ornatilgan ? 'green' : 'amber'}>
                    {bot.webhook_ornatilgan ? 'O‘rnatilgan' : 'O‘rnatilmagan'}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-slate-500 dark:text-slate-400">Oxirgi tekshiruv</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">
                  {bot.oxirgi_tekshiruv ? new Date(bot.oxirgi_tekshiruv).toLocaleString('uz-UZ') : '—'}
                </dd>
              </div>
              {bot.oxirgi_xato && (
                <div className="sm:col-span-2">
                  <dt className="text-slate-500 dark:text-slate-400">Oxirgi xato</dt>
                  <dd className="break-words text-red-600 dark:text-red-400">{bot.oxirgi_xato}</dd>
                </div>
              )}
            </dl>
          )}

          <ErrorBanner message={error} />

          <form onSubmit={onSubmit}>
            <Field>
              <Label htmlFor="bot-token">{connected ? 'Yangi bot tokeni' : 'Bot tokeni'}</Label>
              <Input
                id="bot-token"
                type="password"
                autoComplete="off"
                placeholder="123456789:AA..."
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Tokenni Telegramdagi @BotFather dan oling. U shifrlab saqlanadi va qayta ko‘rsatilmaydi.
                Har bir kutubxonaga alohida bot kerak.
              </p>
            </Field>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" loading={connectMut.isPending}>
                {connected ? 'Tokenni almashtirish' : 'Botni ulash'}
              </Button>
              {connected && (
                <>
                  <Button
                    type="button"
                    variant="secondary"
                    loading={actionMut.isPending && actionMut.variables === 'test'}
                    onClick={() => actionMut.mutate('test')}
                  >
                    Tekshirish
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    loading={actionMut.isPending && actionMut.variables === 'webhook'}
                    onClick={() => actionMut.mutate('webhook')}
                  >
                    Webhookni qayta o‘rnatish
                  </Button>
                  <Button type="button" variant="danger" onClick={() => setConfirmDisconnect(true)}>
                    Botni uzish
                  </Button>
                </>
              )}
            </div>
          </form>
        </>
      )}

      <ConfirmDialog
        open={confirmDisconnect}
        title="Botni uzish"
        confirmLabel="Uzish"
        loading={disconnectMut.isPending}
        message="Bot uzilsa, o‘quvchilar Telegram orqali xabar olmaydi va ariza yubora olmaydi. Davom etasizmi?"
        onConfirm={() => disconnectMut.mutate()}
        onCancel={() => setConfirmDisconnect(false)}
      />
    </Card>
  )
}

function InlineSearchSection({ org }: { org: OrganizationInfo }) {
  const qc = useQueryClient()
  const toast = useToast()
  const enabled = org.capabilities?.search_inline === true
  const mut = useMutation({
    mutationFn: (value: boolean) => authApi.updateOrganization(org.id, { capabilities: { search_inline: value } }),
    onSuccess: (next) => {
      qc.setQueryData(['organization-info'], next)
      toast.success(next.capabilities?.search_inline ? 'Inline qidiruv yoqildi' : 'Inline qidiruv o‘chirildi')
    },
    onError: (e) => toast.error(errorMessage(e)),
  })
  return (
    <Card className="p-5">
      <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-slate-100">Inline qidiruv</h2>
      <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
        A‘zolar istalgan chatda <b>@bot_nomi kitob nomi</b> deb yozib, kutubxona kitoblarini qidira oladi va natijani yuborishi mumkin.
      </p>
      <Switch checked={enabled} disabled={mut.isPending} onChange={(v) => mut.mutate(v)} label={enabled ? 'Yoqilgan' : 'O‘chirilgan'} />
      {enabled && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          Telegram'da ishlashi uchun @BotFather'da botingiz uchun <b>/setinline</b> buyrug‘i bilan inline rejimni yoqing.
        </p>
      )}
    </Card>
  )
}

export function Company() {
  const { data: org, isLoading } = useOrganization()

  if (isLoading) return <PageSkeleton stats={0} />
  if (!canManageCompany(org)) return <Navigate to="/" replace />

  return (
    <div className="max-w-3xl space-y-4">
      <PageHeader title="Kutubxona profili" subtitle="Kutubxona ma‘lumotlari va Telegram bot sozlamalari" />

      {org && <SettingsForm key={org.id} org={org} />}
      {org && <OrganizationTypeSection org={org} />}
      {org && <DashboardWidgetsSection key={`${org.type}-${(org.dashboard_widgets ?? []).join(',')}`} org={org} />}

      <BotSection />
      {org && <InlineSearchSection org={org} />}
    </div>
  )
}
