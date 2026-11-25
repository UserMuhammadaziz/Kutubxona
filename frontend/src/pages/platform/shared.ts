import { useQuery } from '@tanstack/react-query'
import { platformApi, type OrgStatus, type PlatformSubscription, type SubscriptionStatus } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { formatDate, formatMoney } from '../../lib/format'

type Tone = 'slate' | 'green' | 'red' | 'amber' | 'blue'

export const ORG_STATUS: Record<OrgStatus, { label: string; tone: Tone }> = {
  pending: { label: 'Kutilmoqda', tone: 'amber' },
  active: { label: 'Faol', tone: 'green' },
  rejected: { label: 'Rad etilgan', tone: 'red' },
  suspended: { label: "To'xtatilgan", tone: 'red' },
  archived: { label: 'Arxivlangan', tone: 'slate' },
}

export const SUBSCRIPTION_LABELS: Record<SubscriptionStatus, string> = {
  trial: 'Sinov muddati',
  active: 'Faol',
  past_due: "To'lov kechikkan",
  canceled: 'Bekor qilingan',
  expired: 'Muddati tugagan',
}

export const headClass = 'bg-slate-50 text-xs uppercase text-slate-600 dark:bg-slate-700/50 dark:text-slate-300'
export const bodyClass = 'divide-y divide-slate-100 dark:divide-slate-700'

export const planPrice = (price: string | number) => (Number(price) ? formatMoney(price) : 'Bepul')

export const limitText = (limit: number | null) => (limit == null ? 'Cheksiz' : limit.toLocaleString('uz-UZ'))

/** "Sinov, 08.12.2026 gacha" and whether it needs the admin's attention. */
export function subscriptionSummary(sub: PlatformSubscription): { text: string; tone: 'normal' | 'warn' | 'bad' } {
  const end = sub.status === 'trial' ? sub.trial_ends_at : sub.current_period_end
  const until = end ? `${formatDate(end)} gacha` : ''
  switch (sub.effective_status) {
    case 'trial':
      return { text: until ? `Sinov, ${until}` : 'Sinov muddati', tone: 'normal' }
    case 'active':
      return { text: until || 'Muddatsiz', tone: 'normal' }
    case 'past_due':
      return { text: "To'lov kechikkan", tone: 'warn' }
    case 'canceled':
      return { text: 'Bekor qilingan', tone: 'warn' }
    default:
      return { text: end ? `${formatDate(end)} da tugagan` : 'Muddati tugagan', tone: 'bad' }
  }
}

export const usePlans = () => useQuery({ queryKey: ['platform', 'plans'], queryFn: platformApi.plans })

/** The API prefixes field errors with the key ("nomi: ..."), which means nothing to a reader. */
export const formError = (error: unknown) => (error ? errorMessage(error).replace(/^[a-z_]+: /, '') : null)
