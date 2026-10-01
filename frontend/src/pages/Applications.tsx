import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import type { Ariza, ArizaHolati } from '../types'
import { ARIZA_HOLATI_LABELS } from '../types'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Label,
  Modal,
  PageHeader,
  Pagination,
  ResponsiveList,
  Select,
  Table,
  TableSkeleton,
  Textarea,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { formatDate } from '../lib/format'

const TONE: Record<ArizaHolati, 'amber' | 'green' | 'red'> = {
  kutmoqda: 'amber',
  tasdiqlandi: 'green',
  bekor: 'red',
}

export function Applications() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<ArizaHolati | ''>('kutmoqda')
  const [search, setSearch] = useState('')
  const kechikkanQidiruv = useDebouncedValue(search)
  const [qabulAriza, setQabulAriza] = useState<Ariza | null>(null)
  const [radEtishAriza, setRadEtishAriza] = useState<Ariza | null>(null)
  const [radSababi, setRadSababi] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    // `page` kalitga kiritilishi shart: aks holda Pagination bosilganda
    // queryKey o'zgarmaydi va 1-sahifa natijasi qayta ishlatiladi.
    // `kechikkanQidiruv` esa har bir tugma bosilishida so'rov yubormasligi
    // uchun ishlatiladi.
    queryKey: ['applications', page, holati, kechikkanQidiruv],
    queryFn: () =>
      applicationsApi.list({
        page,
        holati: holati || undefined,
        search: kechikkanQidiruv.trim() || undefined,
      }),
  })

  const approveMut = useMutation({
    mutationFn: (id: number) => applicationsApi.approve(id),
    onSuccess: (ariza) => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      qc.invalidateQueries({ queryKey: ['readers'] })
      setQabulAriza(null)
      toast.success(`«${ariza.fish}» tasdiqlandi — o‘quvchi ro‘yxatga qo‘shildi.`)
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const rejectMut = useMutation({
    mutationFn: ({ id, izoh }: { id: number; izoh: string }) => applicationsApi.reject(id, izoh),
    onSuccess: (ariza) => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      setRadEtishAriza(null)
      setRadSababi('')
      toast.success(`«${ariza.fish}» arizasi rad etildi.`)
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  function qidirishOzgardi(qiymat: string) {
    setSearch(qiymat)
    setPage(1)
  }

  function holatiOzgardi(qiymat: string) {
    setHolati(qiymat as ArizaHolati | '')
    setPage(1)
  }

  return (
    <div>
      <PageHeader
        title="A'zolik arizalari"
        subtitle="Telegram bot orqali kelgan arizalarni ko'rib chiqing"
      />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="min-w-0 flex-1">
            <Input
              placeholder="Ism, telefon yoki Telegram ID bo‘yicha qidirish..."
              value={search}
              onChange={(e) => qidirishOzgardi(e.target.value)}
              aria-label="Arizalarni qidirish"
            />
          </div>
          <div className="sm:w-56">
            <Select
              value={holati}
              onChange={(e) => holatiOzgardi(e.target.value)}
              aria-label="Ariza holati"
            >
              <option value="">Barcha holatlar</option>
              {Object.entries(ARIZA_HOLATI_LABELS).map(([qiymat, nomi]) => (
                <option key={qiymat} value={qiymat}>
                  {nomi}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      {isLoading && <TableSkeleton rows={6} cols={5} />}

      {isError && !isLoading && (
        <ErrorState
          title="Arizalarni yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon="📭"
          title={holati === 'kutmoqda' ? 'Kutilayotgan ariza yo‘q' : 'Ariza topilmadi'}
          description={
            holati === 'kutmoqda'
              ? "Telegram bot orqali kelgan yangi a'zo arizalari shu yerda paydo bo'ladi."
              : 'Filtrni o‘zgartirib ko‘ring yoki boshqa so‘z bilan qidiring.'
          }
          action={
            search || holati ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  qidirishOzgardi('')
                  holatiOzgardi('')
                }}
              >
                Filtrni tozalash
              </Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Ariza>
          items={data.results}
          render={(a) => (
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium text-slate-900 dark:text-slate-100">{a.fish}</div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">📞 {a.telefon}</div>
                </div>
                <Badge tone={TONE[a.holati]}>{ARIZA_HOLATI_LABELS[a.holati]}</Badge>
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                🎓 {a.sinf || 'Sinf ko‘rsatilmagan'} · Telegram: {a.telegram_id}
              </div>
              <div className="text-xs text-slate-400">{formatDate(a.ariza_sanasi)}</div>
              {a.izoh && (
                <div className="text-xs text-slate-500 dark:text-slate-400">📝 {a.izoh}</div>
              )}
              {a.holati === 'kutmoqda' && (
                <div className="mt-1 flex gap-2">
                  <Button
                    size="sm"
                    variant="danger"
                    className="flex-1"
                    onClick={() => {
                      setRadSababi('')
                      setRadEtishAriza(a)
                    }}
                  >
                    Rad etish
                  </Button>
                  <Button size="sm" className="flex-1" onClick={() => setQabulAriza(a)}>
                    Qabul qilish
                  </Button>
                </div>
              )}
            </div>
          )}
        >
          <Table>
            <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">F.I.Sh.</th>
                <th className="px-4 py-3">Sinf</th>
                <th className="px-4 py-3">Telefon</th>
                <th className="px-4 py-3">Holati</th>
                <th className="px-4 py-3">Sana</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {data.results.map((a) => (
                <tr key={a.id} className="hover:bg-canvas dark:hover:bg-slate-800/50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900 dark:text-slate-100">{a.fish}</div>
                    <div className="text-xs text-slate-400">Telegram: {a.telegram_id}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{a.sinf || '—'}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{a.telefon}</td>
                  <td className="px-4 py-3">
                    <Badge tone={TONE[a.holati]}>{ARIZA_HOLATI_LABELS[a.holati]}</Badge>
                    {a.izoh && <div className="mt-1 text-xs text-slate-400">{a.izoh}</div>}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                    {formatDate(a.ariza_sanasi)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {a.holati === 'kutmoqda' && (
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => {
                            setRadSababi('')
                            setRadEtishAriza(a)
                          }}
                        >
                          Rad etish
                        </Button>
                        <Button size="sm" onClick={() => setQabulAriza(a)}>
                          Qabul qilish
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

      {data && <Pagination count={data.count} page={page} onChange={setPage} />}

      <ConfirmDialog
        open={!!qabulAriza}
        title="Arizani qabul qilish"
        variant="primary"
        confirmLabel="Qabul qilish"
        loading={approveMut.isPending}
        message={
          qabulAriza && (
            <>
              <b>{qabulAriza.fish}</b> (sinf: {qabulAriza.sinf || '—'}) arizasini qabul qilib,{' '}
              <b>o‘quvchi</b> ro‘yxatiga qo‘shasizmi?
              <br />
              <br />
              Karta raqami avtomatik beriladi va Telegram orqali tasdiqlash xabari yuboriladi.
            </>
          )
        }
        onConfirm={() => qabulAriza && approveMut.mutate(qabulAriza.id)}
        onCancel={() => setQabulAriza(null)}
      />

      <Modal open={!!radEtishAriza} onClose={() => setRadEtishAriza(null)} title="Arizani rad etish">
        <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">
          <b>{radEtishAriza?.fish}</b> arizasini rad etmoqchimisiz? Sabab o‘quvchiga Telegram orqali
          yuboriladi (ixtiyoriy).
        </p>
        <Field>
          <Label htmlFor="a-rad-sababi">Sabab</Label>
          <Textarea
            id="a-rad-sababi"
            rows={3}
            maxLength={255}
            placeholder="Masalan: telefon raqami noto‘g‘ri kiritilgan"
            value={radSababi}
            onChange={(e) => setRadSababi(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-400">{radSababi.length}/255</p>
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={() => setRadEtishAriza(null)} disabled={rejectMut.isPending}>
            Bekor qilish
          </Button>
          <Button
            variant="danger"
            loading={rejectMut.isPending}
            onClick={() => radEtishAriza && rejectMut.mutate({ id: radEtishAriza.id, izoh: radSababi })}
          >
            Rad etish
          </Button>
        </div>
      </Modal>
    </div>
  )
}
