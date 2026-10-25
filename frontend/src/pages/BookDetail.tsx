import type { ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { booksApi, holdsApi } from '../api/resources'
import { Icons } from '../components/icons'
import { Badge, Button, Card, PageHeader, Spinner, Table } from '../components/ui'
import { BAND_HOLATI_LABELS, JANR_LABELS, NAVBAT_HOLATI_LABELS, NUSXA_HOLATI_LABELS, TIL_LABELS, HOLAT_LABELS, type Janr, type NavbatHolati, type NusxaHolati, type BandHolati } from '../types'
import { formatDate, formatMoney, humanize } from '../lib/format'

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-900 dark:text-slate-100">{children}</dd>
    </div>
  )
}

const nusxaTone = { mavjud: 'green', berilgan: 'blue', band: 'amber', tamirda: 'amber', yoqolgan: 'red' } as const

export function BookDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const bookId = Number(id)

  const { data: book, isLoading } = useQuery({ queryKey: ['books', bookId], queryFn: () => booksApi.get(bookId) })
  const { data: queue } = useQuery({ queryKey: ['books', bookId, 'queue'], queryFn: () => booksApi.queue(bookId) })
  const { data: holds } = useQuery({ queryKey: ['books', bookId, 'holds'], queryFn: () => holdsApi.list({ kitob: bookId, holati: 'kutmoqda' }) })

  if (isLoading || !book) return <Spinner />

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        className="mb-4 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        <Icons.arrowLeft className="h-4 w-4" />
        Orqaga
      </button>
      <PageHeader title={book.nomi} subtitle={`${book.muallif} · ${book.nashr_yili}`} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-1">
          <dl className="space-y-3 text-sm">
            {book.isbn && <Fact label="ISBN">{book.isbn}</Fact>}
            <Fact label="Janr">
              <Badge>{JANR_LABELS[book.janr as Janr] ?? humanize(book.janr)}</Badge>
            </Fact>
            {book.til && <Fact label="Til">{TIL_LABELS[book.til] ?? book.til}</Fact>}
            <Fact label="Holati">
              <Badge tone={book.holati === 'mavjud' ? 'green' : book.holati === 'berilgan' ? 'blue' : 'red'}>
                {HOLAT_LABELS[book.holati] ?? humanize(book.holati)}
              </Badge>
            </Fact>
            {book.narh && <Fact label="Narxi">{formatMoney(book.narh)}</Fact>}
            {book.buyurtma_soni != null && <Fact label="Buyurtma soni">{book.buyurtma_soni}</Fact>}
            {book.nashriyot && <Fact label="Nashriyot">{book.nashriyot}</Fact>}
            <Fact label="Qo'shilgan sana">{formatDate(book.qoshilgan_sana)}</Fact>
            {book.tavsif && (
              <div>
                <dt className="text-slate-500 dark:text-slate-400">Tavsif</dt>
                <dd className="text-slate-700 dark:text-slate-200">{book.tavsif}</dd>
              </div>
            )}
          </dl>
        </Card>

        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Nusxalar ({book.nusxalar.length})</h2>
            <Link to="/copies">
              <Button size="sm" variant="secondary">
                Nusxalarni boshqarish
              </Button>
            </Link>
          </div>
          <Table>
            <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Inventar №</th>
                <th className="px-4 py-3">Holati</th>
                <th className="px-4 py-3">Javon</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {book.nusxalar.map((n) => (
                <tr key={n.id}>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{n.inventar_raqami}</td>
                  <td className="px-4 py-3">
                    <Badge tone={nusxaTone[n.holati as NusxaHolati] ?? 'amber'}>
                      {NUSXA_HOLATI_LABELS[n.holati as NusxaHolati] ?? humanize(n.holati)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{n.javon || '—'}</td>
                </tr>
              ))}
              {!book.nusxalar.length && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">
                    Nusxalar yo'q
                  </td>
                </tr>
              )}
            </tbody>
          </Table>

          {!!queue?.length && (
            <>
              <h2 className="mb-3 mt-6 text-lg font-semibold text-slate-900 dark:text-slate-100">Navbat ({queue.length})</h2>
              <Table>
                <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">O'quvchi</th>
                    <th className="px-4 py-3">Holati</th>
                    <th className="px-4 py-3">Sana</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {queue.map((q) => (
                    <tr key={q.id}>
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{q.oquvchi_fish}</td>
                      <td className="px-4 py-3">
                        <Badge tone={q.holati === 'taklif_qilindi' ? 'green' : 'amber'}>{NAVBAT_HOLATI_LABELS[q.holati as NavbatHolati] ?? humanize(q.holati)}</Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(q.navbat_sanasi)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}

          {!!holds?.results?.length && (
            <>
              <h2 className="mb-3 mt-6 text-lg font-semibold text-slate-900 dark:text-slate-100">Band qilingan so'rovlar ({holds.results.length})</h2>
              <Table>
                <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">O'quvchi</th>
                    <th className="px-4 py-3">Holati</th>
                    <th className="px-4 py-3">Sana</th>
                    <th className="px-4 py-3">Izoh</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {holds.results.map((h) => (
                    <tr key={h.id}>
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{h.oquvchi_fish}</td>
                      <td className="px-4 py-3">
                        <Badge tone="amber">{BAND_HOLATI_LABELS[h.holati as BandHolati] ?? humanize(h.holati)}</Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(h.so_rov_sanasi)}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{h.izoh || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
