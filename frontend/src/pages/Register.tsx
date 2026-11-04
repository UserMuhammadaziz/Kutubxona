import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { errorMessage } from '../api/client'
import { Button, Card, ErrorBanner, Field, Input, Label } from '../components/ui'
import { LogoMark } from '../components/Logo'

export function Register() {
  const { status, login, hydrate } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [organizationType, setOrganizationType] = useState<'library' | 'school' | 'university' | 'office' | 'other'>('library')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showOrganizationForm, setShowOrganizationForm] = useState(false)

  // Foydalanuvchi kirishdan keyin kutayotgan sahifaga qaytadi. Manba
  // ikkalida bo'lishi mumkin: `?from=` (RequireAuth) yoki `state.from`.
  const params = new URLSearchParams(location.search)
  const from =
    params.get('from') ?? (location.state as { from?: string } | null)?.from ?? '/'

  if (status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  async function register() {
    setError(null)
    setLoading(true)
    try {
      // API orqali ro'yxatdan o'tish va organization yaratish
      const { access, refresh, user, organization } = await authApi.register(
        username,
        password,
        fullName,
        organizationName,
        organizationType
      )
      tokenStore.set(access, refresh)
      set({ user, status: 'authenticated' })
      // Organizatsiya holati pending bo'lgani uchun, foydalanuvchini
      // direkt dashboard ga joylashtiramiz va admin tasdiqlashga kutyamiz
      navigate('/organization-pending', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 dark:bg-slate-900">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <LogoMark className="mx-auto mb-3 h-14 w-14" />
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Kutubxona SaaS</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Tashkilot tuzing va boshqaring</p>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          {showOrganizationForm ? (
            <OrganizationForm setShowOrganizationForm={setShowOrganizationForm} />
          ) : (
            <RegistrationForm setShowOrganizationForm={setShowOrganizationForm} />
          )}
          <div className="mt-6 text-center">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Kirilmoqda...' : 'Davom etish'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

function RegistrationForm({ setShowOrganizationForm }: { setShowOrganizationForm: (value: boolean) => void }) {
  return (
    <Field>
      <Label>Foydalanuvchi nomi</Label>
      <Input
        autoFocus
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
        required
      />
    </Field>
    <Field>
      <Label>Parol</Label>
      <Input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="current-password"
        required
      />
    </Field>
    <Field>
      <Label>Ism familiyangiz</Label>
      <Input
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        autoComplete="name"
        required
      />
    </Field>
    <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
      ya da <span onClick={() => setShowOrganizationForm(true)} className="text-brand-600 cursor-pointer underline">tashkilot yarating</span>
    </p>
  )
}

function OrganizationForm({ setShowOrganizationForm }: { setShowOrganizationForm: (value: boolean) => void }) {
  return (
    <>
      <Field>
        <Label>Tashkilot nomi</Label>
        <Input
          value={organizationName}
          onChange={(e) => setOrganizationName(e.target.value)}
          autoComplete="organization"
          required
        />
      </Field>
      <Field>
        <Label>Tashkilot turi</Label>
        <select
          value={organizationType}
        >
          <option value="library">Kutubxona</option>
          <option value="school">Maktab / ta'lim muassasasi</option>
          <option value="university">Universitet / kollej</option>
          <option value="office">Ofiz / tashkilot</option>
          <option value="other">Boshqa</option>
        </select>
      </Field>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
        Tashkilot "kutilmoqda" holatida bo'ladi va admin tasdiqligachagancha foydalanuvchilar kitoblar bo'yicha murojaat qilishi mumkin.
      </p>
    </>
  )
}

async function onSubmit(e: FormEvent) {
  e.preventDefault()
  setError(null)
  setLoading(true)
  try {
    await register()
    navigate(from, { replace: true })
  } catch (err) {
    setError(errorMessage(err))
  } finally {
    setLoading(false)
  }
}