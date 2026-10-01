import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { booksApi, copiesApi } from '../api/resources'
import { errorMessage } from '../api/client'
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
  Table,
  TableSkeleton,
} from '../components/ui'
import { useToast } from '../components/Toast'

const emptyForm: NusxaCreatePayload = { kitob: 0, inventar_raqami: '', javon: '', izoh: '' }

const TONE: Record<NusxaHolati, 'green' | 'blue' | 'amber' | 'red'> = {
  mavjud: 'green',
  berilgan: 'blue',
  band: 'amber',
  tamirda: 'amber',
  yoqolgan: 'red',
}

export function Copies() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<NusxaHolati | ''>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<NusxaCreatePayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [ochiriladigan, setOchiriladigan] = useState<Nusxa | null>(null)

  const { data, isLoading, isError, error: listError, refetch, isFetching } = useQuery({
    queryKey: ['copies', page, holati],
    queryFn: () => copiesApi.list({ page, holati: holati || undefined }),
  })

  const { data: books, isLoading: booksLoading } = useQuery({
    queryKey: ['books', 'all-for-select'],
    queryFn: () => booksApi.list({ page: 1 }),
  })

  const createMut = useMutation({
    mutationFn: (payload: NusxaCreatePayload) => copiesApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
      toast.success('Nusxa qo‘shildi.')
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
    setForm(emptyForm)
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
          <Button onClick={openCreate} className="w-full sm:w-auto">
            + Yangi nusxa
          </Button>
        }
      />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="sm:w-64">
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
          icon="📦"
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
          <Table>
            <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Kitob</th>
                <th className="px-4 py-3">Inventar №</th>
                <th className="px-4 py-3">Javon</th>
                <th className="px-4 py-3">Holati</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {data.results.map((c) => (
                <tr key={c.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                    {c.kitob_nomi}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{c.inventar_raqami}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{c.javon || '—'}</td>
                  <td className="px-4 py-3">
                    <Badge tone={TONE[c.holati]}>{NUSXA_HOLATI_LABELS[c.holati]}</Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
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
                            Yo'qolgan deb belgilash
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => setOchiriladigan(c)}>
                            O'chirish
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </ResponsiveList>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title="Yangi nusxa qo'shish"
        description="Kitobni tanlang va inventar raqamini kiriting."
      >
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
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
