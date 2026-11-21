import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { staffApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import type { Rol, User, UserCreatePayload } from '../types'
import {
  Badge,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorBanner,
  ErrorState,
  Field,
  Input,
  Label,
  Modal,
  PageHeader,
  ResponsiveList,
  Select,
  TableSkeleton,
} from '../components/ui'
import { useToast } from '../components/Toast'
import DataTable, { type DataTableColumn } from '../components/DataTable'

const emptyForm: UserCreatePayload = {
  username: '',
  full_name: '',
  rol: 'kutubxonachi',
  telefon: '',
  password: '',
}

export function Staff() {
  const qc = useQueryClient()
  const toast = useToast()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<UserCreatePayload>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [holatiOzgartiriladigan, setHolatiOzgartiriladigan] = useState<User | null>(null)

  const { data, isLoading, isError, error: listError, refetch, isFetching } = useQuery({
    queryKey: ['staff'],
    queryFn: () => staffApi.list(),
  })

  const createMut = useMutation({
    mutationFn: (payload: UserCreatePayload) => staffApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['staff'] })
      setModalOpen(false)
      toast.success('Xodim hisobi yaratildi.')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const toggleActiveMut = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      staffApi.update(id, { is_active }),
    onSuccess: (u) => {
      qc.invalidateQueries({ queryKey: ['staff'] })
      setHolatiOzgartiriladigan(null)
      toast.success(u.is_active ? `${u.full_name} faollashtirildi.` : `${u.full_name} bloklandi.`)
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  function openCreate() {
    setForm(emptyForm)
    setError(null)
    setModalOpen(true)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    createMut.mutate(form)
  }

  return (
    <div>
      <PageHeader
        title="Xodimlar"
        subtitle="Kutubxonachi va administrator hisoblari"
        actions={
          <Button onClick={openCreate} className="w-full sm:w-auto">
            + Yangi xodim
          </Button>
        }
      />

      {isLoading && <TableSkeleton rows={5} cols={6} />}

      {isError && !isLoading && (
        <ErrorState
          title="Xodimlarni yuklab bo‘lmadi"
          message={errorMessage(listError)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon={<Icons.users className="h-10 w-10" />}
          title="Xodim topilmadi"
          description="Kutubxonachi yoki administrator hisobini yarating."
          action={
            <Button size="sm" onClick={openCreate}>
              + Yangi xodim
            </Button>
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<User>
          items={data.results}
          render={(u) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
                  {u.full_name}
                </div>
                <Badge tone={u.is_active ? 'green' : 'red'}>{u.is_active ? 'Faol' : 'Bloklangan'}</Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">@{u.username}</div>
              <div className="flex flex-wrap gap-1.5">
                <Badge tone={u.rol === 'administrator' ? 'blue' : 'slate'}>
                  {u.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}
                </Badge>
                {u.telefon && <span className="text-xs text-slate-500 dark:text-slate-400">{u.telefon}</span>}
              </div>
              <Button
                size="sm"
                variant="secondary"
                className="w-full"
                onClick={() => setHolatiOzgartiriladigan(u)}
              >
                {u.is_active ? 'Bloklash' : 'Faollashtirish'}
              </Button>
            </div>
          )}
        >
          <DataTable<User>
            data={data.results}
            getRowId={(u) => u.id}
            emptyText="Xodim topilmadi"
            columns={
              [
                {
                  id: 'full_name',
                  label: 'F.I.Sh.',
                  sortBy: (u) => u.full_name,
                  render: (u) => (
                    <span className="font-medium text-slate-900 dark:text-slate-100">{u.full_name}</span>
                  ),
                },
                { id: 'username', label: 'Foydalanuvchi nomi', sortBy: (u) => u.username },
                {
                  id: 'rol',
                  label: 'Lavozim',
                  sortBy: (u) => u.rol,
                  render: (u) => (
                    <Badge tone={u.rol === 'administrator' ? 'blue' : 'slate'}>
                      {u.rol === 'administrator' ? 'Administrator' : 'Kutubxonachi'}
                    </Badge>
                  ),
                },
                {
                  id: 'telefon',
                  label: 'Telefon',
                  sortBy: (u) => u.telefon,
                  render: (u) => <span className="text-slate-700 dark:text-slate-200">{u.telefon || '—'}</span>,
                },
                {
                  id: 'is_active',
                  label: 'Holati',
                  sortBy: (u) => (u.is_active ? 1 : 0),
                  render: (u) => (
                    <Badge tone={u.is_active ? 'green' : 'red'}>
                      {u.is_active ? 'Faol' : 'Faol emas'}
                    </Badge>
                  ),
                },
                {
                  id: 'amallar',
                  label: '',
                  sortable: false,
                  align: 'right',
                  render: (u) => (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setHolatiOzgartiriladigan(u)}
                      disabled={toggleActiveMut.isPending}
                    >
                      {u.is_active ? 'Bloklash' : 'Faollashtirish'}
                    </Button>
                  ),
                },
              ] as DataTableColumn<User>[]
            }
          />
        </ResponsiveList>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Yangi xodim qo'shish"
        description="Xodim kirishi uchun login va parol bering."
      >
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="x-fish">To'liq ismi</Label>
            <Input
              id="x-fish"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="x-username">Foydalanuvchi nomi</Label>
            <Input
              id="x-username"
              required
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="x-parol">Parol</Label>
            <Input
              id="x-parol"
              required
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="x-rol">Lavozim</Label>
            <Select
              id="x-rol"
              value={form.rol}
              onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}
            >
              <option value="kutubxonachi">Kutubxonachi</option>
              <option value="administrator">Administrator</option>
            </Select>
          </Field>
          <Field>
            <Label htmlFor="x-telefon">Telefon</Label>
            <Input
              id="x-telefon"
              placeholder="+998 ..."
              value={form.telefon}
              onChange={(e) => setForm({ ...form, telefon: e.target.value })}
            />
          </Field>
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setModalOpen(false)}
              disabled={createMut.isPending}
            >
              Bekor qilish
            </Button>
            <Button type="submit" loading={createMut.isPending}>
              Saqlash
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!holatiOzgartiriladigan}
        title={holatiOzgartiriladigan?.is_active ? 'Xodimni bloklash' : 'Xodimni faollashtirish'}
        variant={holatiOzgartiriladigan?.is_active ? 'danger' : 'primary'}
        confirmLabel={holatiOzgartiriladigan?.is_active ? 'Bloklash' : 'Faollashtirish'}
        loading={toggleActiveMut.isPending}
        message={
          holatiOzgartiriladigan && (
            <>
              <b>{holatiOzgartiriladigan.full_name}</b> (
              @{holatiOzgartiriladigan.username}) xodimi{' '}
              {holatiOzgartiriladigan.is_active
                ? 'kirishidan mahrum qilinsinmi?'
                : 'qayta faollashtirilsinmi?'}
            </>
          )
        }
        onConfirm={() =>
          holatiOzgartiriladigan &&
          toggleActiveMut.mutate({
            id: holatiOzgartiriladigan.id,
            is_active: !holatiOzgartiriladigan.is_active,
          })
        }
        onCancel={() => setHolatiOzgartiriladigan(null)}
      />
    </div>
  )
}
