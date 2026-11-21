import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { errorMessage } from '../api/client'
import { Button, Card, ErrorBanner, Field, Input, Label } from '../components/ui'
import { LogoMark } from '../components/Logo'

type OrgTuri = 'library' | 'school' | 'university' | 'office' | 'other'

export function Register() {
  const { status, register } = useAuthStore()
  const location = useLocation()
  const [step, setStep] = useState<'user' | 'org'>('user')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [fullName, setFullName] = useState('')
  const [kutubxonaNomi, setKutubxonaNomi] = useState('')
  const [turi, setTuri] = useState<OrgTuri>('library')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const params = new URLSearchParams(location.search)
  const from = params.get('from') ?? '/'

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas px-4 dark:bg-slate-900">
        <Card className="w-full max-w-md p-8 text-center">
          <LogoMark className="mx-auto mb-3 h-14 w-14" />
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Ariza yuborildi
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Kutubxonangiz administrator tasdiqlagach faollashadi. Tasdiqlanguncha kutib turing.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            Kirish sahifasiga qaytish
          </Link>
        </Card>
      </div>
    )
  }

  if (status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (step === 'user') {
      if (password !== passwordConfirm) {
        setError('Parollar mos emas.')
        return
      }
      if (password.length < 8) {
        setError('Parol kamida 8 belgidan iborat bo‘lishi kerak.')
        return
      }
      setStep('org')
      return
    }

    setLoading(true)
    try {
      await register({
        username,
        password,
        password_confirm: passwordConfirm,
        full_name: fullName,
        kutubxona_nomi: kutubxonaNomi,
        turi,
      })
      setDone(true)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 dark:bg-slate-900">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <LogoMark className="mx-auto mb-3 h-14 w-14" />
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Kutubxona yaratish
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {step === 'user' ? '1-qadam: hisob ma’lumotlari' : '2-qadam: kutubxona ma’lumotlari'}
          </p>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          {step === 'user' ? (
            <>
              <Field>
                <Label>Foydalanuvchi nomi</Label>
                <Input
                  autoFocus
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </Field>
              <Field>
                <Label>Ism familiyangiz</Label>
                <Input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                />
              </Field>
              <Field>
                <Label>Parol</Label>
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </Field>
              <Field>
                <Label>Parolni takrorlang</Label>
                <Input
                  type="password"
                  required
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  autoComplete="new-password"
                />
              </Field>
            </>
          ) : (
            <>
              <Field>
                <Label>Kutubxona nomi</Label>
                <Input
                  autoFocus
                  required
                  value={kutubxonaNomi}
                  onChange={(e) => setKutubxonaNomi(e.target.value)}
                  placeholder="Masalan: 1-sonli maktab kutubxonasi"
                />
              </Field>
              <Field>
                <Label>Tashkilot turi</Label>
                <select
                  className="w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
                  value={turi}
                  onChange={(e) => setTuri(e.target.value as OrgTuri)}
                >
                  <option value="library">Kutubxona</option>
                  <option value="school">Maktab / ta'lim muassasasi</option>
                  <option value="university">Universitet / kollej</option>
                  <option value="office">Ofis / tashkilot</option>
                  <option value="other">Boshqa</option>
                </select>
              </Field>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Kutubxona "kutilmoqda" holatida yaratiladi va administrator tasdiqlagach ishlaydi.
              </p>
            </>
          )}

          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
            {step === 'org' && (
              <Button type="button" variant="secondary" onClick={() => setStep('user')}>
                Orqaga
              </Button>
            )}
            <Button type="submit" loading={loading}>
              {step === 'user' ? 'Davom etish' : 'Yaratish'}
            </Button>
          </div>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          Allaqachon hisobingiz bormi?{' '}
          <Link to="/login" className="text-brand-600 hover:underline">
            Kirish
          </Link>
        </p>
      </Card>
    </div>
  )
}
