import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { booksApi, reservationsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { formatDate } from '../lib/format'
import { JANR_LABELS, TIL_LABELS, HOLAT_LABELS, NAVBAT_HOLATI_LABELS, type Janr, type Kitob, type KitobHolati, type KitobPayload, type Navbat } from '../types'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorBanner,
  ErrorState,
  Field,
  Input,
  Label,
  Modal,
  PageHeader,
  Pagination,
  ResponsiveList,
  Select,
  Spinner,
  Table,
  TableSkeleton,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { useAuthStore } from '../store/auth'

const KITOB_HOLATI_TONE: Record<KitobHolati, 'slate' | 'green' | 'red' | 'amber' | 'blue'> = {
  mavjud: 'green',
  berilgan: 'blue',
  yoqolgan: 'red',
}

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
  const toast = useToast()
  const user = useAuthStore((s) => s.user)
  const canEdit = user?.rol === 'kutubxonachi' || user?.rol === 'administrator'
  const [page, setPage] = useState(1)
  const [janr, setJanr] = useState('')
  const [search, setSearch] = useState('')
  const kechikkanSearch = useDebouncedValue(search)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Kitob | null>(null)
  const [form, setForm] = useState<KitobPayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [ochiriladigan, setOchiriladigan] = useState<Kitob | null>(null)
  const [navbatBekorQilinadigan, setNavbatBekorQilinadigan] = useState<Navbat | null>(null)

  const searching = kechikkanSearch.trim().length > 0

  const listQuery = useQuery({
    queryKey: ['books', page, janr],
    queryFn: () => booksApi.list({ page, janr: janr || undefined }),
    enabled: !searching,
  })

  const searchQuery = useQuery({
    queryKey: ['books', 'search', kechikkanSearch],
    queryFn: () => booksApi.search(kechikkanSearch.trim()),
    enabled: searching,
  })

  const createMut = useMutation({
    mutationFn: (payload: KitobPayload) => booksApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
      toast.success('Kitob qo‘shildi.')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<KitobPayload> }) => booksApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
      toast.success('Kitob ma’lumotlari yangilandi.')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const removeMut = useMutation({
    mutationFn: (id: number) => booksApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['books'] })
      setOchiriladigan(null)
      toast.success('Kitob o‘chirildi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
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
      qc.invalidateQueries({ queryKey: ['book-queue'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      qc.invalidateQueries({ queryKey: ['reservations'] })
      setNavbatBekorQilinadigan(null)
      toast.success('Navbat bekor qilindi va keyingisiga navbat yuborildi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
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
  const listError = searching ? searchQuery.error : listQuery.error
  const isError = searching ? searchQuery.isError : listQuery.isError
  const isFetching = searching ? searchQuery.isFetching : listQuery.isFetching
  const filtrBor = searching || janr !== ''

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

      {loading && <TableSkeleton rows={8} cols={6} />}

      {isError && !loading && (
        <ErrorState
          title="Kitoblarni yuklab bo‘lmadi"
          message={errorMessage(listError)}
          onRetry={() => {
            if (searching) void searchQuery.refetch()
            else void listQuery.refetch()
          }}
          retrying={isFetching}
        />
      )}

      {!loading && !isError && !rows?.length && (
        <EmptyState
          icon="📚"
          title={filtrBor ? 'Kitob topilmadi' : 'Hali kitob yo‘q'}
          description={
            filtrBor
              ? 'Qidiruv shartini yoki janr filtrini o‘zgartirib ko‘ring.'
              : canEdit
                ? 'Birinchi kitobni qo‘shish uchun «+ Yangi kitob» tugmasidan foydalaning.'
                : 'Katalog hali to‘ldirilmagan.'
          }
          action={
            filtrBor ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSearch('')
                  setJanr('')
                  setPage(1)
                }}
              >
                Filtrni tozalash
              </Button>
            ) : canEdit ? (
              <Button size="sm" onClick={openCreate}>
                + Yangi kitob
              </Button>
            ) : undefined
          }
        />
      )}

      {!loading && !isError && !!rows?.length && (
        <ResponsiveList<Kitob>
          items={rows}
          render={(b) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <Link
                  to={`/books/${b.id}`}
                  className="font-medium text-brand-700 hover:underline dark:text-brand-400"
                >
                  {b.nomi}
                </Link>
<Badge tone={KITOB_HOLATI_TONE[b.holati as KitobHolati] ?? 'slate'}>
                  {HOLAT_LABELS[b.holati as KitobHolati] ?? b.holati}
                </Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">{b.muallif}</div>
              <div className="flex flex-wrap gap-1.5">
                <Badge>{JANR_LABELS[b.janr as Janr] ?? b.janr}</Badge>
                <Badge tone={b.mavjud_nusxalar > 0 ? 'green' : 'red'}>
                  {b.mavjud_nusxalar} / {b.jami_nusxalar} nusxa
                </Badge>
                {b.faol_navbatlar > 0 && <Badge tone="amber">{b.faol_navbatlar} ta navbat</Badge>}
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>{b.nashr_yili} · {b.nashriyot || '—'}</span>
                {b.narh && <span className="font-semibold">{Number(b.narh).toLocaleString('ru-RU')} so‘m</span>}
              </div>
              {canEdit && (
                <div className="mt-1 flex gap-2">
                  {b.faol_navbatlar > 0 && (
                    <Button size="sm" variant="secondary" className="flex-1" onClick={() => setQueueBook(b)}>
                      Navbat
                    </Button>
                  )}
                  <Button size="sm" variant="secondary" className="flex-1" onClick={() => openEdit(b)}>
                    Tahrirlash
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => setOchiriladigan(b)}>
                    O‘chirish
                  </Button>
                </div>
              )}
            </div>
          )}
        >
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
                  <Badge tone={KITOB_HOLATI_TONE[b.holati as KitobHolati] ?? 'slate'}>{HOLAT_LABELS[b.holati as KitobHolati] ?? b.holati}</Badge>
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
                        onClick={() => setOchiriladigan(b)}
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
        </ResponsiveList>
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
          <div className="grid gap-4 sm:grid-cols-2">
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
          <div className="grid gap-4 sm:grid-cols-2">
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
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <Label>Holati</Label>
<Select value={form.holati} onChange={(e) => setForm({ ...form, holati: e.target.value as KitobHolati })}>
                {Object.entries(HOLAT_LABELS)
                  .filter(([value]) => value !== 'berilgan')
                  .map(([value, label]) => (
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
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
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
        {queueQuery.isLoading && <Spinner label="Navbatlar yuklanmoqda..." />}
        {queueQuery.isError && (
          <ErrorState
            title="Navbatlarni yuklab bo‘lmadi"
            message={errorMessage(queueQuery.error)}
            onRetry={() => void queueQuery.refetch()}
            retrying={queueQuery.isFetching}
          />
        )}
        {!queueQuery.isLoading && !queueQuery.isError && !queueQuery.data?.length && (
          <EmptyState
            icon="📋"
            title="Bu kitobga hozircha navbat yo'q"
            description="Kitob qaytarilganda navbatdagi o‘quvchiga avtomatik taklif yuboriladi."
          />
        )}
        {!queueQuery.isLoading && !queueQuery.isError && !!queueQuery.data?.length && (
          <ResponsiveList<Navbat>
            items={queueQuery.data}
            render={(r) => (
              <div className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-medium text-slate-900 dark:text-slate-100">
                    {r.oquvchi_fish}
                  </div>
                  <Badge tone={r.holati === 'kutmoqda' ? 'amber' : 'blue'}>
                    {NAVBAT_HOLATI_LABELS[r.holati]}
                  </Badge>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Navbat sanasi: {formatDate(r.navbat_sanasi)}
                </div>
                <Button
                  size="sm"
                  variant="danger"
                  className="w-full"
                  onClick={() => setNavbatBekorQilinadigan(r)}
                >
                  Bekor qilish
                </Button>
              </div>
            )}
          >
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
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                      {r.oquvchi_fish}
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                      {formatDate(r.navbat_sanasi)}
                    </td>
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
                        onClick={() => setNavbatBekorQilinadigan(r)}
                      >
                        Bekor qilish
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </ResponsiveList>
        )}
      </Modal>

      <ConfirmDialog
        open={!!ochiriladigan}
        title="Kitobni o‘chirish"
        variant="danger"
        confirmLabel="O‘chirish"
        loading={removeMut.isPending}
        message={
          ochiriladigan && (
            <>
              <b>{ochiriladigan.nomi}</b> kitobini ro‘yxatdan o‘chiramoqchimisiz?
              {ochiriladigan.faol_navbatlar > 0 && (
                <>
                  <br />
                  <br />
                  Bu kitobga <b>{ochiriladigan.faol_navbatlar} ta faol navbat</b> bor — ular ham
                  bekor qilinadi.
                </>
              )}
            </>
          )
        }
        onConfirm={() => ochiriladigan && removeMut.mutate(ochiriladigan.id)}
        onCancel={() => setOchiriladigan(null)}
      />

      <ConfirmDialog
        open={!!navbatBekorQilinadigan}
        title="Navbatni bekor qilish"
        variant="danger"
        confirmLabel="Bekor qilish"
        loading={cancelNavbatMut.isPending}
        message={
          navbatBekorQilinadigan && (
            <>
              <b>{navbatBekorQilinadigan.oquvchi_fish}</b> navbatini bekor qilmoqchimisiz? Keyingi
              navbatdagi o‘quvchiga taklif yuboriladi.
            </>
          )
        }
        onConfirm={() =>
          navbatBekorQilinadigan && cancelNavbatMut.mutate(navbatBekorQilinadigan.id)
        }
        onCancel={() => setNavbatBekorQilinadigan(null)}
      />
    </div>
  )
}
