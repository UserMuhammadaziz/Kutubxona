import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { copiesApi, loansApi, readersApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { BERISH_HOLATI_LABELS, type Berish, type BerishCreatePayload, type BerishHolati } from '../types'
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
  ListSkeleton,
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
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { formatDate, formatMoney } from '../lib/format'

const TONE: Record<BerishHolati, 'blue' | 'green' | 'red'> = {
  faol: 'blue',
  qaytarilgan: 'green',
  yoqolgan: 'red',
}

export function Loans() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<BerishHolati | ''>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [readerSearch, setReaderSearch] = useState('')
  const kechikkanReaderSearch = useDebouncedValue(readerSearch)
  const [form, setForm] = useState<BerishCreatePayload>({ nusxa: 0, oquvchi: 0 })
  const [error, setError] = useState<string | null>(null)
  const [qaytariladigan, setQaytariladigan] = useState<Berish | null>(null)

  const { data, isLoading, isError, error: listError, refetch, isFetching } = useQuery({
    queryKey: ['loans', page, holati],
    queryFn: () => loansApi.list({ page, holati: holati || undefined }),
  })

  const { data: readers, isLoading: readersLoading } = useQuery({
    queryKey: ['readers', 'for-select', kechikkanReaderSearch],
    queryFn: () => readersApi.list({ search: kechikkanReaderSearch || undefined }),
    enabled: modalOpen,
  })

  const { data: availableCopies, isLoading: copiesLoading } = useQuery({
    queryKey: ['copies', 'available-for-select'],
    queryFn: () => copiesApi.list({ holati: 'mavjud' }),
    enabled: modalOpen,
  })

  const createMut = useMutation({
    mutationFn: (payload: BerishCreatePayload) => loansApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['readers'] })
      setModalOpen(false)
      toast.success('Kitob berildi. O‘quvchiga Telegram orqali xabar yuborildi.')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const returnMut = useMutation({
    mutationFn: (id: number) => loansApi.return(id),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      qc.invalidateQueries({ queryKey: ['fines'] })
      qc.invalidateQueries({ queryKey: ['reservations'] })
      setQaytariladigan(null)
      if (res.jarima_summasi) {
        toast.success(
          `Kitob qaytarildi. Jarima: ${formatMoney(res.jarima_summasi)}`,
        )
      } else {
        toast.success('Kitob qaytarildi. Jarima yo‘q.')
      }
      if (res.navbatga_taklif_ketdimi) {
        toast.info('Kitob band bo‘lgani uchun navbatdagi o‘quvchiga taklif yuborildi.')
      }
    },
    onError: (err) => toast.error(errorMessage(err)),
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
    setError(null)
    createMut.mutate(form)
  }

  const filtrBor = holati !== ''

  return (
    <div>
      <PageHeader
        title="Berish / Qaytarish"
        subtitle="Kitob berish va qaytarish jarayonlari"
        actions={
          <Button onClick={openCreate} className="w-full sm:w-auto">
            + Kitob berish
          </Button>
        }
      />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="sm:w-64">
          <Select
            value={holati}
            onChange={(e) => {
              setHolati(e.target.value as BerishHolati | '')
              setPage(1)
            }}
            aria-label="Berish holati"
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(BERISH_HOLATI_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {isLoading && <TableSkeleton rows={6} cols={6} />}

      {isError && !isLoading && (
        <ErrorState
          title="Berishlarni yuklab bo‘lmadi"
          message={errorMessage(listError)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon="📚"
          title={filtrBor ? 'Berish topilmadi' : 'Hali berishlar yo‘q'}
          description={
            filtrBor
              ? 'Boshqa holat filtrini tanlab ko‘ring.'
              : 'Yuqoridagi «Kitob berish» tugmasi orqali birinchi kitobni bering.'
          }
          action={
            filtrBor ? (
              <Button variant="secondary" size="sm" onClick={() => setHolati('')}>
                Filtrni tozalash
              </Button>
            ) : (
              <Button size="sm" onClick={openCreate}>
                + Kitob berish
              </Button>
            )
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Berish>
          items={data.results}
          render={(l) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium text-slate-900 dark:text-slate-100">
                    {l.kitob_nomi}
                  </div>
                  <div className="text-xs text-slate-400">{l.inventar_raqami}</div>
                </div>
                <Badge tone={TONE[l.holati]}>{BERISH_HOLATI_LABELS[l.holati]}</Badge>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-300">{l.oquvchi_fish}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Berilgan: {formatDate(l.berilgan_sana)} · Muddat: {formatDate(l.qaytarish_muddati)}
              </div>
              {l.holati === 'faol' && (
                <Button size="sm" className="w-full" onClick={() => setQaytariladigan(l)}>
                  Qaytarish
                </Button>
              )}
            </div>
          )}
        >
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
                    <div className="font-medium text-slate-900 dark:text-slate-100">
                      {l.kitob_nomi}
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-500">
                      {l.inventar_raqami}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{l.oquvchi_fish}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                    {formatDate(l.berilgan_sana)}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                    {formatDate(l.qaytarish_muddati)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={TONE[l.holati]}>{BERISH_HOLATI_LABELS[l.holati as BerishHolati]}</Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {l.holati === 'faol' && (
                      <Button size="sm" onClick={() => setQaytariladigan(l)} disabled={returnMut.isPending}>
                        Qaytarish
                      </Button>
                    )}
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
        onClose={() => setModalOpen(false)}
        title="Kitob berish"
        description="O‘quvchi va mavjud nusxani tanlang. Berish Telegram orqali xabar bilan tasdiqlanadi."
      >
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="l-qidirish">O'quvchini qidirish</Label>
            <Input
              id="l-qidirish"
              placeholder="Ism, sinf yoki telefon..."
              value={readerSearch}
              onChange={(e) => setReaderSearch(e.target.value)}
            />
          </Field>
          <Field>
            <Label htmlFor="l-oquvchi">O'quvchi</Label>
            {readersLoading ? (
              <Spinner label="O‘quvchilar yuklanmoqda..." className="py-2" />
            ) : (
              <Select
                id="l-oquvchi"
                value={form.oquvchi}
                onChange={(e) => setForm({ ...form, oquvchi: Number(e.target.value) })}
              >
                <option value={0}>Tanlang...</option>
                {readers?.results.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.fish} {r.sinf ? `— ${r.sinf}-sinf` : ''} — {r.telefon}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field>
            <Label htmlFor="l-nusxa">Mavjud nusxa</Label>
            {copiesLoading ? (
              <ListSkeleton rows={3} className="py-2" />
            ) : availableCopies?.results.length ? (
              <Select
                id="l-nusxa"
                value={form.nusxa}
                onChange={(e) => setForm({ ...form, nusxa: Number(e.target.value) })}
              >
                <option value={0}>Tanlang...</option>
                {availableCopies.results.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.kitob_nomi} — {c.inventar_raqami}
                  </option>
                ))}
              </Select>
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Hozircha mavjud nusxa yo‘q. Avval nusxa qo‘shing.
              </p>
            )}
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
              Berish
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!qaytariladigan}
        title="Kitobni qaytarish"
        confirmLabel="Qaytarish"
        loading={returnMut.isPending}
        message={
          qaytariladigan && (
            <>
              <b>{qaytariladigan.kitob_nomi}</b> ({qaytariladigan.inventar_raqami}) kitobini{' '}
              <b>{qaytariladigan.oquvchi_fish}</b>dan qaytarasizmi?
              <br />
              <br />
              Muddat o‘tganda jarima avtomatik hisoblanadi.
            </>
          )
        }
        onConfirm={() => qaytariladigan && returnMut.mutate(qaytariladigan.id)}
        onCancel={() => setQaytariladigan(null)}
      />
    </div>
  )
}
