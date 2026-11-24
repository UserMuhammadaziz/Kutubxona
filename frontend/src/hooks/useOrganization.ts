import { useQuery } from '@tanstack/react-query'
import { authApi } from '../api/resources'

/** Joriy kutubxona (tashkilot) ma'lumoti; xato bo'lsa jim o'tadi. */
export function useOrganization() {
  return useQuery({
    queryKey: ['organization-info'],
    queryFn: authApi.organization,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

/** Owner (or platform/org administrator) may open the company profile and set up the bot. */
export function canManageCompany(org: { rol?: string | null } | null | undefined): boolean {
  return org?.rol === 'egasi' || org?.rol === 'administrator'
}
