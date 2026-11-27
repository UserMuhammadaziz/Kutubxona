import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  authApi,
  messagesApi,
  readersApi,
  xatolikApi,
  type OchirishNatijasi,
  type ParolAlmashtirishPayload,
  type ProfilYangilashPayload,
  type XabarYuborishPayload,
} from '../api/resources'
import { errorMessage } from '../api/client'
import { useToast } from '../components/Toast'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import {
  avtomatikHolatniSaqla,
  avtomatikYoqilgan,
} from '../lib/xatolikXabari'
import { useAuthStore } from '../store/auth'
import { useOrganization } from '../hooks/useOrganization'
import { isSchool } from '../lib/organization'
import { Icons } from '../components/icons'
import { ProfilePreferences } from '../components/ProfilePreferences'
import { TelegramLinkCard } from '../components/TelegramLinkCard'
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
  Select,
  Spinner,
  Textarea,
} from '../components/ui'
import type { OquvchiRol, XatolikXabari } from '../types'

const ROL_LABELS: Record<string, string> = {
  egasi: 'Egasi',
  administrator: 'Administrator',
  kutubxonachi: 'Kutubxonachi',
}

const BOSH_PAROL: ParolAlmashtirishPayload = {
  joriy_parol: '',
  yangi_parol: '',
  yangi_parol_takror: '',
}

function rolLabel(rol?: string | null): string {
  return (rol && ROL_LABELS[rol]) || rol || '—'
}

function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 border-b border-slate-100 py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
      <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>
      <span className="min-w-0 break-words text-sm font-medium text-slate-900 dark:text-slate-100">
        {children}
      </span>
    </div>
  )
}

/** Kutubxonachi o'z hisobini boshqaradi: parol, xabar va kitobxonlarni o'chirish. */
export function Profile() {
  const { user } = useAuthStore()
  const organizationId = useAuthStore((s) => s.organizationId)
  const openTenantPicker = useAuthStore((s) => s.openTenantPicker)
  const toast = useToast()
  const queryClient = useQueryClient()

  const [parol, setParol] = useState<ParolAlmashtirishPayload>(BOSH_PAROL)
  const [parolXato, setParolXato] = useState<string | null>(null)

  // Shaxsiy ma'lumotlarni tahrirlash
  const [shaxsiy, setShaxsiy] = useState<ProfilYangilashPayload>({})
  const [tahrir, setTahrir] = useState(false)
  const [shaxsiyXato, setShaxsiyXato] = useState<string | null>(null)

  useEffect(() => {
    if (!user || tahrir) return
    setShaxsiy({
      username: user.username,
      full_name: user.full_name || '',
      telefon: user.telefon || '',
    })
  }, [user, tahrir])

  // Kitobxonlarni o'chirish
  const [ochirishRol, setOchirishRol] = useState<OquvchiRol>('oquvchi')
  const [ochirishQidiruv, setOchirishQidiruv] = useState('')
  const kechikkanOchirishQidiruv = useDebouncedValue(ochirishQidiruv)
  const [tanlanganIds, setTanlanganIds] = useState<number[]>([])
  const [ochirishTasdiq, setOchirishTasdiq] = useState(false)
  const [ochirishNatija, setOchirishNatija] = useState<OchirishNatijasi | null>(null)

  const { data: org } = useOrganization()
  const [xabar, setXabar] = useState<XabarYuborishPayload>({
    tur: 'shaxs',
    rol: 'oquvchi',
    matn: '',
  })
  const [kitobxonQidiruv, setKitobxonQidiruv] = useState('')
  const kechikkanQidiruv = useDebouncedValue(kitobxonQidiruv)

  // Xatolik haqida xabar berish
  const [xatoMatn, setXatoMatn] = useState('')
  const [xatoSahifa, setXatoSahifa] = useState('')
  const [autoXato, setAutoXato] = useState(avtomatikYoqilgan())

  const { data: sinflar, isLoading: sinflarYuklanmoqda } = useQuery({
    queryKey: ['message-classes', xabar.rol],
    queryFn: () => messagesApi.classes(xabar.rol),
    enabled: xabar.tur === 'sinf',
  })

  const { data: kitobxonlar, isLoading: kitobxonlarYuklanmoqda } = useQuery({
    queryKey: ['message-readers', xabar.rol, kechikkanQidiruv],
    queryFn: () => readersApi.list({ rol: xabar.rol, search: kechikkanQidiruv || undefined }),
    enabled: xabar.tur === 'shaxs',
  })

  const { data: ochirishReaderlar, isLoading: ochirishYuklanmoqda } = useQuery({
    queryKey: ['delete-readers', ochirishRol, kechikkanOchirishQidiruv],
    queryFn: () => readersApi.list({ rol: ochirishRol, search: kechikkanOchirishQidiruv || undefined }),
  })

  const shaxsiyMut = useMutation({
    mutationFn: (payload: ProfilYangilashPayload) => authApi.updateProfile(payload),
    onSuccess: (natija) => {
      useAuthStore.setState({ user: natija })
      setShaxsiy({
        username: natija.username,
        full_name: natija.full_name || '',
        telefon: natija.telefon || '',
      })
      setTahrir(false)
      setShaxsiyXato(null)
      toast.success('Shaxsiy ma\'lumotlar saqlandi.')
    },
    onError: (err) => setShaxsiyXato(errorMessage(err)),
  })

  const parolMut = useMutation({
    mutationFn: (payload: ParolAlmashtirishPayload) => authApi.changePassword(payload),
    onSuccess: () => {
      setParol(BOSH_PAROL)
      setParolXato(null)
      toast.success('Parol muvaffaqiyatli o‘zgartirildi.')
    },
    onError: (err) => setParolXato(errorMessage(err)),
  })

  const xabarMut = useMutation({
    mutationFn: (payload: XabarYuborishPayload) => messagesApi.send(payload),
    onSuccess: (natija) => {
      const izoh = [
        `${natija.yuborildi} ta yuborildi`,
        natija.telegramsiz ? `${natija.telegramsiz} tasida Telegram yo‘q` : null,
        natija.xatolik ? `${natija.xatolik} tasida xatolik` : null,
      ]
        .filter(Boolean)
        .join(', ')
      toast.success(`Jami ${natija.jami} ta: ${izoh}.`)
      setXabar((old) => ({ ...old, matn: '' }))
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const { data: xatoliklar, isLoading: xatoliklarYuklanmoqda } = useQuery({
    queryKey: ['xatolik-xabarlari'],
    queryFn: () => xatolikApi.list(),
  })

  const xatoMut = useMutation({
    mutationFn: () =>
      xatolikApi.send({
        matn: xatoMatn.trim(),
        sahifa: xatoSahifa.trim() || window.location.pathname,
        tur: 'qolda',
      }),
    onSuccess: (natija) => {
      setXatoMatn('')
      void queryClient.invalidateQueries({ queryKey: ['xatolik-xabarlari'] })
      toast.success(
        natija.telegramga_yuborildi
          ? `Xabar saqlandi va ${natija.telegramga_yuborildi} ta administratorga yuborildi.`
          : 'Xabar saqlandi. Administratorlarning Telegram ID si topilmadi.',
      )
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const ochirishMut = useMutation({
    mutationFn: (ids: number[]) => readersApi.deleteSelected(ids),
    onSuccess: (natija) => {
      setOchirishNatija(natija)
      setTanlanganIds([])
      setOchirishTasdiq(false)
      void queryClient.invalidateQueries()
      if (natija.ochirildi) toast.success(`${natija.ochirildi} ta kitobxon o'chirildi.`)
      if (natija.ochirilmadi.length) {
        toast.error(`${natija.ochirilmadi.length} ta o'chirilmadi — sababini pastda ko'ring.`)
      }
    },
    onError: (err) => {
      setOchirishTasdiq(false)
      toast.error(errorMessage(err))
    },
  })

  if (!user) return null

  const boshHarflar = (user.full_name || user.username || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((soz) => soz[0]?.toUpperCase() ?? '')
    .join('')

  // Libraries have no classes or teachers: every reader is messaged as one group.
  const library = !!org && !isSchool(org)
  const rolNomi = library ? 'kitobxon' : xabar.rol === 'oquvchi' ? 'o‘quvchi' : 'o‘qituvchi'
  const joriyKutubxonaNomi =
    user.kutubxonalar?.find((k) => k.id === organizationId)?.nomi ?? 'Tanlanmagan'

  function parolYuborish(e: FormEvent) {
    e.preventDefault()
    setParolXato(null)
    parolMut.mutate(parol)
  }

  function shaxsiyYuborish(e: FormEvent) {
    e.preventDefault()
    setShaxsiyXato(null)
    shaxsiyMut.mutate({
      username: shaxsiy.username?.trim(),
      full_name: shaxsiy.full_name?.trim(),
      telefon: shaxsiy.telefon?.trim(),
    })
  }

  function xabarYuborish(e: FormEvent) {
    e.preventDefault()
    if (!xabar.matn.trim()) return
    xabarMut.mutate({
      tur: xabar.tur,
      rol: xabar.rol,
      matn: xabar.matn.trim(),
      ...(xabar.tur === 'shaxs' ? { oquvchi: xabar.oquvchi } : {}),
      ...(xabar.tur === 'sinf' ? { sinf: xabar.sinf } : {}),
    })
  }

  function tanlovniAlmashtir(id: number) {
    setTanlanganIds((old) =>
      old.includes(id) ? old.filter((x) => x !== id) : [...old, id],
    )
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Profil" subtitle="Kutubxonachi hisobi haqidagi ma'lumotlar" />

      <Card className="mb-5 overflow-hidden">
        <div className="flex flex-col items-start gap-4 bg-gradient-to-r from-brand-50 to-transparent p-6 sm:flex-row sm:items-center dark:from-brand-900/20">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xl font-semibold text-white">
            {boshHarflar || '?'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-xl font-semibold text-slate-900 dark:text-slate-100">
              {user.full_name || user.username}
            </div>
            <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">@{user.username}</div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={user.rol === 'administrator' ? 'blue' : 'green'}>
              {rolLabel(user.rol)}
            </Badge>
            <Badge tone={user.is_active ? 'green' : 'red'}>
              {user.is_active ? 'Faol' : 'Bloklangan'}
            </Badge>
          </div>
        </div>
      </Card>

      {(user.kutubxonalar?.length ?? 0) > 1 && (
        <Card className="mb-5 flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <Icons.books className="h-5 w-5 text-brand-600 dark:text-brand-400" />
              Kutubxona
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Hozirgi kutubxona: <b>{joriyKutubxonaNomi}</b>. Bir nechta kutubxonada ishlaysiz.
            </p>
          </div>
          <Button variant="secondary" onClick={openTenantPicker}>
            Kutubxona almashtirish
          </Button>
        </Card>
      )}

      <TelegramLinkCard />

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="flex flex-col gap-5">
          <Card className="p-5">
            <div className="mb-2 flex items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
                <Icons.idCard className="h-5 w-5 text-brand-600 dark:text-brand-400" />
                Shaxsiy ma'lumotlar
              </h2>
              {!tahrir && (
                <button
                  type="button"
                  onClick={() => {
                    setShaxsiy({
                      username: user.username,
                      full_name: user.full_name || '',
                      telefon: user.telefon || '',
                    })
                    setShaxsiyXato(null)
                    setTahrir(true)
                  }}
                  className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-50 dark:text-brand-300 dark:hover:bg-brand-900/30"
                >
                  Tahrirlash
                </button>
              )}
            </div>

            {tahrir ? (
              <form onSubmit={shaxsiyYuborish}>
                <ErrorBanner message={shaxsiyXato} />
                <Field>
                  <Label htmlFor="prof-fish">To'liq ism</Label>
                  <Input
                    id="prof-fish"
                    value={shaxsiy.full_name ?? ''}
                    onChange={(e) => setShaxsiy({ ...shaxsiy, full_name: e.target.value })}
                    maxLength={120}
                    required
                  />
                </Field>
                <Field>
                  <Label htmlFor="prof-login">Foydalanuvchi nomi (login)</Label>
                  <Input
                    id="prof-login"
                    value={shaxsiy.username ?? ''}
                    onChange={(e) => setShaxsiy({ ...shaxsiy, username: e.target.value })}
                    maxLength={150}
                    autoComplete="username"
                    required
                  />
                </Field>
                <Field>
                  <Label htmlFor="prof-telefon">Telefon raqam</Label>
                  <Input
                    id="prof-telefon"
                    value={shaxsiy.telefon ?? ''}
                    onChange={(e) => setShaxsiy({ ...shaxsiy, telefon: e.target.value })}
                    maxLength={20}
                    placeholder="+998901234567"
                    autoComplete="tel"
                  />
                </Field>
                <div className="flex gap-2">
                  <Button type="submit" loading={shaxsiyMut.isPending} className="flex-1">
                    Saqlash
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={shaxsiyMut.isPending}
                    onClick={() => {
                      setTahrir(false)
                      setShaxsiyXato(null)
                    }}
                  >
                    Bekor qilish
                  </Button>
                </div>
              </form>
            ) : (
              <>
                <InfoRow label="To'liq ism">{user.full_name || '—'}</InfoRow>
                <InfoRow label="Foydalanuvchi nomi">@{user.username}</InfoRow>
                <InfoRow label="Telefon raqam">{user.telefon || '—'}</InfoRow>
                <InfoRow label="Tizimdagi roli">{rolLabel(user.rol)}</InfoRow>
                <InfoRow label="Joriy kutubxonadagi roli">{rolLabel(user.joriy_rol)}</InfoRow>
              </>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <Icons.lock className="h-5 w-5 text-brand-600 dark:text-brand-400" />
              Parolni almashtirish
            </h2>
            <form onSubmit={parolYuborish}>
              <ErrorBanner message={parolXato} />
              <Field>
                <Label htmlFor="joriy-parol">Joriy parol</Label>
                <Input
                  id="joriy-parol"
                  type="password"
                  autoComplete="current-password"
                  value={parol.joriy_parol}
                  onChange={(e) => setParol({ ...parol, joriy_parol: e.target.value })}
                  required
                />
              </Field>
              <Field>
                <Label htmlFor="yangi-parol">Yangi parol</Label>
                <Input
                  id="yangi-parol"
                  type="password"
                  autoComplete="new-password"
                  value={parol.yangi_parol}
                  onChange={(e) => setParol({ ...parol, yangi_parol: e.target.value })}
                  required
                />
              </Field>
              <Field>
                <Label htmlFor="yangi-parol-takror">Yangi parolni takrorlang</Label>
                <Input
                  id="yangi-parol-takror"
                  type="password"
                  autoComplete="new-password"
                  value={parol.yangi_parol_takror}
                  onChange={(e) => setParol({ ...parol, yangi_parol_takror: e.target.value })}
                  required
                />
              </Field>
              <Button type="submit" loading={parolMut.isPending} className="w-full">
                Parolni saqlash
              </Button>
            </form>
          </Card>
        </div>

        <div className="flex flex-col gap-5">
          <Card className="p-5">
            <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <Icons.trash className="h-5 w-5 text-red-600 dark:text-red-400" />
              Kitobxonlarni o'chirish
            </h2>
            <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
              Tanlangan o'quvchilar yoki o'qituvchilar ro'yxatdan o'chiriladi. Faqat qaytarilmagan kitobi yoki kutilayotgan band so'rovi borlar o'chirilmaydi. O'chirilgan kitobxonga Telegram orqali qaytadan a'riza topshirish taklifi yuboriladi.
            </p>

            <div className="grid gap-3 sm:grid-cols-2">
              <Field>
                <Label htmlFor="ochirish-rol">Kimlar</Label>
                <Select
                  id="ochirish-rol"
                  value={ochirishRol}
                  onChange={(e) => {
                    setOchirishRol(e.target.value as OquvchiRol)
                    setTanlanganIds([])
                    setOchirishNatija(null)
                  }}
                >
                  <option value="oquvchi">O'quvchilar</option>
                  <option value="oqituvchi">O'qituvchilar</option>
                </Select>
              </Field>
              <Field>
                <Label htmlFor="ochirish-qidiruv">Qidiruv</Label>
                <Input
                  id="ochirish-qidiruv"
                  placeholder={library ? 'Ism yoki telefon...' : 'Ism, sinf yoki telefon...'}
                  value={ochirishQidiruv}
                  onChange={(e) => setOchirishQidiruv(e.target.value)}
                />
              </Field>
            </div>

            <div className="my-3 max-h-56 overflow-y-auto rounded-lg border border-slate-200 dark:border-slate-700">
              {ochirishYuklanmoqda ? (
                <Spinner label="Yuklanmoqda..." className="py-4" />
              ) : ochirishReaderlar?.results.length ? (
                <ul className="divide-y divide-slate-100 dark:divide-slate-700">
                  {ochirishReaderlar.results.map((k) => (
                    <li key={k.id} className="flex items-center gap-3 px-3 py-2">
                      <input
                        type="checkbox"
                        id={`ochirish-${k.id}`}
                        checked={tanlanganIds.includes(k.id)}
                        onChange={() => tanlovniAlmashtir(k.id)}
                        className="h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-600"
                      />
                      <label htmlFor={`ochirish-${k.id}`} className="min-w-0 flex-1 cursor-pointer">
                        <span className="block truncate text-sm font-medium text-slate-800 dark:text-slate-200">
                          {k.fish}
                        </span>
                        <span className="block text-xs text-slate-500 dark:text-slate-400">
                          {k.sinf ? `${k.sinf}-sinf` : k.kasb || '—'}
                          {k.telegram_id ? '' : ' · Telegram yo‘q'}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="px-3 py-4 text-center text-sm text-slate-400">Kitobxon topilmadi.</p>
              )}
            </div>

            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {tanlanganIds.length} ta tanlangan
                {ochirishReaderlar && ochirishReaderlar.count > ochirishReaderlar.results.length
                  ? ` · jami ${ochirishReaderlar.count} ta (qidirib toping)`
                  : ''}
              </span>
              {tanlanganIds.length > 0 && (
                <button
                  type="button"
                  onClick={() => setTanlanganIds([])}
                  className="text-xs text-brand-600 hover:underline dark:text-brand-400"
                >
                  Tanlovni tozalash
                </button>
              )}
            </div>

            <Button
              variant="danger"
              onClick={() => setOchirishTasdiq(true)}
              disabled={!tanlanganIds.length}
              className="w-full"
            >
              <Icons.trash className="h-4 w-4" />
              Tanlanganlarni o'chirish
            </Button>

            {ochirishNatija && (
              <div className="mt-4 space-y-2 text-sm">
                <p className="font-medium text-emerald-700 dark:text-emerald-400">
                  {ochirishNatija.ochirildi} ta o'chirildi.
                </p>
                {ochirishNatija.ochirilmadi.length > 0 && (
                  <ul className="space-y-1 rounded-lg bg-amber-50 p-3 text-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
                    {ochirishNatija.ochirilmadi.map((k) => (
                      <li key={k.id}>
                        {k.fish} — {k.sabab}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </Card>

        </div>
      </div>

      <Card className="mt-5 p-5">
        <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
          <Icons.bell className="h-5 w-5 text-brand-600 dark:text-brand-400" />
          Kitobxonlarga xabar yuborish
        </h2>
        <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
          {library ? 'Bitta kitobxonga yoki barcha kitobxonlarga' : `Bitta ${rolNomi}, butun sinf yoki barcha sinflarga`} Telegram orqali xabar yuborishingiz mumkin.
        </p>
        <form onSubmit={xabarYuborish}>
          <div className="grid gap-4 sm:grid-cols-2">
            {!library && <Field>
              <Label htmlFor="xabar-rol">Kimga</Label>
              <Select
                id="xabar-rol"
                value={xabar.rol}
                onChange={(e) =>
                  setXabar({
                    tur: xabar.tur,
                    rol: e.target.value as OquvchiRol,
                    matn: xabar.matn,
                  })
                }
              >
                <option value="oquvchi">O'quvchilarga</option>
                <option value="oqituvchi">O'qituvchilarga</option>
              </Select>
            </Field>}
            <Field>
              <Label htmlFor="xabar-tur">Yuborish usuli</Label>
              <Select
                id="xabar-tur"
                value={xabar.tur}
                onChange={(e) =>
                  setXabar({
                    rol: xabar.rol,
                    tur: e.target.value as XabarYuborishPayload['tur'],
                    matn: xabar.matn,
                  })
                }
              >
                <option value="shaxs">Bitta {rolNomi}</option>
                {!library && <option value="sinf">Sinf bo'yicha</option>}
                <option value="hamma">{library ? 'Barcha kitobxonlarga' : 'Barcha sinflarga'}</option>
              </Select>
            </Field>
          </div>

          {xabar.tur === 'shaxs' && (
            <>
              <Field>
                <Label htmlFor="xabar-qidiruv">{library ? 'Kitobxon' : xabar.rol === 'oquvchi' ? 'O‘quvchi' : 'O‘qituvchi'} qidirish</Label>
                <Input
                  id="xabar-qidiruv"
                  placeholder={library ? 'Ism yoki telefon...' : 'Ism, sinf yoki telefon...'}
                  value={kitobxonQidiruv}
                  onChange={(e) => setKitobxonQidiruv(e.target.value)}
                />
              </Field>
              <Field>
                <Label htmlFor="xabar-oquvchi">Kitobxonni tanlang</Label>
                {kitobxonlarYuklanmoqda ? (
                  <Spinner label="Yuklanmoqda..." className="py-2" />
                ) : (
                  <Select
                    id="xabar-oquvchi"
                    value={xabar.oquvchi ?? 0}
                    onChange={(e) => setXabar({ ...xabar, oquvchi: Number(e.target.value) || undefined })}
                  >
                    <option value={0}>Tanlang...</option>
                    {kitobxonlar?.results.map((k) => (
                      <option key={k.id} value={k.id}>
                        {k.fish}
                        {k.sinf ? ` — ${k.sinf}-sinf` : k.kasb ? ` — ${k.kasb}` : ''}
                        {k.telegram_id ? '' : ' (Telegram yo‘q)'}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
            </>
          )}

          {xabar.tur === 'sinf' && !library && (
            <Field>
              <Label htmlFor="xabar-sinf">Sinf</Label>
              {sinflarYuklanmoqda ? (
                <Spinner label="Sinflar yuklanmoqda..." className="py-2" />
              ) : (
                <Select
                  id="xabar-sinf"
                  value={xabar.sinf ?? ''}
                  onChange={(e) => setXabar({ ...xabar, sinf: e.target.value || undefined })}
                >
                  <option value="">Tanlang...</option>
                  {sinflar?.map((sinf) => (
                    <option key={sinf} value={sinf}>
                      {sinf}-sinf
                    </option>
                  ))}
                </Select>
              )}
              {!sinflarYuklanmoqda && !sinflar?.length && (
                <p className="mt-1 text-xs text-slate-400">Bu rolda sinflar topilmadi.</p>
              )}
            </Field>
          )}

          {xabar.tur === 'hamma' && (
            <p className="mb-4 rounded-lg border border-slate-200 bg-canvas px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
              {library ? 'Barcha faol kitobxonlarga yuboriladi.' : 'Tanlangan roldagi barcha faol kitobxonlarga (barcha sinflarga) yuboriladi.'}
            </p>
          )}

          <Field>
            <Label htmlFor="xabar-matn">Xabar matni</Label>
            <Textarea
              id="xabar-matn"
              rows={4}
              placeholder="Xabaringizni yozing..."
              value={xabar.matn}
              onChange={(e) => setXabar({ ...xabar, matn: e.target.value })}
              required
            />
          </Field>

          <Button type="submit" loading={xabarMut.isPending} disabled={!xabar.matn.trim()}>
            <Icons.send className="h-4 w-4" />
            Xabarni yuborish
          </Button>
        </form>
      </Card>

      <Card className="mt-5 p-5">
        <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
          <Icons.alert className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          Xatolik haqida xabar berish
        </h2>
        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
          Saytda biror nosozlik yuz bersa, uning tavsifini yuboring — xabar saqlanadi va
          kutubxona egasi/administratorlarining Telegram'iga yetkaziladi.
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!xatoMatn.trim()) return
            xatoMut.mutate()
          }}
        >
          <Field>
            <Label htmlFor="xato-matn">Nima xatolik yuz berdi?</Label>
            <Textarea
              id="xato-matn"
              rows={3}
              maxLength={2000}
              placeholder="Masalan: kitob berishda «Saqlash» tugmasi ishlamayapti..."
              value={xatoMatn}
              onChange={(e) => setXatoMatn(e.target.value)}
              required
            />
          </Field>
          <Field>
            <Label htmlFor="xato-sahifa">Qaysi sahifada? (ixtiyoriy)</Label>
            <Input
              id="xato-sahifa"
              placeholder={window.location.pathname}
              value={xatoSahifa}
              onChange={(e) => setXatoSahifa(e.target.value)}
              maxLength={300}
            />
          </Field>
          <label className="mb-4 flex cursor-pointer items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={autoXato}
              onChange={(e) => {
                setAutoXato(e.target.checked)
                avtomatikHolatniSaqla(e.target.checked)
              }}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-600"
            />
            <span>
              Xatolik yuz berganda avtomatik yuborish
              <span className="block text-xs text-slate-400">
                Ushlanmagan xatolar, rad etilgan so'rovlar va server (5xx) xatolari yuboriladi.
              </span>
            </span>
          </label>
          <Button type="submit" loading={xatoMut.isPending} disabled={!xatoMatn.trim()}>
            <Icons.alert className="h-4 w-4" />
            Xatolik haqida yuborish
          </Button>
        </form>

        <div className="mt-5 border-t border-slate-100 pt-4 dark:border-slate-700">
          <h3 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Oxirgi xatolik xabarlari
          </h3>
          {xatoliklarYuklanmoqda ? (
            <Spinner label="Yuklanmoqda..." className="py-3" />
          ) : xatoliklar?.length ? (
            <ul className="divide-y divide-slate-100 dark:divide-slate-700">
              {xatoliklar.map((x: XatolikXabari) => (
                <li key={x.id} className="py-2 text-sm">
                  <div className="whitespace-pre-wrap break-words text-slate-800 dark:text-slate-200">
                    {x.matn}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-400">
                    {x.tur === 'avtomatik' ? 'Avtomatik' : 'Qo‘lda'} · {x.yuborgan} ·{' '}
                    {x.sahifa || '—'} ·{' '}
                    {new Date(x.yaratilgan).toLocaleString('uz-UZ')}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-2 text-sm text-slate-400">Hali xatolik xabari yuborilmagan.</p>
          )}
        </div>
      </Card>

      <ProfilePreferences />

      <ConfirmDialog
        open={ochirishTasdiq}
        title="Kitobxonlarni o'chirish"
        message={
          <>
            Tanlangan <b>{tanlanganIds.length}</b> ta kitobxon ro'yxatdan o'chiriladi. Qaytarilmagan kitobi yoki kutilayotgan band so'rovi borlar o'chirilmaydi (sababi ko'rsatiladi). Bu amalni qaytarib bo'lmaydi.
          </>
        }
        confirmLabel="O'chirish"
        loading={ochirishMut.isPending}
        onConfirm={() => ochirishMut.mutate(tanlanganIds)}
        onCancel={() => setOchirishTasdiq(false)}
      />

    </div>
  )
}
