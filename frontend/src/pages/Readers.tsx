import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import type { Oquvchi, OquvchiCreatePayload, OquvchiRol } from '../types'
import {
  Badge,
  Button,
  Card,
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
  TableSkeleton,
} from '../components/ui'
import DataTable, { type DataTableColumn } from '../components/DataTable'
import { useToast } from '../components/Toast'
import { useDebouncedValue } from '../hooks/useDebouncedValue'

const emptyForm: OquvchiCreatePayload = {
  rol: 'oquvchi',
  fish: '',
  telefon: '+998',
  sinf: '',
  kasb: '',
  tugilgan_sana: '',
  manzil: '',
}

interface ReadersProps {
  /** `oquvchi` — "O'quvchilar" bo'limi; `oqituvchi` — "O'qituvchilar" bo'limi.
   *  Berilmasa `oquvchi` deb hisoblanadi: har bir bo'lim faqat o'z
   *  a'zolarini ko'rsatadi (aralash ro'yxat chiqmasligi uchun). */
  rol?: OquvchiRol
}

export function Readers({ rol = 'oquvchi' }: ReadersProps = {}) {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const kechikkanQidiruv = useDebouncedValue(search)
  // AI buyruq paneli (Ctrl+K) qidiruvni `?q=` orqali to'ldiradi.
  const [urlParams] = useSearchParams()
  useEffect(() => {
    const q = urlParams.get('q')
    if (q !== null) setSearch(q)
  }, [urlParams])
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<OquvchiCreatePayload>({ ...emptyForm, rol: rol ?? 'oquvchi' })
  const [error, setError] = useState<string | null>(null)

  const oqituvchilar = rol === 'oqituvchi'

  const {
    data,
    isLoading,
    isError,
    error: listError,
    refetch: refetchList,
    isFetching,
  } = useQuery({
    queryKey: ['readers', page, kechikkanQidiruv, rol ?? null],
    queryFn: () =>
      readersApi.list({ page, search: kechikkanQidiruv || undefined, rol: rol ?? undefined }),
  })

  const createMut = useMutation({
    mutationFn: (payload: OquvchiCreatePayload) => readersApi.create(payload),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['readers'] })
      setModalOpen(false)
      toast.success(`${r.fish} ro‘yxatga qo‘shildi. Karta: ${r.karta_raqami}`)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const toggleActiveMut = useMutation({
    mutationFn: ({ id, faol }: { id: number; faol: boolean }) => readersApi.update(id, { faol }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['readers'] })
      toast.success(vars.faol ? 'O‘quvchi faollashtirildi.' : 'O‘quvchi bloklandi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  function openCreate() {
    setForm({ ...emptyForm, rol: rol ?? 'oquvchi' })
    setError(null)
    setModalOpen(true)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    createMut.mutate(form)
  }

  const qidirilmoqda = search.trim().length > 0

  return (
    <div>
      <PageHeader
        title={oqituvchilar ? "O'qituvchilar" : "O'quvchilar"}
        subtitle={
          oqituvchilar
            ? "Faqat a'zo bo'lgan o'qituvchilar ro'yxati"
            : "Kutubxona a'zolari ro'yxati"
        }
        actions={
          <Button onClick={openCreate}>
            <span aria-hidden>+</span> {oqituvchilar ? "Yangi o'qituvchi" : "Yangi o'quvchi"}
          </Button>
        }
      />

      {/* Qidiruv maydoni. Arizalar va jarimalar alohida sahifalarda:
          /applications va /fines (yuqoridagi menyuda). */}
      <Card className="mb-4 p-3 sm:p-4">
        <Input
          placeholder="Ism, telefon yoki karta raqami bo'yicha qidirish..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          aria-label="O'quvchilarni qidirish"
        />
      </Card>
      {isLoading && <TableSkeleton rows={6} cols={5} />}

      {isError && !isLoading && (
        <ErrorState
          title="O‘quvchilarni yuklab bo‘lmadi"
          message={errorMessage(listError)}
          onRetry={() => void refetchList()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon={
            qidirilmoqda ? (
              <Icons.search className="h-10 w-10" />
            ) : oqituvchilar ? (
              <Icons.user className="h-10 w-10" />
            ) : (
              <Icons.graduationCap className="h-10 w-10" />
            )
          }
          title={
            qidirilmoqda
              ? 'Hech narsa topilmadi'
              : oqituvchilar
                ? "Hali o'qituvchi qo'shilmagan"
                : 'Hali o‘quvchi qo‘shilmagan'
          }
          description={
            qidirilmoqda
              ? `«${search}» bo‘yicha natija yo‘q. Boshqa so‘z bilan urinib ko‘ring.`
              : oqituvchilar
                ? "Birinchi o'qituvchini qo'shish uchun yuqoridagi tugmani bosing."
                : 'Birinchi o‘quvchini qo‘shish uchun yuqoridagi tugmani bosing.'
          }
          action={
            qidirilmoqda ? (
              <Button variant="secondary" size="sm" onClick={() => setSearch('')}>
                Qidiruvni tozalash
              </Button>
            ) : (
              <Button size="sm" onClick={openCreate}>
                {oqituvchilar ? "Yangi o'qituvchi" : 'Yangi o‘quvchi'}
              </Button>
            )
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Oquvchi>
          items={data.results}
          render={(r) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <Link
                    to={`/readers/${r.id}`}
                    className="font-medium text-brand-700 hover:underline dark:text-brand-400"
                  >
                    {r.fish}
                  </Link>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {oqituvchilar
                      ? r.kasb || 'Fan ko‘rsatilmagan'
                      : r.sinf || 'Sinf ko‘rsatilmagan'}
                  </div>
                </div>
                <Badge tone={r.faol ? 'green' : 'red'}>{r.faol ? 'Faol' : 'Bloklangan'}</Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">{r.telefon}</div>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                <Icons.idCard className="h-4 w-4 shrink-0" />
                {r.karta_raqami}
              </div>
              <Button
                size="sm"
                variant="secondary"
                className="w-full"
                disabled={toggleActiveMut.isPending}
                onClick={() => toggleActiveMut.mutate({ id: r.id, faol: !r.faol })}
              >
                {r.faol ? 'Bloklash' : 'Faollashtirish'}
              </Button>
            </div>
          )}
        >
          <DataTable<Oquvchi>
            data={data.results}
            getRowId={(r) => r.id}
            emptyText="O'quvchi topilmadi"
            pagination={{
              count: data.count,
              page: page - 1,
              rowsPerPage: 20,
              onPageChange: (p) => setPage(p + 1),
            }}
            columns={
              [
                {
                  id: 'fish',
                  label: 'F.I.Sh.',
                  sortBy: (r) => r.fish,
                  render: (r) => (
                    <Link to={`/readers/${r.id}`} className="font-medium text-brand-700 hover:underline dark:text-brand-400">
                      {r.fish}
                    </Link>
                  ),
                },
                {
                  id: 'sinf',
                  label: oqituvchilar ? 'Fan' : 'Sinf',
                  sortBy: (r) => (oqituvchilar ? r.kasb : r.sinf),
                  render: (r) => (oqituvchilar ? r.kasb || '—' : r.sinf || '—'),
                },
                { id: 'telefon', label: 'Telefon', sortBy: (r) => r.telefon },
                { id: 'karta_raqami', label: 'Karta raqami', sortBy: (r) => r.karta_raqami },
                {
                  id: 'faol',
                  label: 'Holati',
                  sortBy: (r) => (r.faol ? 1 : 0),
                  render: (r) => <Badge tone={r.faol ? 'green' : 'red'}>{r.faol ? 'Faol' : 'Bloklangan'}</Badge>,
                },
                {
                  id: 'amallar',
                  label: '',
                  sortable: false,
                  align: 'right',
                  render: (r) => (
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={toggleActiveMut.isPending}
                      onClick={() => toggleActiveMut.mutate({ id: r.id, faol: !r.faol })}
                    >
                      {r.faol ? 'Bloklash' : 'Faollashtirish'}
                    </Button>
                  ),
                },
              ] as DataTableColumn<Oquvchi>[]
            }
          />
        </ResponsiveList>
      )}

      {/* Mobilda jadvaldagi MUI pagination ko'rinmaydi */}
      {data && (
        <div className="md:hidden">
          <Pagination count={data.count} page={page} onChange={setPage} />
        </div>
      )}


      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={oqituvchilar ? "Yangi o'qituvchi qo'shish" : "Yangi o'quvchi qo'shish"}
      >
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="y-fish">To'liq ismi</Label>
            <Input
              id="y-fish"
              required
              value={form.fish}
              onChange={(e) => setForm({ ...form, fish: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="y-telefon">Telefon raqami</Label>
            <Input
              id="y-telefon"
              required
              placeholder="+998901234567"
              value={form.telefon}
              onChange={(e) => setForm({ ...form, telefon: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor={oqituvchilar ? 'y-kasb' : 'y-sinf'}>
              {oqituvchilar ? "O'qitayotgan fan" : 'Sinf'}
            </Label>
            <Input
              id={oqituvchilar ? 'y-kasb' : 'y-sinf'}
              required={oqituvchilar}
              placeholder={oqituvchilar ? 'Matematika' : '7-A'}
              value={oqituvchilar ? (form.kasb ?? '') : form.sinf}
              onChange={(e) =>
                setForm(
                  oqituvchilar
                    ? { ...form, kasb: e.target.value }
                    : { ...form, sinf: e.target.value },
                )
              }
            />
          </Field>
          <Field>
            <Label htmlFor="y-tugilgan">Tug'ilgan sana</Label>
            <Input
              id="y-tugilgan"
              type="date"
              value={form.tugilgan_sana}
              onChange={(e) => setForm({ ...form, tugilgan_sana: e.target.value })}
            />
          </Field>
          <Field>
            <Label htmlFor="y-manzil">Manzil</Label>
            <Input
              id="y-manzil"
              value={form.manzil}
              onChange={(e) => setForm({ ...form, manzil: e.target.value })}
            />
          </Field>
          <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Bekor qilish
            </Button>
            <Button type="submit" loading={createMut.isPending}>
              Saqlash
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
