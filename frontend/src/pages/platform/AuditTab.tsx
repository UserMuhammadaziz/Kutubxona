import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { platformApi, type AuditEntry } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { EmptyState, ErrorState, Pagination, ResponsiveList, Table, TableSkeleton } from '../../components/ui'
import { formatDateTime, humanize } from '../../lib/format'
import { bodyClass, headClass, SUBSCRIPTION_LABELS } from './shared'

const ACTIONS: Record<string, string> = {
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

const actionLabel = (code: string) => ACTIONS[code] ?? humanize(code.replace(/\./g, '_'))

/** The one detail worth reading: reason, plan or the deleted name. */
function detail(a: AuditEntry): string {
  const m = a.metadata ?? {}
  if (a.action === 'organization.subscription_changed') {
    const status = SUBSCRIPTION_LABELS[m.status as keyof typeof SUBSCRIPTION_LABELS] ?? ''
    return [m.plan_name ?? m.plan, status].filter(Boolean).join(', ')
  }
  const value = m.reason || m.name || (a.organization_nomi ? '' : m.nomi) || m.username
  return value ? String(value) : ''
}

export function AuditTab() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['platform', 'audit', page],
    queryFn: () => platformApi.audit(page),
    placeholderData: (previous) => previous,
  })
  if (isLoading) return <TableSkeleton rows={6} cols={4} />
  if (isError || !data) return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(error)} onRetry={() => void refetch()} retrying={isFetching} />
  return (
    <div aria-busy={isFetching}>
      <ResponsiveList
        items={data.results}
        empty={<EmptyState title="Jurnal bo'sh" description="Tashkilot va tariflar ustidagi har bir amal shu yerga yoziladi." />}
        render={(a) => (
          <div className="text-sm">
            <div className="font-medium text-slate-900 dark:text-slate-100">{actionLabel(a.action)}</div>
            <div className="mt-0.5 break-words text-slate-600 dark:text-slate-300">{[a.organization_nomi, detail(a)].filter(Boolean).join(' · ') || '—'}</div>
            <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{formatDateTime(a.yaratilgan)} · {a.actor_username || 'Tizim'}</div>
          </div>
        )}
      >
        <Table>
          <thead className={headClass}>
            <tr>
              <th className="px-4 py-3">Vaqt</th>
              <th className="px-4 py-3">Amal</th>
              <th className="px-4 py-3">Tashkilot</th>
              <th className="px-4 py-3">Tafsilot</th>
              <th className="px-4 py-3">Kim</th>
            </tr>
          </thead>
          <tbody className={bodyClass}>
            {data.results.map((a) => (
              <tr key={a.id}>
                <td className="px-4 py-2.5 whitespace-nowrap tabular-nums text-slate-600 dark:text-slate-300">{formatDateTime(a.yaratilgan)}</td>
                <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-slate-100">{actionLabel(a.action)}</td>
                <td className="px-4 py-2.5">{a.organization_nomi || '—'}</td>
                <td className="max-w-xs px-4 py-2.5 break-words text-slate-600 dark:text-slate-300">{detail(a) || '—'}</td>
                <td className="px-4 py-2.5">{a.actor_username || 'Tizim'}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </ResponsiveList>
      <Pagination count={data.count} page={page} onChange={setPage} />
    </div>
  )
}
