import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { errorMessage } from '../api/client'
import { Button, Card, ErrorBanner, Field, Input, Label } from '../components/ui'

export function Login() {
  const { status, login } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Foydalanuvchi kirishdan keyin kutayotgan sahifaga qaytadi. Manba
  // ikkalida bo'lishi mumkin: `?from=` (RequireAuth) yoki `state.from`.
  const params = new URLSearchParams(location.search)
  const from =
    params.get('from') ?? (location.state as { from?: string } | null)?.from ?? '/'

  if (status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 dark:bg-slate-900">
      <Card className="w-full max-w-sm p-8">
        <div className="mb-6 text-center">
          <div className="mb-2 text-3xl">📖</div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Kutubxona tizimi</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Kutubxonachi hisobingizga kiring</p>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
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
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Kirilmoqda...' : 'Kirish'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
