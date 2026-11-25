import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore, isAdmin } from '../store/auth'
import { PageSkeleton } from './ui'
import { OrganizationGate } from './OrganizationGate'

export function RequireAuth() {
  const status = useAuthStore((s) => s.status)
  const joylashuv = useLocation()

  if (status === 'idle' || status === 'loading') return <div className="mx-auto max-w-5xl p-6"><PageSkeleton /></div>
  if (status === 'unauthenticated') {
    // Foydalanuvchi kirishdan keyin avvalgi sahifaga qaytishi kerak —
    // aks holda kirish oynasi har doim `/` ga tashlab ketadi va u
    // kutayotgan sahifa yo'qoladi.
    if (joylashuv.pathname === '/' && !joylashuv.search) return <Navigate to="/welcome" replace />
    const qaytish = `${joylashuv.pathname}${joylashuv.search}`
    return <Navigate to={`/login?from=${encodeURIComponent(qaytish)}`} replace />
  }

  return (
    <OrganizationGate>
      <Outlet />
    </OrganizationGate>
  )
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user)
  if (!isAdmin(user)) return <Navigate to="/" replace />
  return <Outlet />
}

export function RequirePlatform({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  if (!user?.is_platform) return <Navigate to="/" replace />
  return <>{children}</>
}
