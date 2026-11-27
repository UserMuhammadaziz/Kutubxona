import { Link } from 'react-router-dom'
import { canManageCompany, useOrganization } from '../hooks/useOrganization'

const WARN_DAYS = 5

/** Reminds the owner/admin to pay when the subscription is about to end or has ended. */
export function SubscriptionBanner() {
  const org = useOrganization().data
  const sub = org?.obuna
  if (!sub || !canManageCompany(org)) return null
  const end = sub.status === 'trial' ? sub.trial_ends_at : sub.current_period_end
  const expired = sub.status === 'expired'
  const left = end ? Math.ceil((new Date(end).getTime() - Date.now()) / 86_400_000) : null
  if (!expired && (left === null || left > WARN_DAYS || !['trial', 'active'].includes(sub.status))) return null
  return (
    <div
      className={
        expired
          ? 'mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200'
          : 'mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200'
      }
    >
      <span>
        {expired
          ? 'Kutubxona obunasi muddati tugagan.'
          : `Obuna ${left === 0 ? 'bugun' : `${left} kundan keyin`} tugaydi.`}
      </span>
      <Link to="/billing" className="font-medium underline">
        Obunani uzaytirish
      </Link>
    </div>
  )
}
