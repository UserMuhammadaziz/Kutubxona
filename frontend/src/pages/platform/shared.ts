import { useQuery } from '@tanstack/react-query'
import { platformApi, type AuditEntry, type OrgStatus, type PlatformSubscription, type SubscriptionStatus } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { formatDate, formatMoney, humanize } from '../../lib/format'

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

export const SOURCE_LABELS: Record<string, string> = {
  direct: 'To‘g‘ridan-to‘g‘ri',
  unknown: 'Noma’lum (kuzatuvdan oldin)',
  google: 'Google',
  yandex: 'Yandex',
  telegram: 'Telegram',
  instagram: 'Instagram',
  facebook: 'Facebook',
  youtube: 'YouTube',
  tiktok: 'TikTok',
}
export const MEDIUM_LABELS: Record<string, string> = {
  cpc: 'reklama',
  ppc: 'reklama',
  paid: 'reklama',
  organic: 'qidiruv',
  social: 'ijtimoiy tarmoq',
  referral: 'havola',
  email: 'e-mail',
  none: '',
}

export const sourceLabel = (s: string) => SOURCE_LABELS[s] ?? s
export const mediumLabel = (m: string) => (m in MEDIUM_LABELS ? MEDIUM_LABELS[m] : m)

export const AUDIT_ACTIONS: Record<string, string> = {
  'organization.registration_requested': 'Yangi ariza keldi',
  'organization.created_by_platform': 'Tashkilot yaratildi',
  'organization.updated_by_platform': "Tashkilot ma'lumotlari o'zgartirildi",
  'organization.deleted': "Tashkilot o'chirildi",
  'organization.pending': "Kutish holatiga o'tkazildi",
  'organization.active': 'Tashkilot faollashtirildi',
  'organization.rejected': 'Ariza rad etildi',
  'organization.suspended': "Tashkilot to'xtatildi",
  'organization.archived': 'Tashkilot arxivlandi',
  'organization.subscription_changed': "Obuna o'zgartirildi",
  'plan.created': 'Tarif yaratildi',
  'plan.updated': "Tarif o'zgartirildi",
  'plan.deleted': "Tarif o'chirildi",
  'staff.created': "Xodim qo'shildi",
}

export const actionLabel = (code: string) => AUDIT_ACTIONS[code] ?? humanize(code.replace(/\./g, '_'))

/** The one detail worth reading: reason, plan or the deleted name. */
export function auditDetail(a: Pick<AuditEntry, 'action' | 'metadata'> & { organization_nomi?: string | null }): string {
  const m = a.metadata ?? {}
  if (a.action === 'organization.subscription_changed') {
    const status = SUBSCRIPTION_LABELS[m.status as keyof typeof SUBSCRIPTION_LABELS] ?? ''
    return [m.plan_name ?? m.plan, status].filter(Boolean).join(', ')
  }
  const value = m.reason || m.name || (a.organization_nomi ? '' : m.nomi) || m.username
  return value ? String(value) : ''
}

