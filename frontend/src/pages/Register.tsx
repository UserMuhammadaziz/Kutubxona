import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { authApi, type RegisterPayload } from '../api/resources'
import { errorMessage, tokenStore } from '../api/client'
import { useAuthStore } from '../store/auth'
import { isCompletePhone } from '../lib/phone'
import { askPushPermission, subscribeToPush } from '../lib/push'
import { PhoneInput, Button, Card, ErrorBanner, Field, Input, Label, Select } from '../components/ui'
import { LogoMark } from '../components/Logo'
import { AuthAside } from '../components/AuthAside'

const TURLAR: { value: RegisterPayload['turi']; label: string }[] = [
  { value: 'library', label: 'Kutubxona' },
  { value: 'school', label: "Maktab / ta'lim muassasasi" },
  { value: 'university', label: 'Universitet / kollej' },
  { value: 'office', label: 'Ofis / tashkilot' },
  { value: 'other', label: 'Boshqa' },
]

export function Register() {
  const status = useAuthStore((s) => s.status)
  const hydrate = useAuthStore((s) => s.hydrate)
  const navigate = useNavigate()
  const [form, setForm] = useState<RegisterPayload>({
    kutubxona_nomi: '',
    turi: 'library',
    full_name: '',
    telefon: '+998',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [show, setShow] = useState(false)

  if (status === 'authenticated') return <Navigate to="/" replace />

  const set = <K extends keyof RegisterPayload>(k: K, v: RegisterPayload[K]) =>
    setForm((f) => ({ ...f, [k]: v }))

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (form.password !== form.password_confirm) {
      setError('Parollar mos emas.')
      return
    }
    if (!isCompletePhone(form.telefon)) {
      setError('Telefon raqami +998901234567 formatida bo‘lishi kerak.')
      return
    }
    setLoading(true)
    try {
      // Must run first, inside the submit gesture: the browser only shows the prompt then.
      await askPushPermission()
      const { access, refresh } = await authApi.register(form)
      tokenStore.set(access, refresh)
      // Fire and forget: the owner gets a push as soon as the application is approved.
      void subscribeToPush()
      await hydrate()
      navigate('/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <AuthAside />
      <main className="flex items-center justify-center bg-canvas px-4 py-8 sm:px-8 dark:bg-slate-900">
      <Card className="animate-pop w-full max-w-xl p-6 sm:p-10">
        <div className="mb-8 flex items-center gap-4">
          <LogoMark className="h-12 w-12 shrink-0" />
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Tashkilot yaratish</h1>
            <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
              Ariza platforma administratori tasdiqlagach faollashadi
            </p>
          </div>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <div className="grid gap-x-4 sm:grid-cols-2">
            <Field className="sm:col-span-2">
              <Label htmlFor="kutubxona_nomi">Tashkilot nomi</Label>
              <Input id="kutubxona_nomi" value={form.kutubxona_nomi} onChange={(e) => set('kutubxona_nomi', e.target.value)} autoComplete="organization" required />
            </Field>
            <Field className="sm:col-span-2">
              <Label htmlFor="turi">Tashkilot turi</Label>
              <Select id="turi" value={form.turi} onChange={(e) => set('turi', e.target.value as RegisterPayload['turi'])}>
                {TURLAR.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </Select>
            </Field>
            <Field>
              <Label htmlFor="full_name">Ism familiyangiz</Label>
              <Input id="full_name" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} autoComplete="name" required />
            </Field>
            <Field>
              <Label htmlFor="telefon">Telefon (kirish uchun login)</Label>
              <PhoneInput id="telefon" value={form.telefon} onValueChange={(v) => set('telefon', v)} required />
            </Field>
            <Field>
              <Label htmlFor="password">Parol (kamida 8 belgi)</Label>
              <div className="relative">
                <Input id="password" type={show ? 'text' : 'password'} className="pr-10" minLength={8} value={form.password} onChange={(e) => set('password', e.target.value)} autoComplete="new-password" required />
                <button type="button" onClick={() => setShow((v) => !v)} aria-label={show ? 'Parolni yashirish' : "Parolni ko'rsatish"} aria-pressed={show} className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-slate-400 hover:text-slate-600 focus-visible:text-brand-600 focus-visible:outline-none dark:hover:text-slate-200">
                  <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
                    <circle cx="12" cy="12" r="3" />
                    {show && <path d="M4 4l16 16" />}
                  </svg>
                </button>
              </div>
            </Field>
            <Field>
              <Label htmlFor="password_confirm">Parolni takrorlang</Label>
              <Input id="password_confirm" type={show ? 'text' : 'password'} minLength={8} value={form.password_confirm} onChange={(e) => set('password_confirm', e.target.value)} autoComplete="new-password" required />
            </Field>
          </div>
          <p className="mb-5 flex items-start gap-2 rounded-lg bg-brand-50 px-3 py-2.5 text-xs leading-relaxed text-slate-600 dark:bg-slate-700/60 dark:text-slate-300">
            <svg viewBox="0 0 24 24" className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
              <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            Ariza tasdiqlanganda darhol xabar olish uchun brauzer bildirishnomasiga ruxsat bering.
          </p>
          <Button type="submit" className="w-full py-2.5" disabled={loading}>
            {loading ? 'Yuborilmoqda...' : "Ro'yxatdan o'tish"}
          </Button>
        </form>
        <p className="mt-5 text-center text-sm text-slate-500 dark:text-slate-400">
          Akkauntingiz bormi?{' '}
          <Link to="/login" className="font-medium text-brand-600 underline underline-offset-2">Kirish</Link>
        </p>
      </Card>
      </main>
    </div>
  )
}
