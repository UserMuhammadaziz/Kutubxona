import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore, isAdmin } from '../store/auth'
import { Spinner } from './ui'

export function RequireAuth() {
  const status = useAuthStore((s) => s.status)

  if (status === 'idle' || status === 'loading') return <Spinner />
  if (status === 'unauthenticated') return <Navigate to="/login" replace />

  return <Outlet />
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user)
  if (!isAdmin(user)) return <Navigate to="/" replace />
  return <Outlet />
}
