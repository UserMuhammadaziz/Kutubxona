import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { finesApi, loansApi, readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import type { BerishMeni, JarimaMeni } from '../types'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  ErrorState,
  PageHeader,
  ResponsiveList,
  Spinner,
  Table,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { formatDate, formatMoney } from '../lib/format'

export function ReaderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToast()
  const readerId = Number(id)
  const [qaytariladigan, setQaytariladigan] = useState<BerishMeni | null>(null)
  const [tolanadigan, setTolanadigan] = useState<JarimaMeni | null>(null)

  const { data: reader, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['readers', readerId],
    queryFn: () => readersApi.get(readerId),
    retry: false,
  })

  const returnMut = useMutation({
    mutationFn: (loanId: number) => loansApi.return(loanId),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['readers', readerId] })
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      // Kechikib qaytarilgan kitob uchun jarima yuzaga keladi, navbatdagi
      // o'quvchiga taklif yuboriladi — shuning uchun ikkalasini ham yangilaymiz.
      qc.invalidateQueries({ queryKey: ['fines'] })
      qc.invalidateQueries({ queryKey: ['reservations'] })
      setQaytariladigan(null)
      if (res.jarima_summasi) {
        toast.success(`Kitob qaytarildi. Jarima: ${formatMoney(res.jarima_summasi)}`)
      } else {
        toast.success('Kitob qaytarildi. Jarima yo‘q.')
      }
      if (res.navbatga_taklif_ketdimi) {
        toast.info('Kitob band bo‘lgani uchun navbatdagi o‘quvchiga taklif yuborildi.')
      }
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const payMut = useMutation({
    mutationFn: (fineId: number) => finesApi.pay(fineId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['readers', readerId] })
      qc.invalidateQueries({ queryKey: ['fines'] })
      setTolanadigan(null)
      toast.success('Jarima to‘langan deb belgilandi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  if (isLoading) return <Spinner label="O‘quvchi ma’lumotlari yuklanmoqda..." />

  if (isError || !reader) {
    return (
      <div>
        <button
          onClick={() => navigate(-1)}
          className="mb-4 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
        >
          ← Orqaga
        </button>
        <ErrorState
          title="O‘quvchini yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      </div>
    )
  }

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
              <dt className="text-slate-500 dark:text-slate-400">Sinf</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {reader.sinf ? `${reader.sinf}-sinf` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Ro'yxatdan o'tgan sana</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {formatDate(reader.royxat_sanasi)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Tug'ilgan sana</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {formatDate(reader.tugilgan_sana)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Manzil</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{reader.manzil || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Telegram</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {reader.telegram_id ? `#${reader.telegram_id}` : 'Bog‘lanmagan'}
              </dd>
            </div>
          </dl>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
              Joriy kitoblar ({reader.joriy_kitoblari.length})
            </h2>
            {reader.joriy_kitoblari.length ? (
              <ResponsiveList<BerishMeni>
                items={reader.joriy_kitoblari}
                render={(l) => (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
                        {l.kitob_nomi}
                      </div>
                      <Badge tone={l.qolgan_kun < 0 ? 'red' : l.qolgan_kun <= 2 ? 'amber' : 'green'}>
                        {l.qolgan_kun} kun
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      № {l.inventar_raqami} · Muddat: {formatDate(l.qaytarish_muddati)}
                    </div>
                    <Button size="sm" className="w-full" onClick={() => setQaytariladigan(l)}>
                      Qaytarish
                    </Button>
                  </div>
                )}
              >
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
                        <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                          {l.kitob_nomi}
                        </td>
                        <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                          {formatDate(l.berilgan_sana)}
                        </td>
                        <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                          {formatDate(l.qaytarish_muddati)}
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            tone={l.qolgan_kun < 0 ? 'red' : l.qolgan_kun <= 2 ? 'amber' : 'green'}
                          >
                            {l.qolgan_kun} kun
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            size="sm"
                            onClick={() => setQaytariladigan(l)}
                            disabled={returnMut.isPending}
                          >
                            Qaytarish
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ResponsiveList>
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                Joriy kitoblar yo‘q
              </p>
            )}
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
              To'lanmagan jarimalar ({reader.jarimalari.length})
            </h2>
            {reader.jarimalari.length ? (
              <ResponsiveList<JarimaMeni>
                items={reader.jarimalari}
                render={(f) => (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
                        {f.kitob_nomi}
                      </div>
                      <span className="font-semibold text-red-600 dark:text-red-400">
                        {formatMoney(f.summa)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {f.kechikkan_kunlar} kun kechikish
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="w-full"
                      onClick={() => setTolanadigan(f)}
                    >
                      To'landi deb belgilash
                    </Button>
                  </div>
                )}
              >
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
                        <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                          {f.kitob_nomi}
                        </td>
                        <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                          {f.kechikkan_kunlar}
                        </td>
                        <td className="px-4 py-3 font-medium text-red-600 dark:text-red-400">
                          {formatMoney(f.summa)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => setTolanadigan(f)}
                            disabled={payMut.isPending}
                          >
                            To'landi deb belgilash
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ResponsiveList>
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                To‘lanmagan jarimalar yo‘q
              </p>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={!!qaytariladigan}
        title="Kitobni qaytarish"
        confirmLabel="Qaytarish"
        loading={returnMut.isPending}
        message={
          qaytariladigan && (
            <>
              <b>{qaytariladigan.kitob_nomi}</b> ({qaytariladigan.inventar_raqami}) kitobini{' '}
              <b>{reader.fish}</b>dan qaytarasizmi?
              <br />
              <br />
              Muddat o‘tganda jarima avtomatik hisoblanadi.
            </>
          )
        }
        onConfirm={() => qaytariladigan && returnMut.mutate(qaytariladigan.id)}
        onCancel={() => setQaytariladigan(null)}
      />

      <ConfirmDialog
        open={!!tolanadigan}
        title="Jarimani to‘langan belgilash"
        confirmLabel="To‘langan deb belgilash"
        loading={payMut.isPending}
        message={
          tolanadigan && (
            <>
              <b>{tolanadigan.kitob_nomi}</b> uchun <b>{formatMoney(tolanadigan.summa)}</b>{' '}
              jarimani to‘langan deb belgilaysizmi?
            </>
          )
        }
        onConfirm={() => tolanadigan && payMut.mutate(tolanadigan.id)}
        onCancel={() => setTolanadigan(null)}
      />
    </div>
  )
}
