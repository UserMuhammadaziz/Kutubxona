import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { statsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Spinner } from '../components/ui'

type Tab = 'oquvchi' | 'oqituvchi'

function medalTone(orin: number): 'amber' | 'blue' | 'slate' {
  if (orin === 1) return 'amber'
  if (orin === 2) return 'blue'
  return 'slate'
}

function Progress({ ball }: { ball: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
      <div
        className="h-full rounded-full bg-brand-600"
        style={{ width: `${Math.max(0, Math.min(100, ball))}%` }}
      />
    </div>
  )
}

function RatingRow({
  orin,
  nomi,
  izoh,
  ball,
  readerId,
}: {
  orin: number
  nomi: string
  izoh: string
  ball: number
  readerId?: number
}) {
  return (
    <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-center gap-3">
        <Badge tone={medalTone(orin)}>#{orin}</Badge>
        <div className="min-w-0">
          {readerId !== undefined ? (
            <Link
              to={`/readers/${readerId}`}
              className="block truncate font-semibold text-brand-700 hover:underline dark:text-brand-400"
            >
              {nomi}
            </Link>
          ) : (
            <div className="truncate font-semibold text-slate-900 dark:text-slate-100">{nomi}</div>
          )}
          <div className="text-sm text-slate-500 dark:text-slate-400">{izoh}</div>
        </div>
      </div>
      <div className="w-full shrink-0 sm:w-48">
        <div className="mb-1 flex items-center justify-between text-sm">
          <span className="text-slate-500 dark:text-slate-400">Ball</span>
          <span className="font-semibold text-slate-900 dark:text-slate-100">{ball}</span>
        </div>
        <Progress ball={ball} />
      </div>
    </div>
  )
}

function ReytingBolimi({
  sarlavha,
  izoh,
  bor,
  boshqaSarlavha,
  boshqaIzoh,
  children,
}: {
  sarlavha: string
  izoh: string
  bor: boolean
  boshqaSarlavha: string
  boshqaIzoh: string
  children: ReactNode
}) {
  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{sarlavha}</h2>
      <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">{izoh}</p>
      {bor ? (
        <Card className="divide-y divide-slate-100 dark:divide-slate-700">{children}</Card>
      ) : (
        <Card className="p-4">
          <EmptyState
            icon={<Icons.inbox className="h-10 w-10" />}
            title={boshqaSarlavha}
            description={boshqaIzoh}
          />
        </Card>
      )}
    </section>
  )
}

export function Kitobxonlar() {
  const [tab, setTab] = useState<Tab>('oquvchi')
  const [sinfTanlov, setSinfTanlov] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['stats', 'faollik-reytingi'],
    queryFn: statsApi.faollikReytingi,
  })

  const sinflar = data?.sinflar ?? []
  const oqituvchilar = data?.oqituvchilar ?? []
  const faolOquvchilar = data?.faol_oquvchilar ?? []
  const faolOqituvchilar = data?.faol_oqituvchilar ?? []

  // "Faol sinf" tanlaganda o'quvchilar ro'yxati shu sinf bilan cheklanadi.
  const korsatiladiganOquvchilar = sinfTanlov
    ? faolOquvchilar.filter((o) => o.sinf === sinfTanlov)
    : faolOquvchilar

  return (
    <div>
      <PageHeader
        title="Kitobxonlar"
        subtitle={
          data?.organization
            ? `${data.organization.nomi} — sinflar, o'quvchilar va o'qituvchilar faolligi`
            : "Sinf, o'quvchi va o'qituvchilar faolligi"
        }
      />

      {/* Ikki tugma: o'quvchilar va o'qituvchilar */}
      <div className="mb-5 inline-flex rounded-xl border border-slate-200 bg-paper p-1 dark:border-slate-700 dark:bg-slate-800">
        <Button
          variant={tab === 'oquvchi' ? 'primary' : 'ghost'}
          onClick={() => setTab('oquvchi')}
          aria-pressed={tab === 'oquvchi'}
        >
          <Icons.graduationCap className="h-4 w-4" /> O‘quvchilar
        </Button>
        <Button
          variant={tab === 'oqituvchi' ? 'primary' : 'ghost'}
          onClick={() => setTab('oqituvchi')}
          aria-pressed={tab === 'oqituvchi'}
        >
          <Icons.user className="h-4 w-4" /> O‘qituvchilar
        </Button>
      </div>

      {isLoading && <Spinner label="Reyting yuklanmoqda..." />}

      {isError && (
        <ErrorState
          title="Reytingni yuklab bo‘lmadi"
          message={errorMessage(error)}
          onRetry={() => void refetch()}
          retrying={isFetching}
        />
      )}

      {data && (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Card className="p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Umumiy ball</div>
              <div className="mt-1 text-2xl font-semibold text-brand-600 dark:text-brand-400">
                {data.umumiy_bali}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Jami berishlar</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                {data.berishlar_soni}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">
                Hozirda kitob o‘qiyotganlar
              </div>
              <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                {data.faol_oquvchi_soni}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Qaytarilganlar</div>
              <div className="mt-1 text-2xl font-semibold text-green-600 dark:text-green-400">
                {data.qaytarilgan_soni}
              </div>
            </Card>
          </div>

          {tab === 'oquvchi' ? (
            <>
              <ReytingBolimi
                sarlavha="Faol sinflar"
                izoh="Bir sinf turli yozilishlarda bitta hisoblanadi. O'rin sinfdagi o'quvchilarning hozirgi kitob o'qish faolligiga qarab aniqlanadi."
                bor={sinflar.length > 0}
                boshqaSarlavha="Hali faol sinf yo‘q"
                boshqaIzoh="O‘quvchi qo‘shib, ularga sinf berilgach reyting paydo bo‘ladi."
              >
                {sinflar.map((s) => (
                  <RatingRow
                    key={s.sinf}
                    orin={s.o_rin}
                    nomi={`${s.sinf}-sinf`}
                    izoh={`${s.oquvchilar} o‘quvchi · ${s.faol_oquvchilar_soni} kitob o‘qiyapti · ${s.faol_berishlar} faol berish · ${s.qaytarilganlar} qaytarilgan`}
                    ball={s.ball}
                  />
                ))}
              </ReytingBolimi>

              <ReytingBolimi
                sarlavha="Faol o‘quvchilar"
                izoh="Hozirda qaytarilmagan kitoblari bor o‘quvchilar — kim ko‘p kitob o‘qiyotgani shu ro‘yxatda ko‘rinadi."
                bor={faolOquvchilar.length > 0}
                boshqaSarlavha="Hali kitob olgan o‘quvchi yo‘q"
                boshqaIzoh="Kitob berilgach, o‘quvchi bu ro‘yxatda ko‘rinadi."
              >
                <div className="border-b border-slate-100 p-3 dark:border-slate-700">
                  <div className="mb-2 text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
                    Faol sinf bo‘yicha
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant={sinfTanlov === '' ? 'primary' : 'ghost'}
                      onClick={() => setSinfTanlov('')}
                    >
                      Barcha sinflar
                    </Button>
                    {sinflar.map((s) => (
                      <Button
                        key={s.sinf}
                        size="sm"
                        variant={sinfTanlov === s.sinf ? 'primary' : 'ghost'}
                        onClick={() => setSinfTanlov(s.sinf)}
                      >
                        {s.sinf}-sinf
                      </Button>
                    ))}
                  </div>
                </div>
                {korsatiladiganOquvchilar.length ? (
                  korsatiladiganOquvchilar.map((o) => (
                    <RatingRow
                      key={o.id}
                      orin={o.o_rin}
                      nomi={o.fish}
                      izoh={`${o.sinf ? `${o.sinf}-sinf · ` : ''}hozirda ${o.faol_berishlar} kitob · jami ${o.jami_berishlar} berish`}
                      ball={o.ball}
                      readerId={o.id}
                    />
                  ))
                ) : (
                  <div className="p-4 text-sm text-slate-500 dark:text-slate-400">
                    Bu sinfda hozirda kitob o‘qiyotgan o‘quvchi yo‘q.
                  </div>
                )}
              </ReytingBolimi>
            </>
          ) : (
            <>
              <ReytingBolimi
                sarlavha="Faol o‘qituvchilar"
                izoh="Hozirda qaytarilmagan kitoblari bor o‘qituvchilar — kim ko‘p kitob o‘qiyotgani shu ro‘yxatda ko‘rinadi."
                bor={faolOqituvchilar.length > 0}
                boshqaSarlavha="Hali kitob olgan o‘qituvchi yo‘q"
                boshqaIzoh="O‘qituvchiga kitob berilgach, u bu ro‘yxatda ko‘rinadi."
              >
                {faolOqituvchilar.map((t) => (
                  <RatingRow
                    key={t.id}
                    orin={t.o_rin}
                    nomi={t.fish}
                    izoh={`${t.kasb || 'Fan ko‘rsatilmagan'} · hozirda ${t.faol_berishlar} kitob · jami ${t.jami_berishlar} berish`}
                    ball={t.ball}
                    readerId={t.id}
                  />
                ))}
              </ReytingBolimi>

              <ReytingBolimi
                sarlavha="O‘qituvchilar umumiy reytingi"
                izoh="Barcha berishlar va ularning qaytarilishlari bo'yicha tartiblangan."
                bor={oqituvchilar.length > 0}
                boshqaSarlavha="Hali o‘qituvchi yo‘q"
                boshqaIzoh="O‘qituvchi qo‘shilgach ularning reytingi shu yerda ko‘rinadi."
              >
                {oqituvchilar.map((t) => (
                  <RatingRow
                    key={t.id}
                    orin={t.o_rin}
                    nomi={t.fish}
                    izoh={`${t.kasb || 'Fan ko‘rsatilmagan'} · ${t.berishlar} berish · ${t.qaytarilganlar} qaytarilgan`}
                    ball={t.ball}
                    readerId={t.id}
                  />
                ))}
              </ReytingBolimi>
            </>
          )}
        </>
      )}
    </div>
  )
}
