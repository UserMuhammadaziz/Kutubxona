/*
 * Collects console errors, uncaught exceptions, unhandled rejections and failed
 * API requests in a small ring buffer so a problem report can attach them.
 */

export interface ConsoleEntry {
  level: 'error' | 'warn' | 'exception' | 'rejection'
  message: string
  at: string
}

export interface FailedRequest {
  method: string
  url: string
  status: number | null
  detail: string
  at: string
}

const MAX = 30
const consoleBuffer: ConsoleEntry[] = []
const requestBuffer: FailedRequest[] = []

function push<T>(buf: T[], item: T) {
  buf.push(item)
  if (buf.length > MAX) buf.shift()
}

function stringify(arg: unknown): string {
  if (arg instanceof Error) return `${arg.name}: ${arg.message}\n${(arg.stack ?? '').split('\n').slice(1, 4).join('\n')}`
  if (typeof arg === 'string') return arg
  try {
    return JSON.stringify(arg)
  } catch {
    return String(arg)
  }
}

let installed = false

export function installDiagnostics() {
  if (installed) return
  installed = true

  for (const level of ['error', 'warn'] as const) {
    const original = console[level].bind(console)
    console[level] = (...args: unknown[]) => {
      push(consoleBuffer, { level, message: args.map(stringify).join(' ').slice(0, 800), at: new Date().toISOString() })
      original(...args)
    }
  }
  window.addEventListener('error', (e) => {
    push(consoleBuffer, {
      level: 'exception',
      message: `${e.message} (${e.filename?.split('/').pop() ?? ''}:${e.lineno})`.slice(0, 800),
      at: new Date().toISOString(),
    })
  })
  window.addEventListener('unhandledrejection', (e) => {
    push(consoleBuffer, { level: 'rejection', message: stringify(e.reason).slice(0, 800), at: new Date().toISOString() })
  })
}

export function recordFailedRequest(r: Omit<FailedRequest, 'at'>) {
  push(requestBuffer, { ...r, at: new Date().toISOString() })
}

export const getConsoleErrors = () => [...consoleBuffer]
export const getFailedRequests = () => [...requestBuffer]

/** Maps an API URL or page path to a module name (auth, books, copies, ...). */
const MODULE_RULES: [RegExp, string][] = [
  [/\/(auth|login|register|password)/, 'auth'],
  [/\/(copies|nusxa)/, 'copies'],
  [/\/books/, 'books'],
  [/\/(readers|applications|subjects)/, 'readers'],
  [/\/loans/, 'loans'],
  [/\/fines/, 'fines'],
  [/\/(reservations|holds)/, 'reservations'],
  [/\/announcements/, 'announcements'],
  [/\/staff/, 'staff'],
  [/\/(telegram|bot)/, 'telegram'],
  [/\/(stats|dashboard)/, 'dashboard'],
  [/\/(organizations|saas)/, 'organization'],
]

export function moduleFromPath(path: string): string | null {
  for (const [re, name] of MODULE_RULES) if (re.test(path)) return name
  return null
}

/** Best guess: failed API requests first (most precise), then console text, then current page. */
export function detectModule(pathname: string): string {
  const reqs = getFailedRequests()
  for (let i = reqs.length - 1; i >= 0; i--) {
    const m = moduleFromPath(reqs[i].url)
    if (m) return m
  }
  const errs = getConsoleErrors()
  for (let i = errs.length - 1; i >= 0; i--) {
    const m = moduleFromPath(errs[i].message.toLowerCase())
    if (m) return m
  }
  return moduleFromPath(pathname) ?? 'other'
}

export type IssueCategory = 'bug' | 'validation' | 'performance' | 'other'

export function detectCategory(): IssueCategory {
  const reqs = getFailedRequests()
  if (getConsoleErrors().some((e) => e.level !== 'warn') || reqs.some((r) => r.status === null || r.status >= 500)) return 'bug'
  if (reqs.some((r) => r.status !== null && r.status >= 400)) return 'validation'
  return 'other'
}
