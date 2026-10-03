import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { holdsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { BAND_HOLATI_LABELS, type BandQilish, type BandHolati } from '../types'
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
  PageHeader,
  Pagination,
  Select,
  Table,
  TableSkeleton,
  Textarea,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { useDebouncedValue } from '../hooks/useDebouncedValue'

const TONE: Record<BandHolati, 'blue' | 'green' | 'red' | 'slate'> = {
  kutmoqda: 'blue',
  tasdiqlandi: 'green',
  rad_etildi: 'red',
  bekor_qilindi: 'slate',
}

export function Bandlar() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<BandHolati | ''>('kutmoqda')
  const [search, setSearch] = useState('')
  const kechikkanQidiruv = useDebouncedValue(search)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'approve' | 'reject' | 'view'>('view')
  const [selected, setSelected] = useState<BandQilish | null>(null)
  const [izoh, setIzoh] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['holds', page, holati, kechikkanQidiruv],
    queryFn: () =>
      holdsApi.list({ page, holati: holati || undefined, kitob: kechikkanQidiruv ? parseInt(kechikkanQidiruv) || undefined : undefined }),
  })

  const approveMut = useMutation({
    mutationFn: (id: number) => holdsApi.approve(id, izoh || undefined),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['holds'] })
      toast.success(`Band tasdiqlandi. Kitob "${r.kitob_nomi}" so'rov qiluvchiga berildi.`)
      setModalOpen(false)
      setIzoh('')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const rejectMut = useMutation({
    mutationFn: (id: number) => holdsApi.reject(id, izoh || undefined),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['holds'] })
      toast.success(`Band rad etildi. Kitob "${r.kitob_nomi}" yana berishga ochiq.`)
      setModalOpen(false)
      setIzoh('')
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const handleApprove = (b: BandQilish) => {
    setSelected(b)
    setModalMode('approve')
    setModalOpen(true)
  }

  const handleReject = (b: BandQilish) => {
    setSelected(b)
    setModalMode('reject')
    setModalOpen(true)
  }

  const handleConfirm = () => {
    if (!selected) return
    if (modalMode === 'approve') {
      approveMut.mutate(selected.id)
    } else {
      rejectMut.mutate(selected.id)
    }
  }

  const handleCancel = () => {
    setModalOpen(false)
    setIzoh('')
  }

  if (isLoading) {
    return <TableSkeleton rows={5} cols={7} />
  }
  if (isError) {
    return <ErrorState message={String(listError)} onRetry={() => refetch()} />
  }

  const royxat = data?.results ?? []

  return (
    <div className="space-y-6">
      <PageHeader
        title="🔒 Band qilingan kitoblar"
        subtitle="Tasdiqlash kutilayotgan so'rovlarni ko'rib chiqing, tasdiqlang yoki rad eting."
      />

      <Card className="p-4 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex gap-2">
            <Input
              placeholder="Kitob ID yoki nomi..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-64"
            />
            <Select
              value={holati}
              onChange={(e) => setHolati(e.target.value as BandHolati | '')}
              className="w-48"
            >
              <option value="">Barcha holatlar</option>
              <option value="kutmoqda">Kutmoqda</option>
              <option value="tasdiqlandi">Tasdiqlandi</option>
              <option value="rad_etildi">Rad etildi</option>
              <option value="bekor_qilindi">Bekor qilindi</option>
            </Select>
          </div>
          <div className="text-sm text-slate-500 dark:text-slate-400">
            Jami: {data?.count ?? 0} ta so'rov
          </div>
        </div>

        {error && <ErrorBanner message={error} />}

        {royxat.length === 0 ? (
          <EmptyState
            icon="🔒"
            title="Band so'rovi topilmadi"
            description={holati
              ? `Holat "${BAND_HOLATI_LABELS[holati]}" bo'yicha hech qanday so'rov yo'q.`
              : 'Hozircha bitta ham band so\'rovi kiritilmagan.'}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <thead>
                  <tr>
                    <th className="w-16">ID</th>
                    <th>Kitob</th>
                    <th className="w-48">So'ragan o'quvchi</th>
                    <th className="w-40">Holat</th>
                    <th className="w-40">So'rov sanasi</th>
                    <th className="w-36">Tasdiqlovchi</th>
                    <th className="w-48">Harakat</th>
                  </tr>
                </thead>
                <tbody>
                  {royxat.map((b) => (
                    <tr key={b.id}>
                      <td className="font-mono text-sm">{b.id}</td>
                      <td>
                        <div className="font-medium">{b.kitob_nomi}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          {b.kitob_muallif}
                        </div>
                      </td>
                      <td>
                        <div>{b.oquvchi_fish}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          {b.oquvchi_rol === 'oqituvchi'
                            ? `O'qituvchi — ${b.oquvchi_sinf || 'Fan belgilanmagan'}`
                            : `O'quvchi — ${b.oquvchi_sinf || 'Sinf belgilanmagan'}`}
                        </div>
                      </td>
                      <td>
                        <Badge tone={TONE[b.holati]}>
                          {BAND_HOLATI_LABELS[b.holati]}
                        </Badge>
                      </td>
                      <td className="text-sm">{b.so_rov_sanasi.slice(0, 16).replace('T', ' ')}</td>
                      <td className="text-sm">
                        {b.tasdiqlovchi_fish || (b.holati === 'kutmoqda' ? '—' : 'Noma\'lum')}
                      </td>
                      <td>
                        {b.holati === 'kutmoqda' ? (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="primary"
                              className="w-full"
                              disabled={approveMut.isPending}
                              onClick={() => handleApprove(b)}
                            >
                              ✅ Tasdiqlash
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              className="w-full"
                              disabled={rejectMut.isPending}
                              onClick={() => handleReject(b)}
                            >
                              ❌ Rad etish
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {b.holati === 'tasdiqlandi' && b.berish
                              ? 'Berish yaratildi'
                              : '—'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
            <Pagination
              count={data?.count ?? 0}
              page={page}
              pageSize={20}
              onChange={setPage}
            />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={modalOpen}
        onCancel={handleCancel}
        onConfirm={handleConfirm}
        loading={approveMut.isPending || rejectMut.isPending}
        title={modalMode === 'approve' ? '✅ Bandni tasdiqlash' : '❌ Bandni rad etish'}
        message={
          selected
            ? (
              <>
                <p className="mb-4">
                  Kitob: <strong>{selected.kitob_nomi}</strong> — {selected.kitob_muallif}
                </p>
                <p className="mb-4">
                  So'ragan: <strong>{selected.oquvchi_fish}</strong>
                </p>
                <p className="mb-4">
                  Holati: <Badge tone={TONE[selected.holati]}>{BAND_HOLATI_LABELS[selected.holati]}</Badge>
                </p>
                <p className="mb-4">
                  So'rov sanasi: {selected.so_rov_sanasi.slice(0, 16).replace('T', ' ')}
                </p>
                {selected.izoh && (
                  <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
                    <em>Sabab: {selected.izoh}</em>
                  </p>
                )}
                <Field>
                  <Label htmlFor="izoh">Izoh (ixtiyoriy)</Label>
                  <Textarea
                    id="izoh"
                    placeholder="Tasdiqlash/rad etish sababi..."
                    value={izoh}
                    onChange={(e) => setIzoh(e.target.value)}
                    rows={3}
                  />
                </Field>
              </>
            )
            : 'Tanlov bekor qilindi'
        }
        confirmLabel={modalMode === 'approve' ? 'Tasdiqlash' : 'Rad etish'}
        variant={modalMode === 'approve' ? 'primary' : 'danger'}
      />
    </div>
  )
}