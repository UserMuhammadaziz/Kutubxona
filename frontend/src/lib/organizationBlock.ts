import type { User } from '../types'

export type BlockStatus = 'pending' | 'suspended' | 'rejected' | 'archived' | 'none'

export interface OrganizationBlock {
  id: number | null
  name: string
  status: BlockStatus
}

interface BlockSource {
  user: User | null
  organizationId: number | null
  noOrganization: boolean
}

/** Why the selected library cannot be used right now, or null when it is active. */
export function findOrganizationBlock({ user, organizationId, noOrganization }: BlockSource): OrganizationBlock | null {
  const libraries = user?.kutubxonalar ?? []
  if (!libraries.length) {
    return user && noOrganization && !user.is_platform ? { id: null, name: '', status: 'none' } : null
  }
  const current = libraries.find((k) => k.id === organizationId)
  // Older API responses carry no status: treat them as active.
  if (!current?.status || current.status === 'active') return null
  return { id: current.id, name: current.nomi, status: current.status as BlockStatus }
}

/** Several libraries and none chosen yet: tenant requests have no target. */
export const needsLibraryChoice = ({ user, organizationId }: Omit<BlockSource, 'noOrganization'>) =>
  (user?.kutubxonalar?.length ?? 0) > 1 && organizationId === null
