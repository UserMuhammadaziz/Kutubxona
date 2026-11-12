import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { authApi, type RegisterPayload } from '../api/resources'
import { errorMessage, tokenStore } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Button, Card, ErrorBanner, Field, Input, Label, Select } from '../components/ui'
import { LogoMark } from '../components/Logo'

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
    username: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

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
    setLoading(true)
    try {
      const { access, refresh } = await authApi.register(form)
      tokenStore.set(access, refresh)
      await hydrate()
      navigate('/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 py-8 dark:bg-slate-900">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <LogoMark className="mx-auto mb-3 h-14 w-14" />
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Tashkilot yaratish</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Ariza platforma administratori tasdiqlagach faollashadi
          </p>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="kutubxona_nomi">Tashkilot nomi</Label>
            <Input id="kutubxona_nomi" value={form.kutubxona_nomi} onChange={(e) => set('kutubxona_nomi', e.target.value)} autoComplete="organization" required />
          </Field>
          <Field>
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
            <Label htmlFor="username">Foydalanuvchi nomi</Label>
            <Input id="username" value={form.username} onChange={(e) => set('username', e.target.value)} autoComplete="username" required />
          </Field>
          <Field>
            <Label htmlFor="password">Parol (kamida 8 belgi)</Label>
            <Input id="password" type="password" minLength={8} value={form.password} onChange={(e) => set('password', e.target.value)} autoComplete="new-password" required />
          </Field>
          <Field>
            <Label htmlFor="password_confirm">Parolni takrorlang</Label>
            <Input id="password_confirm" type="password" minLength={8} value={form.password_confirm} onChange={(e) => set('password_confirm', e.target.value)} autoComplete="new-password" required />
          </Field>
          <Button type="submit" className="mt-2 w-full" disabled={loading}>
            {loading ? 'Yuborilmoqda...' : "Ro'yxatdan o'tish"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          Akkauntingiz bormi?{' '}
          <Link to="/login" className="text-brand-600 underline">Kirish</Link>
        </p>
      </Card>
    </div>
  )
}
