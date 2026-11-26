import { useState, type FormEvent } from 'react'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { booksApi, copiesApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { NUSXA_HOLATI_LABELS, type Nusxa, type NusxaCreatePayload, type NusxaHolati } from '../types'
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
  TableSkeleton,
} from '../components/ui'
import { DatePicker, toISO } from '../components/DatePicker'
import { useToast } from '../components/Toast'
import DataTable, { type DataTableColumn } from '../components/DataTable'
import { usePageSize } from '../hooks/usePageSize'

const makeEmptyForm = (): NusxaCreatePayload => ({
  kitob: 0,
  inventar_raqami: '',
  javon: '',
  izoh: '',
  qabul_sana: toISO(new Date()),
  count: 1,
})

const TONE: Record<NusxaHolati, 'green' | 'blue' | 'amber' | 'red'> = {
  mavjud: 'green',
  berilgan: 'blue',
  band: 'amber',
  tamirda: 'amber',
  yoqolgan: 'red',
}

/** Mirrors `inventory_numbers` in apps/nusxa/serializers.py for the form hint. */
function inventoryPreview(start: string, count: number) {
  const match = /(\d+)$/.exec(start)
  if (!match) return 'inventar raqami raqam bilan tugashi kerak (masalan, INV-001)'
  const prefix = start.slice(0, match.index)
  const at = (i: number) => prefix + String(Number(match[1]) + i).padStart(match[1].length, '0')
  return count === 2 ? `${at(0)}, ${at(1)}` : `${at(0)} … ${at(count - 1)}`
}

export function Copies() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = usePageSize()
  const [holati, setHolati] = useState<NusxaHolati | ''>('')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<NusxaCreatePayload>(makeEmptyForm)
  const [error, setError] = useState<string | null>(null)
  const [ochiriladigan, setOchiriladigan] = useState<Nusxa | null>(null)

  const { data, isLoading, isError, error: listError, refetch, isFetching } = useQuery({
    queryKey: ['copies', page, pageSize, holati, debouncedSearch],
    queryFn: () => copiesApi.list({ page, page_size: pageSize, holati: holati || undefined, search: debouncedSearch || undefined }),
  })

  const [bookSearch, setBookSearch] = useState('')
  const debouncedBookSearch = useDebouncedValue(bookSearch)
  const { data: books, isLoading: booksLoading } = useQuery({
    queryKey: ['books', 'for-copy-select', debouncedBookSearch],
    queryFn: () => booksApi.list({ page: 1, page_size: 50, search: debouncedBookSearch || undefined }),
    enabled: modalOpen,
  })

  const { data: summary } = useQuery({
    queryKey: ['copies', 'summary', debouncedSearch],
    queryFn: () => copiesApi.summary({ search: debouncedSearch || undefined }),
  })

  const createMut = useMutation({
    mutationFn: (payload: NusxaCreatePayload) => copiesApi.create(payload),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
      toast.success(created.created_count > 1 ? `${created.created_count} ta nusxa qo‘shildi.` : 'Nusxa qo‘shildi.')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const statusMut = useMutation({
    mutationFn: ({ id, holati: yangiHolat }: { id: number; holati: NusxaHolati }) =>
      copiesApi.update(id, { holati: yangiHolat }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      toast.success('Nusxa holati yangilandi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const removeMut = useMutation({
    mutationFn: (id: number) => copiesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      setOchiriladigan(null)
      toast.success('Nusxa o‘chirildi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  function openCreate() {
    setForm(makeEmptyForm())
    setBookSearch('')
    setError(null)
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.kitob) {
      setError('Kitobni tanlang')
      return
    }
    if (!form.qabul_sana) {
      setError('Qabul qilingan sanani kiriting')
      return
    }
    setError(null)
    createMut.mutate(form)
  }

  const filtrBor = holati !== ''

  return (
    <div>
      <PageHeader
        title="Nusxalar"
        subtitle="Har bir kitobning jismoniy nusxalari"
        actions={
          <Button onClick={openCreate}>
            + Yangi nusxa
          </Button>
        }
      />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_16rem]">
          <Input
            placeholder="Inventar raqam, kitob yoki javon bo'yicha qidirish..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            aria-label="Qidirish"
          />
          <Select
            value={holati}
            onChange={(e) => {
              setHolati(e.target.value as NusxaHolati | '')
              setPage(1)
            }}
            aria-label="Nusxa holati"
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(NUSXA_HOLATI_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
        {summary && summary.total > 0 && (
          <div className="mt-3 flex flex-wrap gap-2" aria-label="Holatlar bo‘yicha nusxalar soni">
            <button
              type="button"
              onClick={() => { setHolati(''); setPage(1) }}
              className={'rounded-full px-3 py-1 text-sm ring-1 ' + (holati === '' ? 'bg-brand-700 text-white ring-brand-700' : 'bg-paper text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700')}
            >
              Jami: <span className="font-semibold tabular-nums">{summary.total}</span>
            </button>
            {(Object.keys(NUSXA_HOLATI_LABELS) as NusxaHolati[])
              .filter((key) => summary.by_status[key])
              .map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => { setHolati(key); setPage(1) }}
                  className={'rounded-full px-3 py-1 text-sm ring-1 ' + (holati === key ? 'bg-brand-700 text-white ring-brand-700' : 'bg-paper text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700')}
                >
                  {NUSXA_HOLATI_LABELS[key]}: <span className="font-semibold tabular-nums">{summary.by_status[key]}</span>
                </button>
              ))}
          </div>
        )}
      </Card>

      {isLoading && <TableSkeleton rows={6} cols={5} />}

      {isError && !isLoading && (
        <ErrorState
          title="Nusxalarni yuklab bo‘lmadi"
          message={errorMessage(listError)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon={<Icons.package className="h-10 w-10" />}
          title={filtrBor ? 'Nusxa topilmadi' : 'Hali nusxa yo‘q'}
          description={
            filtrBor
              ? 'Boshqa holat filtrini tanlab ko‘ring.'
              : 'Kitob qo‘shganingizdan keyin uning jismoniy nusxalarini shu yerda yarating.'
          }
          action={
            filtrBor ? (
              <Button variant="secondary" size="sm" onClick={() => setHolati('')}>
                Filtrni tozalash
              </Button>
            ) : (
              <Button size="sm" onClick={openCreate}>
                + Yangi nusxa
              </Button>
            )
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Nusxa>
          items={data.results}
          render={(c) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
                  {c.kitob_nomi}
                </div>
                <Badge tone={TONE[c.holati]}>{NUSXA_HOLATI_LABELS[c.holati]}</Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">
                № {c.inventar_raqami} · Javon: {c.javon || '—'}
              </div>
              <div className="flex flex-wrap gap-2">
                {(c.holati === 'mavjud' || c.holati === 'tamirda') && (
                  <Button
                    size="sm"
                    variant="secondary"
                    className="flex-1"
                    disabled={statusMut.isPending}
                    onClick={() =>
                      statusMut.mutate({
                        id: c.id,
                        holati: c.holati === 'mavjud' ? 'tamirda' : 'mavjud',
                      })
                    }
                  >
                    {c.holati === 'mavjud' ? "Ta'mirga berish" : 'Qaytarish'}
                  </Button>
                )}
                {c.holati === 'mavjud' && (
                  <>
                    <Button
                      size="sm"
                      variant="danger"
                      className="flex-1"
                      disabled={statusMut.isPending}
                      onClick={() => statusMut.mutate({ id: c.id, holati: 'yoqolgan' })}
                    >
                      Yo'qolgan
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => setOchiriladigan(c)}>
                      O'chirish
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        >
          <DataTable<Nusxa>
            data={data.results}
            getRowId={(c) => c.id}
            emptyText="Nusxa topilmadi"
            pagination={{
              count: data.count,
              page: page - 1,
              rowsPerPage: pageSize,
              onRowsPerPageChange: (n) => {
                setPageSize(n)
                setPage(1)
              },
              onPageChange: (p) => setPage(p + 1),
            }}
            columns={
              [
                {
                  id: 'kitob',
                  label: 'Kitob',
                  sortBy: (c) => c.kitob_nomi,
                  render: (c) => (
                    <div className="font-medium text-slate-900 dark:text-slate-100">
                      {c.kitob_nomi}
                    </div>
                  ),
                },
                {
                  id: 'inventar_raqami',
                  label: 'Inventar №',
                  sortBy: (c) => c.inventar_raqami,
                },
                {
                  id: 'javon',
                  label: 'Javon',
                  sortBy: (c) => c.javon,
                  render: (c) => c.javon || '—',
                },
                {
                  id: 'holati',
                  label: 'Holati',
                  sortBy: (c) => c.holati,
                  render: (c) => <Badge tone={TONE[c.holati]}>{NUSXA_HOLATI_LABELS[c.holati]}</Badge>,
                },
                {
                  id: 'amallar',
                  label: '',
                  sortable: false,
                  align: 'right',
                  render: (c) => (
                    <div className="flex justify-end gap-2">
                      {(c.holati === 'mavjud' || c.holati === 'tamirda') && (
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={statusMut.isPending}
                          onClick={() =>
                            statusMut.mutate({
                              id: c.id,
                              holati: c.holati === 'mavjud' ? 'tamirda' : 'mavjud',
                            })
                          }
                        >
                          {c.holati === 'mavjud' ? "Ta'mirga berish" : 'Qaytarish'}
                        </Button>
                      )}
                      {c.holati === 'mavjud' && (
                        <>
                          <Button
                            size="sm"
                            variant="danger"
                            disabled={statusMut.isPending}
                            onClick={() => statusMut.mutate({ id: c.id, holati: 'yoqolgan' })}
                          >
                            Yo'qolgan
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => setOchiriladigan(c)}>
                            O'chirish
                          </Button>
                        </>
                      )}
                    </div>
                  ),
                },
              ] as DataTableColumn<Nusxa>[]
            }
          />
        </ResponsiveList>
      )}

      {/* Mobilda jadvaldagi MUI pagination ko'rinmaydi */}
      {data && (
        <div className="md:hidden">
          <Pagination count={data.count} page={page} pageSize={pageSize} onChange={setPage} />
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title="Yangi nusxa qo'shish"
        description="Kitobni tanlang va inventar raqamini kiriting. Bir nechta nusxa bo‘lsa, sonini yozing."
      >
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="n-kitob-qidirish">Kitobni qidirish</Label>
            <Input
              id="n-kitob-qidirish"
              placeholder="Kitob nomi yoki muallif..."
              value={bookSearch}
              onChange={(e) => {
                setBookSearch(e.target.value)
                setForm((old) => ({ ...old, kitob: 0 }))
              }}
            />
          </Field>
          <Field>
            <Label htmlFor="n-kitob">Kitob</Label>
            {booksLoading ? (
              <Spinner label="Kitoblar yuklanmoqda..." className="py-2" />
            ) : (
              <Select
                id="n-kitob"
                value={form.kitob}
                onChange={(e) => setForm({ ...form, kitob: Number(e.target.value) })}
              >
                <option value={0}>Tanlang...</option>
                {books?.results.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.nomi} — {b.muallif}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field>
            <Label htmlFor="n-inventar">Inventar raqami</Label>
            <Input
              id="n-inventar"
              required
              value={form.inventar_raqami}
              onChange={(e) => setForm({ ...form, inventar_raqami: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="n-count">Nechta nusxa</Label>
            <Input
              id="n-count"
              type="number"
              inputMode="numeric"
              min={1}
              max={200}
              value={form.count ?? 1}
              onChange={(e) => setForm({ ...form, count: Math.max(1, Math.min(200, Number(e.target.value) || 1)) })}
            />
            {(form.count ?? 1) > 1 && (
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Inventar raqamlari ketma-ket beriladi: {inventoryPreview(form.inventar_raqami, form.count ?? 1)}
              </p>
            )}
          </Field>
          <Field>
            <Label htmlFor="n-qabul">Qabul qilingan sana</Label>
            <DatePicker
              id="n-qabul"
              allowClear={false}
              value={form.qabul_sana ?? ''}
              onChange={(v) => setForm({ ...form, qabul_sana: v })}
            />
          </Field>
          <Field>
            <Label htmlFor="n-javon">Javon</Label>
            <Input
              id="n-javon"
              placeholder="Masalan: A-3"
              value={form.javon}
              onChange={(e) => setForm({ ...form, javon: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="n-izoh">Izoh</Label>
            <Input
              id="n-izoh"
              value={form.izoh}
              onChange={(e) => setForm({ ...form, izoh: e.target.value })}
            />
          </Field>
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={closeModal} disabled={createMut.isPending}>
              Bekor qilish
            </Button>
            <Button type="submit" loading={createMut.isPending}>
              Saqlash
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!ochiriladigan}
        title="Nusxani o‘chirish"
        variant="danger"
        confirmLabel="O‘chirish"
        loading={removeMut.isPending}
        message={
          ochiriladigan && (
            <>
              <b>{ochiriladigan.kitob_nomi}</b> — № {ochiriladigan.inventar_raqami} nusxasini
              ro‘yxatdan o‘chiramoqchimisiz?
            </>
          )
        }
        onConfirm={() => ochiriladigan && removeMut.mutate(ochiriladigan.id)}
        onCancel={() => setOchiriladigan(null)}
      />
    </div>
  )
}
