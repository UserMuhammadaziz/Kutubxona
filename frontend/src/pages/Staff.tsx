import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { staffApi } from '../api/resources'
import { errorMessage } from '../api/client'
import type { Rol, UserCreatePayload } from '../types'
import { Badge, Button, EmptyState, ErrorBanner, Field, Input, Label, Modal, PageHeader, Select, Spinner, Table } from '../components/ui'

const emptyForm: UserCreatePayload = { username: '', full_name: '', rol: 'kutubxonachi', telefon: '', password: '' }

export function Staff() {
  const qc = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<UserCreatePayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)

  const { data, isLoading } = useQuery({ queryKey: ['staff'], queryFn: () => staffApi.list() })

  const createMut = useMutation({
    mutationFn: (payload: UserCreatePayload) => staffApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff'] })
      setModalOpen(false)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const toggleActiveMut = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => staffApi.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['staff'] }),
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
      <PageHeader title="Xodimlar" subtitle="Kutubxonachi va administrator hisoblari" actions={<Button onClick={openCreate}>+ Yangi xodim</Button>} />

      {isLoading && <Spinner />}
      {!isLoading && !data?.results.length && <EmptyState text="Xodimlar topilmadi" />}

      {!isLoading && !!data?.results.length && (
        <Table>
          <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">F.I.Sh.</th>
              <th className="px-4 py-3">Foydalanuvchi nomi</th>
              <th className="px-4 py-3">Lavozim</th>
              <th className="px-4 py-3">Telefon</th>
              <th className="px-4 py-3">Holati</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {data.results.map((u) => (
              <tr key={u.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{u.full_name}</td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{u.username}</td>
                <td className="px-4 py-3">
                  <Badge tone={u.rol === 'administrator' ? 'blue' : 'slate'}>{u.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}</Badge>
                </td>
                <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{u.telefon}</td>
                <td className="px-4 py-3">
                  <Badge tone={u.is_active ? 'green' : 'red'}>{u.is_active ? 'Faol' : 'Faol emas'}</Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button size="sm" variant="secondary" onClick={() => toggleActiveMut.mutate({ id: u.id, is_active: !u.is_active })}>
                    {u.is_active ? 'Bloklash' : 'Faollashtirish'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Yangi xodim qo'shish">
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label>To'liq ismi</Label>
            <Input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </Field>
          <Field>
            <Label>Foydalanuvchi nomi</Label>
            <Input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          </Field>
          <Field>
            <Label>Parol</Label>
            <Input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
          <Field>
            <Label>Lavozim</Label>
            <Select value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}>
              <option value="kutubxonachi">Kutubxonachi</option>
              <option value="administrator">Administrator</option>
            </Select>
          </Field>
          <Field>
            <Label>Telefon</Label>
            <Input value={form.telefon} onChange={(e) => setForm({ ...form, telefon: e.target.value })} />
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
