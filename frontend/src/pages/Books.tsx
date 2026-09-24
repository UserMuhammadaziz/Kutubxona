import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { booksApi, reservationsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { formatDate } from '../lib/format'
import { JANR_LABELS, TIL_LABELS, HOLAT_LABELS, NAVBAT_HOLATI_LABELS, type Janr, type Kitob, type KitobHolati, type KitobPayload, type Navbat } from '../types'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorBanner,
  Field,
  Input,
  Label,
  Modal,
  PageHeader,
  Pagination,
  Select,
  Spinner,
  Table,
} from '../components/ui'
import { useAuthStore } from '../store/auth'

const emptyForm: KitobPayload = {
  nomi: '',
  muallif: '',
  isbn: '',
  janr: 'badiiy',
  til: '',
  narh: '',
  buyurtma_soni: '',
  nashr_yili: new Date().getFullYear(),
  nashriyot: '',
  tavsif: '',
  holati: 'mavjud',
}

export function Books() {
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const canEdit = user?.rol === 'kutubxonachi' || user?.rol === 'administrator'
  const [page, setPage] = useState(1)
  const [janr, setJanr] = useState('')
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Kitob | null>(null)
  const [form, setForm] = useState<KitobPayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)

  const searching = search.trim().length > 0

  const listQuery = useQuery({
    queryKey: ['books', page, janr],
    queryFn: () => booksApi.list({ page, janr: janr || undefined }),
    enabled: !searching,
  })

  const searchQuery = useQuery({
    queryKey: ['books', 'search', search],
    queryFn: () => booksApi.search(search.trim()),
    enabled: searching,
  })

  const createMut = useMutation({
    mutationFn: (payload: KitobPayload) => booksApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<KitobPayload> }) => booksApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const removeMut = useMutation({
    mutationFn: (id: number) => booksApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['books'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  const [queueBook, setQueueBook] = useState<Kitob | null>(null)

  const queueOpen = queueBook !== null
  const queueQuery = useQuery({
    queryKey: ['book-queue', queueBook?.id],
    queryFn: () => booksApi.queue(queueBook!.id),
    enabled: queueOpen,
  })

  const cancelNavbatMut = useMutation({
    mutationFn: (id: number) => reservationsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['book-queue', queueBook?.id] })
      qc.invalidateQueries({ queryKey: ['books'] })
      qc.invalidateQueries({ queryKey: ['reservations'] })
    },
    onError: (err) => alert(errorMessage(err)),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setError(null)
    setModalOpen(true)
  }

  function openEdit(book: Kitob) {
    booksApi.get(book.id).then((detail) => {
      setEditing(book)
      setForm({
        nomi: detail.nomi,
        muallif: detail.muallif,
        isbn: detail.isbn ?? '',
        janr: detail.janr,
        til: detail.til ?? '',
        narh: detail.narh ?? '',
        buyurtma_soni: String(detail.buyurtma_soni ?? ''),
        nashr_yili: detail.nashr_yili,
        nashriyot: detail.nashriyot ?? '',
        tavsif: detail.tavsif ?? '',
        holati: detail.holati ?? 'mavjud',
      })
      setError(null)
      setModalOpen(true)
    })
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    const payload: KitobPayload = { ...form }
    if (payload.isbn?.trim() === '') payload.isbn = undefined
    if (payload.til === '') payload.til = undefined
    if (payload.narh === '') payload.narh = undefined
    if (payload.buyurtma_soni === '') payload.buyurtma_soni = undefined
    if (editing) updateMut.mutate({ id: editing.id, payload })
    else createMut.mutate(payload)
  }

  const rows = searching ? searchQuery.data : listQuery.data?.results
  const loading = searching ? searchQuery.isLoading : listQuery.isLoading

  return (
    <div>
      <PageHeader
        title="Kitoblar"
        subtitle="Kutubxona katalogidagi barcha kitoblar"
        actions={canEdit ? <Button onClick={openCreate}>+ Yangi kitob</Button> : undefined}
      />

      <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
        <div className="min-w-[220px] flex-1">
          <Input placeholder="Nomi, muallif yoki ISBN bo'yicha qidirish..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="w-48">
          <Select value={janr} onChange={(e) => { setJanr(e.target.value); setPage(1) }} disabled={searching}>
            <option value="">Barcha janrlar</option>
            {Object.entries(JANR_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {loading && <Spinner />}
      {!loading && !rows?.length && <EmptyState text="Kitoblar topilmadi" />}

      {!loading && !!rows?.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Nomi</th>
              <th className="px-4 py-3">Muallif</th>
              <th className="px-4 py-3">Janr</th>
              <th className="px-4 py-3">Til</th>
              <th className="px-4 py-3">Nashriyot</th>
              <th className="px-4 py-3">Yil</th>
              <th className="px-4 py-3">Narhi</th>
              <th className="px-4 py-3">Buyurtma</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3">Nusxalar</th>
              <th className="px-4 py-3">Band</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {rows.map((b) => (
              <tr key={b.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3">
                  <Link to={`/books/${b.id}`} className="font-medium text-brand-700 hover:underline dark:text-brand-400">
                    {b.nomi}
                  </Link>
                  <div className="text-xs text-slate-400 dark:text-slate-500">{b.isbn}</div>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{b.muallif}</td>
                <td className="px-4 py-3">
                  <Badge>{JANR_LABELS[b.janr as Janr] ?? b.janr}</Badge>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{(TIL_LABELS[b.til] ?? b.til) || '—'}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{b.nashriyot || '—'}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{b.nashr_yili}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                  {b.narh ? Number(b.narh).toLocaleString('ru-RU') : '—'}
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{b.buyurtma_soni ?? '—'}</td>
                <td className="px-4 py-3">
                  <Badge tone={b.holati === 'mavjud' ? 'green' : 'red'}>{HOLAT_LABELS[b.holati as KitobHolati] ?? b.holati}</Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={b.mavjud_nusxalar > 0 ? 'green' : 'red'}>
                    {b.mavjud_nusxalar} / {b.jami_nusxalar}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={b.faol_navbatlar > 0 ? 'amber' : 'slate'}>
                    {b.faol_navbatlar > 0 ? `${b.faol_navbatlar} ta` : '—'}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {canEdit && b.faol_navbatlar > 0 && (
                    <Button size="sm" variant="secondary" onClick={() => setQueueBook(b)}>
                      Navbat
                    </Button>
                  )}
                  {canEdit && (
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="secondary" onClick={() => openEdit(b)}>
                        Tahrirlash
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => {
                          if (confirm(`"${b.nomi}" kitobini o'chirmoqchimisiz?`)) removeMut.mutate(b.id)
                        }}
                      >
                        O'chirish
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {!searching && listQuery.data && (
        <Pagination count={listQuery.data.count} page={page} onChange={setPage} />
      )}

      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Kitobni tahrirlash' : 'Yangi kitob qo‘shish'}>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label>Nomi</Label>
            <Input required value={form.nomi} onChange={(e) => setForm({ ...form, nomi: e.target.value })} />
          </Field>
          <Field>
            <Label>Muallif</Label>
            <Input required value={form.muallif} onChange={(e) => setForm({ ...form, muallif: e.target.value })} />
          </Field>
          <Field>
            <Label>ISBN (ixtiyoriy)</Label>
            <Input value={form.isbn} placeholder="Mavjud bo'lmasa bo'sh qoldiring" onChange={(e) => setForm({ ...form, isbn: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field>
              <Label>Janr</Label>
              <Select value={form.janr} onChange={(e) => setForm({ ...form, janr: e.target.value as Janr })}>
                {Object.entries(JANR_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field>
              <Label>Nashr yili</Label>
              <Input
                type="number"
                required
                value={form.nashr_yili}
                onChange={(e) => setForm({ ...form, nashr_yili: Number(e.target.value) })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field>
              <Label>Til</Label>
              <Select value={form.til} onChange={(e) => setForm({ ...form, til: e.target.value })}>
                <option value="">Tanlang...</option>
                {Object.entries(TIL_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field>
              <Label>Narhi (so'm)</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="Masalan: 15000"
                value={form.narh}
                onChange={(e) => setForm({ ...form, narh: e.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field>
              <Label>Holati</Label>
              <Select value={form.holati} onChange={(e) => setForm({ ...form, holati: e.target.value as KitobHolati })}>
                {Object.entries(HOLAT_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field>
              <Label>Buyurtma soni</Label>
              <Input
                type="number"
                min="0"
                placeholder="Masalan: 5"
                value={form.buyurtma_soni}
                onChange={(e) => setForm({ ...form, buyurtma_soni: e.target.value })}
              />
            </Field>
          </div>
          <Field>
            <Label>Nashriyot</Label>
            <Input value={form.nashriyot} onChange={(e) => setForm({ ...form, nashriyot: e.target.value })} />
          </Field>
          <Field>
            <Label>Tavsif</Label>
            <textarea
              className="w-full rounded-lg border border-slate-300 bg-paper px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder:text-slate-400 dark:focus:border-brand-400 dark:focus:ring-brand-900"
              rows={3}
              value={form.tavsif}
              onChange={(e) => setForm({ ...form, tavsif: e.target.value })}
            />
          </Field>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={closeModal}>
              Bekor qilish
            </Button>
            <Button type="submit" disabled={createMut.isPending || updateMut.isPending}>
              Saqlash
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={queueOpen}
        onClose={() => setQueueBook(null)}
        title={queueBook ? `Navbat — ${queueBook.nomi}` : 'Navbat'}
      >
        {queueQuery.isLoading && <Spinner />}
        {!queueQuery.isLoading && !queueQuery.data?.length && (
          <EmptyState text="Bu kitobga hozircha navbat yo'q" />
        )}
        {!queueQuery.isLoading && !!queueQuery.data?.length && (
          <Table>
            <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">O'quvchi</th>
                <th className="px-4 py-3">Navbat sanasi</th>
                <th className="px-4 py-3">Holati</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {queueQuery.data.map((r: Navbat) => (
                <tr key={r.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{r.oquvchi_fish}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(r.navbat_sanasi)}</td>
                  <td className="px-4 py-3">
                    <Badge tone={r.holati === 'kutmoqda' ? 'amber' : 'blue'}>
                      {NAVBAT_HOLATI_LABELS[r.holati]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="danger"
                      disabled={cancelNavbatMut.isPending}
                      onClick={() => {
                        if (confirm(`${r.oquvchi_fish} navbatini bekor qilmoqchimisiz?`)) {
                          cancelNavbatMut.mutate(r.id)
                        }
                      }}
                    >
                      Bekor qilish
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Modal>
    </div>
  )
}
