import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { copiesApi, loansApi, readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { BERISH_HOLATI_LABELS, type BerishCreatePayload, type BerishHolati } from '../types'
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
import { formatDate, formatMoney } from '../lib/format'

export function Loans() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [readerSearch, setReaderSearch] = useState('')
  const [form, setForm] = useState<BerishCreatePayload>({ nusxa: 0, oquvchi: 0 })
  const [error, setError] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['loans', page, holati],
    queryFn: () => loansApi.list({ page, holati: holati || undefined }),
  })

  const { data: readers } = useQuery({
    queryKey: ['readers', 'for-select', readerSearch],
    queryFn: () => readersApi.list({ search: readerSearch || undefined }),
    enabled: modalOpen,
  })

  const { data: availableCopies } = useQuery({
    queryKey: ['copies', 'available-for-select'],
    queryFn: () => copiesApi.list({ holati: 'mavjud' }),
    enabled: modalOpen,
  })

  const createMut = useMutation({
    mutationFn: (payload: BerishCreatePayload) => loansApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      setModalOpen(false)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const returnMut = useMutation({
    mutationFn: (id: number) => loansApi.return(id),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      if (res.jarima_summasi) alert(`Kitob qaytarildi. Jarima: ${formatMoney(res.jarima_summasi)}`)
    },
    onError: (err) => alert(errorMessage(err)),
  })

  function openCreate() {
    setForm({ nusxa: 0, oquvchi: 0 })
    setError(null)
    setModalOpen(true)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.nusxa || !form.oquvchi) {
      setError("Nusxa va o'quvchini tanlang")
      return
    }
    createMut.mutate(form)
  }

  return (
    <div>
      <PageHeader title="Berish / Qaytarish" subtitle="Kitob berish va qaytarish jarayonlari" actions={<Button onClick={openCreate}>+ Kitob berish</Button>} />

      <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
        <div className="w-56">
          <Select value={holati} onChange={(e) => setHolati(e.target.value)}>
            <option value="">Barcha holatlar</option>
            {Object.entries(BERISH_HOLATI_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="Berishlar topilmadi" />}

      {!isLoading && !!data?.results.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">Kitob</th>
              <th className="px-4 py-3">O'quvchi</th>
              <th className="px-4 py-3">Berilgan</th>
              <th className="px-4 py-3">Muddat</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.results.map((l) => (
              <tr key={l.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900 dark:text-slate-100">{l.kitob_nomi}</div>
                  <div className="text-xs text-slate-400 dark:text-slate-500">{l.inventar_raqami}</div>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{l.oquvchi_fish}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(l.berilgan_sana)}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatDate(l.qaytarish_muddati)}</td>
                <td className="px-4 py-3">
                  <Badge tone={l.holati === 'faol' ? 'blue' : l.holati === 'qaytarilgan' ? 'green' : 'red'}>
                    {BERISH_HOLATI_LABELS[l.holati as BerishHolati]}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {l.holati === 'faol' && (
                    <Button size="sm" onClick={() => returnMut.mutate(l.id)} disabled={returnMut.isPending}>
                      Qaytarish
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Kitob berish">
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label>O'quvchini qidirish</Label>
            <Input placeholder="Ism yoki telefon..." value={readerSearch} onChange={(e) => setReaderSearch(e.target.value)} />
          </Field>
          <Field>
            <Label>O'quvchi</Label>
            <Select value={form.oquvchi} onChange={(e) => setForm({ ...form, oquvchi: Number(e.target.value) })}>
              <option value={0}>Tanlang...</option>
              {readers?.results.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.fish} — {r.telefon}
                </option>
              ))}
            </Select>
          </Field>
          <Field>
            <Label>Mavjud nusxa</Label>
            <Select value={form.nusxa} onChange={(e) => setForm({ ...form, nusxa: Number(e.target.value) })}>
              <option value={0}>Tanlang...</option>
              {availableCopies?.results.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.kitob_nomi} — {c.inventar_raqami}
                </option>
              ))}
            </Select>
          </Field>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Bekor qilish
            </Button>
            <Button type="submit" disabled={createMut.isPending}>
              Berish
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
