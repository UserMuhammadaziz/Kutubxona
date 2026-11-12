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
