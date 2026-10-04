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
  ResponsiveList,
  Select,
  Table,
  TableSkeleton,
  Textarea,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { formatDateTime } from '../lib/format'

const TONE: Record<BandHolati, 'blue' | 'green' | 'red' | 'slate'> = {
  kutmoqda: 'blue',
  tasdiqlandi: 'green',
  rad_etildi: 'red',
  bekor_qilindi: 'slate',
}

const PAGE_SIZE = 20

/**
 * «Tasdiqlash» va «Rad etish» tugmalari.
 *
 * `h-9` — ikkala tugma ham bir xil balandlikda bo'lishi uchun (matn
 * sichqonchani bo'lganda ham satr buzilmasin), `whitespace-nowrap` —
 * qisqa ekranda matn ikki qatorga bo'linib ketmasin.
 */
function HarakatTugmalari({
  band,
  busy,
  onApprove,
  onReject,
}: {
  band: BandQilish
  busy: boolean
  onApprove: (b: BandQilish) => void
  onReject: (b: BandQilish) => void
}) {
  if (band.holati !== 'kutmoqda') {
    const natija =
      band.holati === 'tasdiqlandi'
        ? band.berish
          ? 'Berish yaratildi'
          : 'Tasdiqlandi'
        : band.holati === 'rad_etildi'
          ? 'Rad etildi'
          : 'Bekor qilindi'
    return (
      <div className="min-w-0 text-xs text-slate-500 dark:text-slate-400">
        <div>{natija}</div>
        {/* Qaror izohi Telegram orqali o'quvchiga yuboriladi, lekin
            kutubxonachi uchun bu yozim faqat shu yerda ko'rinadi. */}
        {band.tasdiqlash_izohi?.trim() && (
          <div className="mt-1 break-words italic text-slate-400 dark:text-slate-500">
            Izoh: {band.tasdiqlash_izohi}
          </div>
        )}
      </div>
    )
  }
  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        variant="primary"
        className="h-9 flex-1 whitespace-nowrap"
        disabled={busy}
        onClick={() => onApprove(band)}
      >
        Tasdiqlash
      </Button>
      <Button
        size="sm"
        variant="danger"
        className="h-9 flex-1 whitespace-nowrap"
        disabled={busy}
        onClick={() => onReject(band)}
      >
        Rad etish
      </Button>
    </div>
  )
}

/** O'quvchi roli + sinfi (yoki kasbi) — ikki qatorli yordamchi matn. */
function OquvchiQatori({ band }: { band: BandQilish }) {
  const rol = band.oquvchi_rol === 'oqituvchi' ? 'O’qituvchi' : 'O’quvchi'
  const ikkinchi = band.oquvchi_rol === 'oqituvchi' ? 'Kasb' : 'Sinf'
  const qiymat = band.oquvchi_sinf?.trim()
  return (
    <>
      <div className="min-w-0 break-words font-medium text-slate-900 dark:text-slate-100">
        {band.oquvchi_fish}
      </div>
      <div className="text-xs text-slate-500 dark:text-slate-400">
        {qiymat ? `${rol} — ${qiymat}` : `${rol} — ${ikkinchi} belgilanmagan`}
      </div>
    </>
  )
}

export function Bandlar() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<BandHolati | ''>('kutmoqda')
  const [search, setSearch] = useState('')
  const kechikkanQidiruv = useDebouncedValue(search)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'approve' | 'reject'>('approve')
  const [selected, setSelected] = useState<BandQilish | null>(null)
  const [izoh, setIzoh] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Qidiruv maydoniga faqat son kiritiladi. Backend `kitob` filtrini
  // `isdigit()` bilan tekshiradi, shuning uchun "12abc" kabi qiymat
  // yuborilsa javob kutilmagan bo'lardi (odatda 12-ga filtrlanadi).
  const kitobId = /^\d+$/.test(kechikkanQidiruv.trim())
    ? Number(kechikkanQidiruv.trim())
    : undefined

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['holds', page, holati, kitobId],
    queryFn: () =>
      holdsApi.list({ page, holati: holati || undefined, kitob: kitobId }),
  })

  const approveMut = useMutation({
    mutationFn: (id: number) => holdsApi.approve(id, izoh || undefined),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['holds'] })
      toast.success(`Band tasdiqlandi. "${r.kitob_nomi}" so'rov qiluvchiga berildi.`)
      setModalOpen(false)
      setIzoh('')
      setError(null)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const rejectMut = useMutation({
    mutationFn: (id: number) => holdsApi.reject(id, izoh || undefined),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['holds'] })
      toast.success(`Band rad etildi. "${r.kitob_nomi}" yana berishga ochiq.`)
      setModalOpen(false)
      setIzoh('')
      setError(null)
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const busy = approveMut.isPending || rejectMut.isPending

  const openModal = (b: BandQilish, mode: 'approve' | 'reject') => {
    setSelected(b)
    setModalMode(mode)
    setIzoh('')
    // Eski xato yangi oynada ko'rinmasin.
    setError(null)
    setModalOpen(true)
  }

  const handleConfirm = () => {
    if (!selected || busy) return
    if (modalMode === 'approve') {
      approveMut.mutate(selected.id)
    } else {
      rejectMut.mutate(selected.id)
    }
  }

  const handleCancel = () => {
    if (busy) return
    setModalOpen(false)
    setIzoh('')
    setError(null)
  }

  if (isLoading) {
    return <TableSkeleton rows={5} cols={7} />
  }
  if (isError) {
    return <ErrorState message={errorMessage(listError)} onRetry={() => void refetch()} />
  }

  const royxat = data?.results ?? []
  // `kitobId` 0 ham bo'lishi mumkin (kitob ID 0 mavjud emas, lekin falsy
  // qiymat "filtr yo'q" deb hisoblanmasligi kerak).
  const filtrBor = Boolean(holati) || kitobId !== undefined

  return (
    <div className="space-y-6">
      <PageHeader
        title="🔒 Band qilingan kitoblar"
        subtitle="Tasdiqlash kutilayotgan so'rovlarni ko'rib chiqing, tasdiqlang yoki rad eting."
      />

      <Card className="p-4 space-y-4">
        {/* Filtr paneli: tor ekranda ustma-ust tushmasin, satrga o'ralsin. */}
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="w-full sm:w-52">
              <Input
                type="search"
                inputMode="numeric"
                aria-label="Kitob ID bo'yicha qidirish"
                placeholder="Kitob ID bo'yicha..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="w-full sm:w-44">
              <Select
                aria-label="Holat bo'yicha filtr"
                value={holati}
                onChange={(e) => {
                  setHolati(e.target.value as BandHolati | '')
                  setPage(1)
                }}
                className="w-full"
              >
                <option value="">Barcha holatlar</option>
                <option value="kutmoqda">Kutmoqda</option>
                <option value="tasdiqlandi">Tasdiqlandi</option>
                <option value="rad_etildi">Rad etilgan</option>
                <option value="bekor_qilindi">Bekor qilindi</option>
              </Select>
            </div>
          </div>
          <div className="shrink-0 text-sm text-slate-500 dark:text-slate-400">
            Jami: <span className="font-medium text-slate-700 dark:text-slate-200">{data?.count ?? 0}</span>{' '}
            ta so'rov
            {(holati || kitobId !== undefined) && (
              <span className="ml-1 text-xs">(tanlangan filtrga mos)</span>
            )}
          </div>
        </div>

        {error && !modalOpen && <ErrorBanner message={error} />}

        {royxat.length === 0 ? (
          <EmptyState
            icon="🔒"
            title="Band so'rovi topilmadi"
            description={
              holati
                ? `Holat "${BAND_HOLATI_LABELS[holati]}" bo'yicha hech qanday so'rov yo'q.`
                : kitobId !== undefined
                  ? `${kitobId} raqamli kitobga band so'rovi yo'q.`
                  : 'Hozircha bitta ham band so\'rovi kiritilmagan.'}
            action={
              filtrBor ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setHolati('')
                    setSearch('')
                    setPage(1)
                  }}
                >
                  Filtrni tozalash
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            <ResponsiveList<BandQilish>
              items={royxat}
              getKey={(b) => b.id}
              render={(b) => (
                <div className="flex flex-col gap-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="break-words font-medium text-slate-900 dark:text-slate-100">
                        {b.kitob_nomi}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {b.kitob_muallif}
                      </div>
                    </div>
                    <Badge tone={TONE[b.holati]}>{BAND_HOLATI_LABELS[b.holati]}</Badge>
                  </div>
                  <OquvchiQatori band={b} />
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    So'rov: {formatDateTime(b.so_rov_sanasi)}
                  </div>
                  {b.tasdiqlovchi_fish && (
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      Tasdiqlovchi: {b.tasdiqlovchi_fish}
                    </div>
                  )}
                  <HarakatTugmalari
                    band={b}
                    busy={busy}
                    onApprove={(x) => openModal(x, 'approve')}
                    onReject={(x) => openModal(x, 'reject')}
                  />
                </div>
              )}
            >
              <Table>
                <thead className="border-b border-slate-200 bg-canvas text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400">
                  <tr>
                    <th className="w-20 px-4 py-3">So'rov</th>
                    <th className="px-4 py-3">Kitob</th>
                    <th className="px-4 py-3">So&apos;ragan o&apos;quvchi</th>
                    <th className="px-4 py-3">Holat</th>
                    <th className="px-4 py-3">So&apos;rov sanasi</th>
                    <th className="px-4 py-3">Tasdiqlovchi</th>
                    <th className="w-64 px-4 py-3">Harakat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {royxat.map((b) => (
                    <tr key={b.id} className="align-top hover:bg-canvas dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        {/* Ikki xil ID bor: so'rov ID va kitob ID. Qidiruv
                            kitob ID bo'yicha — ikkalasini chalkashtirmaslik uchun
                            aniq yozilgan. */}
                        <div className="font-mono text-xs text-slate-500 dark:text-slate-400">
                          #{b.id}
                        </div>
                        <div className="font-mono text-xs text-slate-400 dark:text-slate-500">
                          kitob: {b.kitob}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="min-w-0 break-words font-medium text-slate-900 dark:text-slate-100">
                          {b.kitob_nomi}
                        </div>
                        <div className="break-words text-xs text-slate-500 dark:text-slate-400">
                          {b.kitob_muallif}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <OquvchiQatori band={b} />
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={TONE[b.holati]}>{BAND_HOLATI_LABELS[b.holati]}</Badge>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-700 dark:text-slate-200">
                        {formatDateTime(b.so_rov_sanasi)}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">
                        {b.tasdiqlovchi_fish ? (
                          <>
                            <div className="break-words">{b.tasdiqlovchi_fish}</div>
                            {b.tasdiqlash_sanasi && (
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {formatDateTime(b.tasdiqlash_sanasi)}
                              </div>
                            )}
                          </>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <HarakatTugmalari
                          band={b}
                          busy={busy}
                          onApprove={(x) => openModal(x, 'approve')}
                          onReject={(x) => openModal(x, 'reject')}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </ResponsiveList>
            <Pagination
              count={data?.count ?? 0}
              page={page}
              pageSize={PAGE_SIZE}
              onChange={setPage}
            />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={modalOpen}
        onCancel={handleCancel}
        onConfirm={handleConfirm}
        loading={busy}
        title={modalMode === 'approve' ? 'Bandni tasdiqlash' : 'Bandni rad etish'}
        message={
          selected ? (
            <>
              <dl className="mb-4 space-y-2">
                <div>
                  <dt className="text-xs uppercase text-slate-400">Kitob</dt>
                  <dd className="break-words font-medium text-slate-900 dark:text-slate-100">
                    {selected.kitob_nomi}
                    <span className="font-normal text-slate-500"> — {selected.kitob_muallif}</span>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase text-slate-400">So&apos;ragan</dt>
                  <dd className="font-medium text-slate-900 dark:text-slate-100">
                    {selected.oquvchi_fish}
                    <span className="font-normal text-slate-500">
                      {selected.oquvchi_rol === 'oqituvchi' ? ' (o&apos;qituvchi)' : ' (o&apos;quvchi)'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase text-slate-400">Holat</dt>
                  <dd>
                    <Badge tone={TONE[selected.holati]}>
                      {BAND_HOLATI_LABELS[selected.holati]}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase text-slate-400">So&apos;rov sanasi</dt>
                  <dd className="text-slate-700 dark:text-slate-200">
                    {formatDateTime(selected.so_rov_sanasi)}
                  </dd>
                </div>
              </dl>

              {modalMode === 'approve' && (
                <p className="mb-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:bg-slate-700/50 dark:text-slate-300">
                  Tasdiqlanganda kitob so&apos;rov qilgan o&apos;quvchiga beriladi va unga
                  qaytarish muddati bilan xabar yuboriladi.
                </p>
              )}

              {selected.izoh && (
                <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
                  <em>O&apos;quvchining sababi: {selected.izoh}</em>
                </p>
              )}

              <Field>
                <Label htmlFor="izoh">
                  {modalMode === 'approve' ? 'Izoh (ixtiyoriy)' : 'Rad etish sababi (ixtiyoriy)'}
                </Label>
                <Textarea
                  id="izoh"
                  placeholder={
                    modalMode === 'approve'
                      ? 'Masalan: 3-sinf darsiga tayyorlanmoqda...'
                      : 'Masalan: hozircha bitta nusxa bor, keyinroq taklif qilamiz...'
                  }
                  value={izoh}
                  onChange={(e) => setIzoh(e.target.value)}
                  rows={3}
                />
              </Field>

              {/* Xato oynaning ichida ko'rinishi kerak — aks holda foydalanuvchi
                  jadvaldagi banner'ni ko'rmaydi va nima bo'lganini bilmaydi. */}
              {error && (
                <div className="mt-3">
                  <ErrorBanner message={error} />
                </div>
              )}
            </>
          ) : (
            'So&apos;rov tanlanmagan'
          )
        }
        confirmLabel={modalMode === 'approve' ? 'Tasdiqlash' : 'Rad etish'}
        variant={modalMode === 'approve' ? 'primary' : 'danger'}
      />
    </div>
  )
}