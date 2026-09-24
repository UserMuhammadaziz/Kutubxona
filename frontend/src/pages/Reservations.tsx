import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reservationsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { NAVBAT_HOLATI_LABELS, type NavbatHolati } from '../types'
import { Badge, Button, Card, EmptyState, PageHeader, Pagination, Select, Spinner, Table } from '../components/ui'
import { formatDate } from '../lib/format'

export function Reservations() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['reservations', page, holati],
    queryFn: () => reservationsApi.list({ page, holati: holati || undefined }),
  })

  const cancelMut = useMutation({
    mutationFn: (id: number) => reservationsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  const confirmMut = useMutation({
    mutationFn: (id: number) => reservationsApi.confirm(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  return (
    <div>
      <PageHeader title="Navbatlar" subtitle="Kitob mavjud bo'lmaganda o'quvchilar navbati" />

      <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
        <div className="w-56">
          <Select value={holati} onChange={(e) => setHolati(e.target.value)}>
            <option value="">Barcha holatlar</option>
            {Object.entries(NAVBAT_HOLATI_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="Navbatlar topilmadi" />}

      {!isLoading && !!data?.results.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Kitob</th>
              <th className="px-4 py-3">O'quvchi</th>
              <th className="px-4 py-3">Navbat sanasi</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3">Taklif muddati</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.results.map((r) => (
              <tr key={r.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{r.kitob_nomi}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{r.oquvchi_fish}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(r.navbat_sanasi)}</td>
                <td className="px-4 py-3">
                  <Badge tone={r.holati === 'kutmoqda' ? 'amber' : r.holati === 'taklif_qilindi' ? 'blue' : r.holati === 'yakunlandi' ? 'green' : 'red'}>
                    {NAVBAT_HOLATI_LABELS[r.holati as NavbatHolati]}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{r.taklif_muddati ? formatDate(r.taklif_muddati) : '—'}</td>
                <td className="px-4 py-3 text-right">
                  {(r.holati === 'kutmoqda' || r.holati === 'taklif_qilindi') && (
                    <>
                      <Button
                        size="sm"
                        className="mr-2"
                        disabled={confirmMut.isPending}
                        onClick={() => {
                          if (confirm(`${r.kitob_nomi} kitobini o'quvchiga berdingizmi? Navbat tasdiqlansinmi?`)) confirmMut.mutate(r.id)
                        }}
                      >
                        Tasdiqlandi
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        disabled={cancelMut.isPending}
                        onClick={() => {
                          if (confirm("Bu navbatni bekor qilmoqchimisiz?")) cancelMut.mutate(r.id)
                        }}
                      >
                        Bekor qilish
                      </Button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}
    </div>
  )
}
