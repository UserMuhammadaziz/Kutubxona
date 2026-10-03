import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore, isAdmin } from '../store/auth'
import { Spinner } from './ui'

export function RequireAuth() {
  const status = useAuthStore((s) => s.status)
  const joylashuv = useLocation()

  if (status === 'idle' || status === 'loading') return <Spinner />
  if (status === 'unauthenticated') {
    // Foydalanuvchi kirishdan keyin avvalgi sahifaga qaytishi kerak —
    // aks holda kirish oynasi har doim `/` ga tashlab ketadi va u
    // kutayotgan sahifa yo'qoladi.
    const qaytish = `${joylashuv.pathname}${joylashuv.search}`
    return <Navigate to={`/login?from=${encodeURIComponent(qaytish)}`} replace />
  }

  return <Outlet />
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user)
  if (!isAdmin(user)) return <Navigate to="/" replace />
  return <Outlet />
}
