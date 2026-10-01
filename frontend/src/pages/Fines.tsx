import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { finesApi } from '../api/resources'
import { errorMessage } from '../api/client'
import type { Jarima } from '../types'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  ResponsiveList,
  Select,
  Table,
  TableSkeleton,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { formatDate, formatMoney } from '../lib/format'

export function Fines() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [tolandimi, setTolandimi] = useState('')
  const [tasdiqlanadigan, setTasdiqlanadigan] = useState<Jarima | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['fines', page, tolandimi],
    queryFn: () =>
      finesApi.list({ page, tolandimi: tolandimi === '' ? undefined : tolandimi === 'true' }),
  })

  const payMut = useMutation({
    mutationFn: (id: number) => finesApi.pay(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fines'] })
      setTasdiqlanadigan(null)
      toast.success('Jarima to‘langan deb belgilandi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const filtrBor = tolandimi !== ''

  return (
    <div>
      <PageHeader title="Jarimalar" subtitle="Kechiktirib qaytarilgan kitoblar uchun jarimalar" />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="sm:w-64">
          <Select
            value={tolandimi}
            onChange={(e) => {
              setTolandimi(e.target.value)
              setPage(1)
            }}
            aria-label="To'lanish holati"
          >
            <option value="">Barchasi</option>
            <option value="false">To'lanmagan</option>
            <option value="true">To'langan</option>
          </Select>
        </div>
      </Card>

      {isLoading && <TableSkeleton rows={6} cols={6} />}

      {isError && !isLoading && (
        <ErrorState
          title="Jarimalarni yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon={filtrBor ? '🔍' : '🎉'}
          title={filtrBor ? 'Jarima topilmadi' : 'Jarima yo‘q'}
          description={
            filtrBor
              ? 'Boshqa filtr holatini tanlab ko‘ring.'
              : 'Hammasida jarima yo‘q — ajoyib holat!'
          }
          action={
            filtrBor ? (
              <Button variant="secondary" size="sm" onClick={() => setTolandimi('')}>
                Filtrni tozalash
              </Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Jarima>
          items={data.results}
          render={(f) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
                  {f.oquvchi_fish}
                </div>
                <Badge tone={f.tolandimi ? 'green' : 'red'}>
                  {f.tolandimi ? 'To‘langan' : 'To‘lanmagan'}
                </Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">📖 {f.kitob_nomi}</div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {f.kechikkan_kunlar} kun kechikish
                </span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  {formatMoney(f.summa)}
                </span>
              </div>
              {!f.tolandimi && (
                <Button size="sm" className="w-full" onClick={() => setTasdiqlanadigan(f)}>
                  To‘landi deb belgilash
                </Button>
              )}
              {f.tolandimi && f.tolangan_sana && (
                <div className="text-xs text-slate-400">💳 {formatDate(f.tolangan_sana)}</div>
              )}
            </div>
          )}
        >
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
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                    {f.oquvchi_fish}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{f.kitob_nomi}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{f.kechikkan_kunlar}</td>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                    {formatMoney(f.summa)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={f.tolandimi ? 'green' : 'red'}>
                      {f.tolandimi ? "To'langan" : "To'lanmagan"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {!f.tolandimi && (
                      <Button size="sm" onClick={() => setTasdiqlanadigan(f)} disabled={payMut.isPending}>
                        To'landi
                      </Button>
                    )}
                    {f.tolandimi && f.tolangan_sana && (
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        {formatDate(f.tolangan_sana)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </ResponsiveList>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <ConfirmDialog
        open={!!tasdiqlanadigan}
        title="Jarimani to‘langan belgilash"
        confirmLabel="To‘langan deb belgilash"
        loading={payMut.isPending}
        message={
          tasdiqlanadigan && (
            <>
              <b>{tasdiqlanadigan.oquvchi_fish}</b> uchun{' '}
              <b>{formatMoney(tasdiqlanadigan.summa)}</b> jarimani to‘langan deb belgilaysizmi?
              <br />
              <br />
              O‘quvchiga Telegram orqali tasdiqlash xabari yuboriladi.
            </>
          )
        }
        onConfirm={() => tasdiqlanadigan && payMut.mutate(tasdiqlanadigan.id)}
        onCancel={() => setTasdiqlanadigan(null)}
      />
    </div>
  )
}
