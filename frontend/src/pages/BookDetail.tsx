import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { booksApi } from '../api/resources'
import { Badge, Button, Card, PageHeader, Spinner, Table } from '../components/ui'
import { JANR_LABELS, NAVBAT_HOLATI_LABELS, NUSXA_HOLATI_LABELS, TIL_LABELS, HOLAT_LABELS, type Janr, type NavbatHolati, type NusxaHolati } from '../types'
import { formatDate, formatMoney } from '../lib/format'

export function BookDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const bookId = Number(id)

  const { data: book, isLoading } = useQuery({ queryKey: ['books', bookId], queryFn: () => booksApi.get(bookId) })
  const { data: queue } = useQuery({ queryKey: ['books', bookId, 'queue'], queryFn: () => booksApi.queue(bookId) })

  if (isLoading || !book) return <Spinner />

  return (
    <div>
      <button onClick={() => navigate(-1)} className="mb-4 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
        ← Orqaga
      </button>
      <PageHeader title={book.nomi} subtitle={`${book.muallif} · ${book.nashr_yili}`} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-1">
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-slate-500 dark:text-slate-400">ISBN</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{book.isbn || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Janr</dt>
              <dd>
                <Badge>{JANR_LABELS[book.janr as Janr] ?? book.janr}</Badge>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Til</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{book.til ? (TIL_LABELS[book.til] ?? book.til) : '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Holati</dt>
              <dd>
                <Badge tone={book.holati === 'mavjud' ? 'green' : 'red'}>{HOLAT_LABELS[book.holati] ?? book.holati}</Badge>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Narhi</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{formatMoney(book.narh)}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Buyurtma soni</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{book.buyurtma_soni ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Nashriyot</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{book.nashriyot || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Qo'shilgan sana</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">{formatDate(book.qoshilgan_sana)}</dd>
            </div>
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
                    <Badge tone={n.holati === 'mavjud' ? 'green' : n.holati === 'berilgan' ? 'blue' : 'amber'}>
                      {NUSXA_HOLATI_LABELS[n.holati as NusxaHolati] ?? n.holati}
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
                        <Badge tone="amber">{NAVBAT_HOLATI_LABELS[q.holati as NavbatHolati] ?? q.holati}</Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(q.navbat_sanasi)}</td>
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
