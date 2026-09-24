import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { finesApi, loansApi, readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Badge, Button, Card, PageHeader, Spinner, Table } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'

export function ReaderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const readerId = Number(id)

  const { data: reader, isLoading } = useQuery({ queryKey: ['readers', readerId], queryFn: () => readersApi.get(readerId) })

  const returnMut = useMutation({
    mutationFn: (loanId: number) => loansApi.return(loanId),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['readers', readerId] })
      if (res.jarima_summasi) alert(`Kitob qaytarildi. Jarima: ${formatMoney(res.jarima_summasi)}`)
    },
    onError: (err) => alert(errorMessage(err)),
  })

  const payMut = useMutation({
    mutationFn: (fineId: number) => finesApi.pay(fineId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['readers', readerId] }),
    onError: (err) => alert(errorMessage(err)),
  })

  if (isLoading || !reader) return <Spinner />

  return (
    <div>
      <button onClick={() => navigate(-1)} className="mb-4 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
        ← Orqaga
      </button>
      <PageHeader
        title={reader.fish}
        subtitle={`${reader.karta_raqami} · ${reader.telefon}`}
        actions={<Badge tone={reader.faol ? 'green' : 'red'}>{reader.faol ? 'Faol' : 'Faol emas'}</Badge>}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-1">
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Ro'yxatdan o'tgan sana</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{formatDate(reader.royxat_sanasi)}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Tug'ilgan sana</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{formatDate(reader.tugilgan_sana)}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Manzil</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{reader.manzil || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Telegram</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{reader.telegram_id ? `#${reader.telegram_id}` : 'Bog‘lanmagan'}</dd>
            </div>
          </dl>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Joriy kitoblar ({reader.joriy_kitoblari.length})</h2>
            <Table>
              <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Kitob</th>
                  <th className="px-4 py-3">Berilgan</th>
                  <th className="px-4 py-3">Muddat</th>
                  <th className="px-4 py-3">Qolgan kun</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {reader.joriy_kitoblari.map((l) => (
                  <tr key={l.id}>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{l.kitob_nomi}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(l.berilgan_sana)}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(l.qaytarish_muddati)}</td>
                    <td className="px-4 py-3">
                      <Badge tone={l.qolgan_kun < 0 ? 'red' : l.qolgan_kun <= 2 ? 'amber' : 'green'}>{l.qolgan_kun} kun</Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" onClick={() => returnMut.mutate(l.id)} disabled={returnMut.isPending}>
                        Qaytarish
                      </Button>
                    </td>
                  </tr>
                ))}
                {!reader.joriy_kitoblari.length && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">
                      Joriy kitoblar yo'q
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">To'lanmagan jarimalar ({reader.jarimalari.length})</h2>
            <Table>
              <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Kitob</th>
                  <th className="px-4 py-3">Kechikkan kun</th>
                  <th className="px-4 py-3">Summa</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {reader.jarimalari.map((f) => (
                  <tr key={f.id}>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{f.kitob_nomi}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{f.kechikkan_kunlar}</td>
                    <td className="px-4 py-3 font-medium text-red-600 dark:text-red-400">{formatMoney(f.summa)}</td>
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" variant="secondary" onClick={() => payMut.mutate(f.id)} disabled={payMut.isPending}>
                        To'landi deb belgilash
                      </Button>
                    </td>
                  </tr>
                ))}
                {!reader.jarimalari.length && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">
                      To'lanmagan jarimalar yo'q
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  )
}
