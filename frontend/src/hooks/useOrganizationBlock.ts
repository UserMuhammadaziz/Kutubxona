import { findOrganizationBlock, type OrganizationBlock } from '../lib/organizationBlock'
import { useAuthStore } from '../store/auth'

export type { BlockStatus, OrganizationBlock } from '../lib/organizationBlock'

export const ORG_STATUS_LABELS: Record<string, string> = {
  pending: 'Kutilmoqda',
  suspended: "To'xtatilgan",
  rejected: 'Rad etilgan',
  archived: 'Arxivlangan',
  active: 'Faol',
}

export function useOrganizationBlock(): OrganizationBlock | null {
  const user = useAuthStore((s) => s.user)
  const organizationId = useAuthStore((s) => s.organizationId)
  const noOrganization = useAuthStore((s) => s.noOrganization)
  return findOrganizationBlock({ user, organizationId, noOrganization })
}
