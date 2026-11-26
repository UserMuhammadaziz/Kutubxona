import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { platformApi, type MarketingTouch, type PlatformOrgDetails } from '../../api/resources'
import { errorMessage } from '../../api/client'
import { Badge, ErrorState, Skeleton } from '../../components/ui'
import { formatDateTime } from '../../lib/format'
import { ORG_TYPE_LABELS } from '../../lib/organization'
import { actionLabel, auditDetail, mediumLabel, ORG_STATUS, sourceLabel, subscriptionSummary } from './shared'

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      {children}
    </section>
  )
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  if (children === '' || children == null) return null
  return (
    <div className="grid grid-cols-[8.5rem_1fr] gap-3 py-1 text-sm">
      <dt className="text-slate-600 dark:text-slate-300">{label}</dt>
      <dd className="min-w-0 break-words text-slate-900 dark:text-slate-100">{children}</dd>
    </div>
  )
}

/** "Telegram · ijtimoiy tarmoq · noyabr" */
function touchText(t: MarketingTouch) {
  return [sourceLabel(t.source), mediumLabel(t.medium), t.campaign].filter(Boolean).join(' · ')
}

type Event = { at: string; title: string; detail: string; who: string; kind: 'visit' | 'audit' | 'signup' }

/** Site visits, the signup and every recorded action in one chronological list. */
function buildEvents(d: PlatformOrgDetails): Event[] {
  const events: Event[] = [
    { at: d.organization.created_at, title: 'Ro‘yxatdan o‘tdi', detail: d.organization.name, who: d.owner?.full_name ?? '', kind: 'signup' },
  ]
  for (const v of d.attribution?.visits ?? []) {
    const where = [v.referrer_host && `${v.referrer_host} orqali`, v.landing_path && `sahifa: ${v.landing_path}`].filter(Boolean).join(', ')
    events.push({ at: v.created_at, title: `Saytga kirdi: ${touchText(v)}`, detail: where, who: '', kind: 'visit' })
  }
  for (const a of d.timeline) {
    // The signup row above already covers the registration request.
    if (a.action === 'organization.registration_requested') continue
    events.push({ at: a.created_at, title: actionLabel(a.action), detail: auditDetail({ ...a, organization_nomi: d.organization.name }), who: a.actor, kind: 'audit' })
  }
  return events.sort((x, y) => y.at.localeCompare(x.at))
}

const DOT: Record<Event['kind'], string> = {
  visit: 'bg-slate-400',
  signup: 'bg-brand-600',
  audit: 'bg-amber-500',
}

export function OrganizationDetails({ id, actions }: { id: number; actions?: ReactNode }) {
  const q = useQuery({ queryKey: ['platform', 'details', id], queryFn: () => platformApi.details(id) })

  if (q.isLoading)
    return (
      <div className="space-y-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    )
  if (q.isError || !q.data)
    return <ErrorState title="Yuklab bo‘lmadi" message={errorMessage(q.error)} onRetry={() => void q.refetch()} retrying={q.isFetching} />

  const d = q.data
  const o = d.organization
  const status = ORG_STATUS[o.status]
  const sub = d.subscription ? subscriptionSummary(d.subscription) : null
  const events = buildEvents(d)
  const u = d.usage

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={status?.tone}>{status?.label ?? o.status}</Badge>
        <span className="text-sm text-slate-600 dark:text-slate-300">
          {ORG_TYPE_LABELS[o.type] ?? o.type} · {o.slug} · {formatDateTime(o.created_at)} da ro‘yxatdan o‘tgan
        </span>
        {actions && <div className="ml-auto flex items-center gap-1">{actions}</div>}
      </div>
      {o.status_reason && (
        <p className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 dark:bg-slate-700/50 dark:text-slate-200">Sabab: {o.status_reason}</p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Egasi va aloqa">
          <dl>
            <Row label="Ism">{d.owner?.full_name || '—'}</Row>
            <Row label="Telefon">{d.owner?.phone ? <a className="text-brand-700 hover:underline dark:text-brand-300" href={`tel:${d.owner.phone}`}>{d.owner.phone}</a> : ''}</Row>
            <Row label="Login">{d.owner?.username ?? ''}</Row>
            <Row label="E-mail">{d.owner?.email || o.email}</Row>
            <Row label="Oxirgi kirish">{d.owner?.last_login ? formatDateTime(d.owner.last_login) : 'Hali kirmagan'}</Row>
            <Row label="Tashkilot tel.">{o.phone !== d.owner?.phone ? o.phone : ''}</Row>
            <Row label="Manzil">{o.address}</Row>
            <Row label="Tavsif">{o.description}</Row>
            <Row label="Tasdiqlagan">{o.approved_at ? `${o.approved_by || '—'}, ${formatDateTime(o.approved_at)}` : ''}</Row>
          </dl>
        </Section>

        <Section title="Qayerdan keldi">
          {d.attribution ? (
            <dl>
              <Row label="Birinchi manba">{touchText(d.attribution.first)}</Row>
              <Row label="Oxirgi manba">{touchText(d.attribution.last)}</Row>
              <Row label="Birinchi kirish">{d.attribution.first.at ? formatDateTime(d.attribution.first.at) : ''}</Row>
              <Row label="Kelgan sayt">{d.attribution.first.referrer_host}</Row>
              <Row label="Kirgan sahifa">{d.attribution.first.landing_path}</Row>
              <Row label="Kalit so‘z">{d.attribution.first.term}</Row>
              <Row label="Reklama ID">{d.attribution.first.click_id}</Row>
              <Row label="Tashriflar">{`${d.attribution.visits.length} ta`}</Row>
            </dl>
          ) : (
            <p className="text-sm text-slate-600 dark:text-slate-300">Manba yozilmagan: tashkilot kuzatuv yoqilishidan oldin yoki platforma tomonidan yaratilgan.</p>
          )}
        </Section>

        <Section title="Foydalanish">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1">
            {(
              [
                ['Kitoblar', u.books],
                ['Nusxalar', u.copies],
                ['Kitobxonlar', u.readers],
                ['Berishlar', u.loans],
                ['Qo‘lda', u.open_loans],
                ['Muddati o‘tgan', u.overdue_loans],
                ['Arizalar', u.pending_applications],
                ['Navbatlar', u.reservations],
              ] as const
            ).map(([label, value]) => (
              <div key={label} className="flex items-baseline justify-between gap-2 py-1 text-sm">
                <dt className="text-slate-600 dark:text-slate-300">{label}</dt>
                <dd className={clsx('font-medium tabular-nums text-slate-900 dark:text-slate-100', label === 'Muddati o‘tgan' && value > 0 && 'text-red-700 dark:text-red-400')}>{value}</dd>
              </div>
            ))}
          </dl>
          <dl className="mt-2 border-t border-slate-100 pt-2 dark:border-slate-700">
            <Row label="Obuna">{d.subscription ? `${d.subscription.plan_name}, ${sub?.text}` : 'Biriktirilmagan'}</Row>
            <Row label="Telegram bot">
              {d.bot ? (
                <>
                  @{d.bot.username || '—'} · {d.bot.status_display}
                  {d.bot.last_error && <div className="text-xs text-red-700 dark:text-red-400">{d.bot.last_error}</div>}
                </>
              ) : (
                'Ulanmagan'
              )}
            </Row>
            <Row label="Push obuna">{d.push_subscriptions ? `${d.push_subscriptions} ta brauzer` : 'Yo‘q'}</Row>
          </dl>
        </Section>

        <Section title={`Xodimlar (${d.members.length})`}>
          {d.members.length ? (
            <ul className="divide-y divide-slate-100 dark:divide-slate-700">
              {d.members.map((m) => (
                <li key={m.id} className={clsx('py-2 text-sm', !m.active && 'opacity-60')}>
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-medium text-slate-900 dark:text-slate-100">{m.full_name || m.username}</span>
                    <span className="text-xs text-slate-600 dark:text-slate-300">{m.role_display}{m.active ? '' : ' · nofaol'}</span>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-300">
                    {[m.username, m.telegram_linked && 'Telegram ulangan', m.last_login ? `oxirgi kirish ${formatDateTime(m.last_login)}` : 'hali kirmagan'].filter(Boolean).join(' · ')}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-600 dark:text-slate-300">Xodim yo‘q.</p>
          )}
        </Section>
      </div>

      <Section title="Hodisalar tarixi">
        <ol className="relative space-y-3 border-l border-slate-200 pl-5 dark:border-slate-700">
          {events.map((e, i) => (
            <li key={`${e.kind}-${e.at}-${i}`} className="relative text-sm">
              <span className={clsx('absolute top-1.5 -left-[1.6rem] h-2.5 w-2.5 rounded-full ring-4 ring-paper dark:ring-slate-800', DOT[e.kind])} aria-hidden />
              <div className="font-medium text-slate-900 dark:text-slate-100">{e.title}</div>
              {e.detail && <div className="break-words text-slate-600 dark:text-slate-300">{e.detail}</div>}
              <div className="text-xs text-slate-500 dark:text-slate-400">{formatDateTime(e.at)}{e.who ? ` · ${e.who}` : ''}</div>
            </li>
          ))}
        </ol>
      </Section>
    </div>
  )
}
