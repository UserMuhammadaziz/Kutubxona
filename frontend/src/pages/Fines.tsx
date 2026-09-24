import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { finesApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Badge, Button, Card, EmptyState, PageHeader, Pagination, Select, Spinner, Table } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'

export function Fines() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [tolandimi, setTolandimi] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['fines', page, tolandimi],
    queryFn: () => finesApi.list({ page, tolandimi: tolandimi === '' ? undefined : tolandimi === 'true' }),
  })

  const payMut = useMutation({
    mutationFn: (id: number) => finesApi.pay(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['fines'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  return (
    <div>
      <PageHeader title="Jarimalar" subtitle="Kechiktirib qaytarilgan kitoblar uchun jarimalar" />

      <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
        <div className="w-56">
          <Select value={tolandimi} onChange={(e) => setTolandimi(e.target.value)}>
            <option value="">Barchasi</option>
            <option value="false">To'lanmagan</option>
            <option value="true">To'langan</option>
          </Select>
        </div>
      </Card>

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="Jarimalar topilmadi" />}

      {!isLoading && !!data?.results.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">O'quvchi</th>
              <th className="px-4 py-3">Kitob</th>
              <th className="px-4 py-3">Kechikkan kun</th>
              <th className="px-4 py-3">Summa</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.results.map((f) => (
              <tr key={f.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{f.oquvchi_fish}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{f.kitob_nomi}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{f.kechikkan_kunlar}</td>
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{formatMoney(f.summa)}</td>
                <td className="px-4 py-3">
                  <Badge tone={f.tolandimi ? 'green' : 'red'}>{f.tolandimi ? "To'langan" : "To'lanmagan"}</Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {!f.tolandimi && (
                    <Button size="sm" onClick={() => payMut.mutate(f.id)} disabled={payMut.isPending}>
                      To'landi
                    </Button>
                  )}
                  {f.tolandimi && f.tolangan_sana && <span className="text-xs text-slate-400 dark:text-slate-500">{formatDate(f.tolangan_sana)}</span>}
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
