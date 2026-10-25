import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reservationsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { NAVBAT_HOLATI_LABELS, NAVBAT_JAVOB_LABELS, type Navbat, type NavbatHolati } from '../types'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  ResponsiveList,
  Select,
  TableSkeleton,
} from '../components/ui'
import { useToast } from '../components/Toast'
import { formatDate } from '../lib/format'
import DataTable, { type DataTableColumn } from '../components/DataTable'

const TONE: Record<NavbatHolati, 'amber' | 'blue' | 'green' | 'red'> = {
  kutmoqda: 'amber',
  taklif_qilindi: 'blue',
  yakunlandi: 'green',
  bekor: 'red',
}

function muddatiOtdi(r: Navbat): boolean {
  return Boolean(r.taklif_muddati) && new Date(r.taklif_muddati!).getTime() < Date.now()
}

export function Reservations() {
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [holati, setHolati] = useState<NavbatHolati | ''>('')
  const [tasdiqlanadigan, setTasdiqlanadigan] = useState<Navbat | null>(null)
  const [bekorQilinadigan, setBekorQilinadigan] = useState<Navbat | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['reservations', page, holati],
    queryFn: () => reservationsApi.list({ page, holati: holati || undefined }),
  })

  const cancelMut = useMutation({
    mutationFn: (id: number) => reservationsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reservations'] })
      setBekorQilinadigan(null)
      toast.success('Navbat bekor qilindi va keyingisiga navbat yuborildi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const confirmMut = useMutation({
    mutationFn: (id: number) => reservationsApi.confirm(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reservations'] })
      qc.invalidateQueries({ queryKey: ['loans'] })
      qc.invalidateQueries({ queryKey: ['copies'] })
      setTasdiqlanadigan(null)
      toast.success('Navbat yakunlandi. Nusxa «mavjud» holatiga qaytarildi.')
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  const filtrBor = holati !== ''

  return (
    <div>
      <PageHeader title="Navbatlar" subtitle="Kitob mavjud bo'lmaganda o'quvchilar navbati" />

      <Card className="mb-4 p-3 sm:p-4">
        <div className="sm:w-64">
          <Select
            value={holati}
            onChange={(e) => {
              setHolati(e.target.value as NavbatHolati | '')
              setPage(1)
            }}
            aria-label="Navbat holati"
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(NAVBAT_HOLATI_LABELS).map(([value, label]) => (
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
          title="Navbatlarni yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {!isLoading && !isError && !data?.results.length && (
        <EmptyState
          icon={<Icons.clipboardList className="h-10 w-10" />}
          title={filtrBor ? 'Navbat topilmadi' : 'Navbat yo‘q'}
          description={
            filtrBor
              ? 'Boshqa holat filtrini tanlab ko‘ring.'
              : 'Barcha kitoblar mavjud — navbatlar shu yerda paydo bo‘ladi.'
          }
          action={
            filtrBor ? (
              <Button variant="secondary" size="sm" onClick={() => setHolati('')}>
                Filtrni tozalash
              </Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && !!data?.results.length && (
        <ResponsiveList<Navbat>
          items={data.results}
          render={(r) => {
            const javobBerilgan = r.holati === 'taklif_qilindi' && r.javob === 'olaman'
            return (
              <div className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-medium text-slate-900 dark:text-slate-100">
                      {r.kitob_nomi}
                    </div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                      {r.oquvchi_fish}
                    </div>
                  </div>
                  <Badge tone={TONE[r.holati]}>{NAVBAT_HOLATI_LABELS[r.holati]}</Badge>
                </div>

                {r.holati === 'taklif_qilindi' && r.javob && (
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Javob: <b>{NAVBAT_JAVOB_LABELS[r.javob]}</b>
                    {javobBerilgan && r.taklif_muddati && (
                      <>
                        {muddatiOtdi(r) ? ' • muddati o‘tgan' : ' • muddati bor'} ({formatDate(r.taklif_muddati)})
                      </>
                    )}
                  </div>
                )}

                {(r.holati === 'kutmoqda' || r.holati === 'taklif_qilindi') && (
                  <div className="mt-1 flex gap-2">
                    <Button
                      size="sm"
                      variant="danger"
                      className="flex-1"
                      onClick={() => setBekorQilinadigan(r)}
                    >
                      Bekor qilish
                    </Button>
                    <Button size="sm" className="flex-1" onClick={() => setTasdiqlanadigan(r)}>
                      Tasdiqlash
                    </Button>
                  </div>
                )}
              </div>
            )
          }}
        >
          <DataTable<Navbat>
            data={data.results}
            getRowId={(r) => r.id}
            emptyText="Navbat topilmadi"
            pagination={{
              count: data.count,
              page: page - 1,
              rowsPerPage: 20,
              onPageChange: (p) => setPage(p + 1),
            }}
            columns={
              [
                {
                  id: 'kitob',
                  label: 'Kitob',
                  sortBy: (r) => r.kitob_nomi,
                  render: (r) => (
                    <div className="font-medium text-slate-900 dark:text-slate-100">
                      {r.kitob_nomi}
                    </div>
                  ),
                },
                {
                  id: 'oquvchi',
                  label: "O'quvchi",
                  sortBy: (r) => r.oquvchi_fish,
                },
                {
                  id: 'navbat_sanasi',
                  label: 'Navbat sanasi',
                  sortBy: (r) => r.navbat_sanasi,
                  render: (r) => formatDate(r.navbat_sanasi),
                },
                {
                  id: 'holati',
                  label: 'Holati',
                  sortBy: (r) => r.holati,
                  render: (r) => <Badge tone={TONE[r.holati]}>{NAVBAT_HOLATI_LABELS[r.holati]}</Badge>,
                },
                {
                  id: 'javob',
                  label: 'Taklif javobi',
                  sortBy: (r) => r.javob ?? '',
                  render: (r) => {
                    const javobBerilgan = r.holati === 'taklif_qilindi' && r.javob === 'olaman'
                    return r.javob ? (
                      <>
                        <Badge tone={r.javob === 'olaman' ? 'green' : 'red'}>
                          {NAVBAT_JAVOB_LABELS[r.javob]}
                        </Badge>
                        {javobBerilgan && r.taklif_muddati && (
                          <div
                            className={`mt-1 text-xs ${muddatiOtdi(r) ? 'text-amber-600 dark:text-amber-400' : 'text-slate-400'}`}
                          >
                            {muddatiOtdi(r) ? 'Muddati o‘tgan' : 'Muddati bor'}:{' '}
                            {formatDate(r.taklif_muddati)}
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-slate-400 dark:text-slate-500">—</span>
                    )
                  },
                },
                {
                  id: 'amallar',
                  label: '',
                  sortable: false,
                  align: 'right',
                  render: (r) =>
                    (r.holati === 'kutmoqda' || r.holati === 'taklif_qilindi') && (
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => setBekorQilinadigan(r)}
                          disabled={cancelMut.isPending}
                        >
                          Bekor qilish
                        </Button>
                        <Button size="sm" onClick={() => setTasdiqlanadigan(r)}>
                          Tasdiqlash
                        </Button>
                      </div>
                    ),
                },
              ] as DataTableColumn<Navbat>[]
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

      <ConfirmDialog
        open={!!tasdiqlanadigan}
        title="Navbatni tasdiqlash"
        confirmLabel="Tasdiqlash"
        loading={confirmMut.isPending}
        message={
          tasdiqlanadigan && (
            <>
              <b>{tasdiqlanadigan.kitob_nomi}</b> kitobini{' '}
              <b>{tasdiqlanadigan.oquvchi_fish}</b>ga berdingizmi? Navbat yakunlanadi va ajratilgan
              nusxa «mavjud» holatiga qaytariladi.
            </>
          )
        }
        onConfirm={() => tasdiqlanadigan && confirmMut.mutate(tasdiqlanadigan.id)}
        onCancel={() => setTasdiqlanadigan(null)}
      />

      <ConfirmDialog
        open={!!bekorQilinadigan}
        title="Navbatni bekor qilish"
        variant="danger"
        confirmLabel="Bekor qilish"
        loading={cancelMut.isPending}
        message={
          bekorQilinadigan && (
            <>
              <b>{bekorQilinadigan.oquvchi_fish}</b> navbatini bekor qilmoqchimisiz? Keyingi navbatdagi
              o‘quvchiga taklif yuboriladi.
              {bekorQilinadigan.holati === 'taklif_qilindi' && bekorQilinadigan.javob === 'olaman' && (
                <>
                  <br />
                  <br />
                  O‘quvchi «olaman» deb javob bergan — navbatni bekor qilish undan voz kechishni
                  nazarda tutadi.
                </>
              )}
            </>
          )
        }
        onConfirm={() => bekorQilinadigan && cancelMut.mutate(bekorQilinadigan.id)}
        onCancel={() => setBekorQilinadigan(null)}
      />
    </div>
  )
}
