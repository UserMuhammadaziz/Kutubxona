import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applicationsApi, finesApi, readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import type { OquvchiCreatePayload } from '../types'
import { Badge, Button, Card, EmptyState, ErrorBanner, Field, Input, Label, Modal, PageHeader, Pagination, Spinner, Table } from '../components/ui'
import { formatDate, formatMoney } from '../lib/format'

const emptyForm: OquvchiCreatePayload = { fish: '', telefon: '+998', tugilgan_sana: '', manzil: '' }

export function Readers() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<OquvchiCreatePayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [showArizalar, setShowArizalar] = useState(false)
  const [showJarimalar, setShowJarimalar] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['readers', page, search],
    queryFn: () => readersApi.list({ page, search: search || undefined }),
  })

  // Kutilayotgan a'zolik arizalari — o'quvchilar ro'yxati yonida qabul qilinadi
  const { data: arizalar } = useQuery({
    queryKey: ['applications', 'kutmoqda'],
    queryFn: () => applicationsApi.list({ holati: 'kutmoqda' }),
  })

  // Jarimasi bor o'quvchilar — arizalar yonida to'langan deb belgilanadi
  const { data: jarimalar } = useQuery({
    queryKey: ['fines', 'tolamagan'],
    queryFn: () => finesApi.list({ tolandimi: false }),
  })

  const payJarima = useMutation({
    mutationFn: (id: number) => finesApi.pay(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['fines'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  const approveAriza = useMutation({
    mutationFn: (id: number) => applicationsApi.approve(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      qc.invalidateQueries({ queryKey: ['readers'] })
    },
    onError: (err) => alert(errorMessage(err)),
  })

  const rejectAriza = useMutation({
    mutationFn: (id: number) => applicationsApi.reject(id, prompt('Rad etish sababi (ixtiyoriy):') ?? ''),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  const createMut = useMutation({
    mutationFn: (payload: OquvchiCreatePayload) => readersApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['readers'] })
      setModalOpen(false)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const toggleActiveMut = useMutation({
    mutationFn: ({ id, faol }: { id: number; faol: boolean }) => readersApi.update(id, { faol }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['readers'] }),
    onError: (err) => alert(errorMessage(err)),
  })

  function openCreate() {
    setForm(emptyForm)
    setError(null)
    setModalOpen(true)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    createMut.mutate(form)
  }

  return (
    <div>
      <PageHeader title="O'quvchilar" subtitle="Kutubxona a'zolari ro'yxati" actions={<Button onClick={openCreate}>+ Yangi o'quvchi</Button>} />

      <Card className="mb-4 p-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Button variant="secondary" onClick={() => setShowArizalar((v) => !v)}>
            📋 Arizalar {arizalar ? `(${arizalar.count})` : ''}
          </Button>
          <Button variant="secondary" onClick={() => setShowJarimalar((v) => !v)}>
            💰 Jarimalar {jarimalar ? `(${jarimalar.count})` : ''}
          </Button>
        </div>
        <Input placeholder="Ism, telefon yoki karta raqami bo'yicha qidirish..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </Card>

      {showArizalar && (
        <Card className="mb-6 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              📋 A'zolik arizalari
            </h2>
            <Button size="sm" variant="secondary" onClick={() => setShowArizalar(false)}>
              Yopish
            </Button>
          </div>

          {!arizalar?.results.length && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Yangi arizalar yo'q.</p>
          )}

        {!!arizalar?.results.length && (
          <ul className="divide-y divide-slate-100 dark:divide-slate-700">
            {arizalar.results.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-4 py-3">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-slate-900 dark:text-slate-100">{a.fish}</div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    {a.telefon} · Telegram: {a.telegram_id}
                  </div>
                  {a.tugilgan_sana && (
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                      Tug'ilgan sana: {formatDate(a.tugilgan_sana)}
                    </div>
                  )}
                  {a.manzil && (
                    <div className="text-sm text-slate-500 dark:text-slate-400">Manzil: {a.manzil}</div>
                  )}
                  <div className="text-xs text-slate-400">{formatDate(a.ariza_sanasi)}</div>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={rejectAriza.isPending}
                    onClick={() => {
                      if (confirm(`"${a.fish}" arizasini rad etmoqchimisiz?`)) rejectAriza.mutate(a.id)
                    }}
                  >
                    Rad etish
                  </Button>
                  <Button
                    size="sm"
                    disabled={approveAriza.isPending}
                    onClick={() => {
                      if (confirm(`"${a.fish}" arizasini qabul qilib, o'quvchi ro'yxatiga qo'shasizmi?`)) approveAriza.mutate(a.id)
                    }}
                  >
                    Qabul qilish
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
        </Card>
      )}

      {showJarimalar && (
        <Card className="mb-6 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              💰 Jarimasi bor o'quvchilar
            </h2>
            <Button size="sm" variant="secondary" onClick={() => setShowJarimalar(false)}>
              Yopish
            </Button>
          </div>

          {!jarimalar?.results.length && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Jarimasi bor o'quvchilar yo'q. 🎉</p>
          )}

          {!!jarimalar?.results.length && (
            <ul className="divide-y divide-slate-100 dark:divide-slate-700">
              {jarimalar.results.map((j) => (
                <li key={j.id} className="flex flex-wrap items-center gap-4 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-slate-900 dark:text-slate-100">{j.oquvchi_fish}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                      📖 {j.kitob_nomi} · {j.kechikkan_kunlar} kun kechikish
                    </div>
                  </div>
                  <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {formatMoney(j.summa)}
                  </div>
                  <Button
                    size="sm"
                    disabled={payJarima.isPending}
                    onClick={() => {
                      if (confirm(`"${j.oquvchi_fish}" jarimasini (${formatMoney(j.summa)}) to'langan deb belgilaysizmi?`)) payJarima.mutate(j.id)
                    }}
                  >
                    To'landi
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="O'quvchilar topilmadi" />}

      {!isLoading && !!data?.results.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">F.I.Sh.</th>
              <th className="px-4 py-3">Telefon</th>
              <th className="px-4 py-3">Karta raqami</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.results.map((r) => (
              <tr key={r.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3">
                  <Link to={`/readers/${r.id}`} className="font-medium text-brand-700 hover:underline dark:text-brand-400">
                    {r.fish}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{r.telefon}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{r.karta_raqami}</td>
                <td className="px-4 py-3">
                  <Badge tone={r.faol ? 'green' : 'red'}>{r.faol ? 'Faol' : 'Faol emas'}</Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button size="sm" variant="secondary" onClick={() => toggleActiveMut.mutate({ id: r.id, faol: !r.faol })}>
                    {r.faol ? 'Bloklash' : 'Faollashtirish'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Yangi o'quvchi qo'shish">
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label>To'liq ismi</Label>
            <Input required value={form.fish} onChange={(e) => setForm({ ...form, fish: e.target.value })} />
          </Field>
          <Field>
            <Label>Telefon raqami</Label>
            <Input required placeholder="+998901234567" value={form.telefon} onChange={(e) => setForm({ ...form, telefon: e.target.value })} />
          </Field>
          <Field>
            <Label>Tug'ilgan sana</Label>
            <Input type="date" value={form.tugilgan_sana} onChange={(e) => setForm({ ...form, tugilgan_sana: e.target.value })} />
          </Field>
          <Field>
            <Label>Manzil</Label>
            <Input value={form.manzil} onChange={(e) => setForm({ ...form, manzil: e.target.value })} />
          </Field>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
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
