import { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import clsx from 'clsx'
import { PageHeader } from '../components/ui'
import { AuditTab } from './platform/AuditTab'
import { HealthTab } from './platform/HealthTab'
import { OrganizationsTab } from './platform/OrganizationsTab'
import { PlansTab } from './platform/PlansTab'

const TABS = [
  ['organizations', 'Tashkilotlar'],
  ['plans', 'Tariflar'],
  ['health', 'Tizim holati'],
  ['audit', 'Harakatlar jurnali'],
] as const

type Tab = (typeof TABS)[number][0]

export function Platform() {
  const [params, setParams] = useSearchParams()
  const list = useRef<HTMLDivElement>(null)
  const tab: Tab = TABS.find(([key]) => key === params.get('tab'))?.[0] ?? 'organizations'
  const plan = params.get('plan') ?? ''

  const go = (next: Tab, planCode = '') =>
    setParams({ ...(next === 'organizations' ? {} : { tab: next }), ...(planCode ? { plan: planCode } : {}) })

  // On narrow screens the tab row scrolls: keep the open tab in view.
  useEffect(() => {
    list.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [tab])

  function onKeyDown(e: React.KeyboardEvent) {
    const i = TABS.findIndex(([key]) => key === tab)
    const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: TABS.length - 1 }[e.key]
    if (next === undefined) return
    e.preventDefault()
    const key = TABS[(next + TABS.length) % TABS.length][0]
    go(key)
    document.getElementById(`platform-tab-${key}`)?.focus()
  }

  return (
    <div>
      <PageHeader title="Platforma" subtitle="Tashkilotlar, tariflar va obunalar" />
      <div
        ref={list}
        role="tablist"
        aria-label="Platforma bo'limlari"
        onKeyDown={onKeyDown}
        className="-mx-4 mb-5 flex gap-1 overflow-x-auto border-b border-slate-200 px-4 sm:mx-0 sm:px-0 dark:border-slate-700"
      >
        {TABS.map(([key, label]) => (
          <button
            key={key}
            id={`platform-tab-${key}`}
            type="button"
            role="tab"
            aria-selected={tab === key}
            aria-controls="platform-panel"
            tabIndex={tab === key ? 0 : -1}
            onClick={() => go(key)}
            className={clsx(
              'shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors',
              tab === key
                ? 'border-brand-600 text-brand-700 dark:border-brand-400 dark:text-brand-300'
                : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100',
            )}
          >
            {label}
          </button>
        ))}
      </div>
      <div id="platform-panel" role="tabpanel" aria-labelledby={`platform-tab-${tab}`}>
        {tab === 'organizations' && <OrganizationsTab plan={plan} onPlanChange={(code) => go('organizations', code)} />}
        {tab === 'plans' && <PlansTab onShowOrganizations={(code) => go('organizations', code)} />}
        {tab === 'health' && <HealthTab />}
        {tab === 'audit' && <AuditTab />}
      </div>
    </div>
  )
}
