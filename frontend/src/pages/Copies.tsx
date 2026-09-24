import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { booksApi, copiesApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { NUSXA_HOLATI_LABELS, type NusxaCreatePayload, type NusxaHolati } from '../types'
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

const emptyForm: NusxaCreatePayload = { kitob: 0, inventar_raqami: '', javon: '', izoh: '' }

export function Copies() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<NusxaCreatePayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['copies', page, holati],
    queryFn: () => copiesApi.list({ page, holati: (holati || undefined) as NusxaHolati | undefined }),
  })

  const { data: books } = useQuery({ queryKey: ['books', 'all-for-select'], queryFn: () => booksApi.list({ page: 1 }) })

  const createMut = useMutation({
    mutationFn: (payload: NusxaCreatePayload) => copiesApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
      closeModal()
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const statusMut = useMutation({
    mutationFn: ({ id, holati }: { id: number; holati: NusxaHolati }) => copiesApi.update(id, { holati }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['copies'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  const removeMut = useMutation({
    mutationFn: (id: number) => copiesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['books'] })
    },
    onError: (err) => alert(errorMessage(err)),
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
    createMut.mutate(form)
  }

  return (
    <div>
      <PageHeader title="Nusxalar" subtitle="Har bir kitobning jismoniy nusxalari" actions={<Button onClick={openCreate}>+ Yangi nusxa</Button>} />

      <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
        <div className="w-56">
          <Select value={holati} onChange={(e) => setHolati(e.target.value)}>
            <option value="">Barcha holatlar</option>
            {Object.entries(NUSXA_HOLATI_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="Nusxalar topilmadi" />}

      {!isLoading && !!data?.results.length && (
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
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{c.kitob_nomi}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{c.inventar_raqami}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{c.javon || '—'}</td>
                <td className="px-4 py-3">
                  <Badge tone={c.holati === 'mavjud' ? 'green' : c.holati === 'berilgan' ? 'blue' : 'amber'}>
                    {NUSXA_HOLATI_LABELS[c.holati]}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    {(c.holati === 'mavjud' || c.holati === 'tamirda') && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => statusMut.mutate({ id: c.id, holati: c.holati === 'mavjud' ? 'tamirda' : 'mavjud' })}
                      >
                        {c.holati === 'mavjud' ? "Ta'mirga berish" : 'Qaytarish'}
                      </Button>
                    )}
                    {c.holati === 'mavjud' && (
                      <Button size="sm" variant="danger" onClick={() => statusMut.mutate({ id: c.id, holati: 'yoqolgan' })}>
                        Yo'qolgan deb belgilash
                      </Button>
                    )}
                    {c.holati === 'mavjud' && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => {
                          if (confirm(`${c.inventar_raqami} nusxasini o'chirmoqchimisiz?`)) removeMut.mutate(c.id)
                        }}
                      >
                        O'chirish
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <Modal open={modalOpen} onClose={closeModal} title="Yangi nusxa qo'shish">
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label>Kitob</Label>
            <Select value={form.kitob} onChange={(e) => setForm({ ...form, kitob: Number(e.target.value) })}>
              <option value={0}>Tanlang...</option>
              {books?.results.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.nomi} — {b.muallif}
                </option>
              ))}
            </Select>
          </Field>
          <Field>
            <Label>Inventar raqami</Label>
            <Input required value={form.inventar_raqami} onChange={(e) => setForm({ ...form, inventar_raqami: e.target.value })} />
          </Field>
          <Field>
            <Label>Javon</Label>
            <Input value={form.javon} onChange={(e) => setForm({ ...form, javon: e.target.value })} />
          </Field>
          <Field>
            <Label>Izoh</Label>
            <Input value={form.izoh} onChange={(e) => setForm({ ...form, izoh: e.target.value })} />
          </Field>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={closeModal}>
              Bekor qilish
            </Button>
            <Button type="submit" disabled={createMut.isPending}>
              Saqlash
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
