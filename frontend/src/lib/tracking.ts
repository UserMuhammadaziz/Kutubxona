/**
 * Traffic source tracking (UTM tags, ad click ids, referrer).
 *
 * On every full page load we read the entry URL once: the first touch is kept
 * forever, the last touch is replaced whenever the visitor arrives from a new
 * campaign or another site. The server gets one visit per session and source,
 * and the signup request carries both touches.
 */
import axios from 'axios'

const VISITOR_KEY = 'kx-visitor'
const FIRST_KEY = 'kx-first-touch'
const LAST_KEY = 'kx-last-touch'
const SENT_KEY = 'kx-visit-sent'
const PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'yclid', 'fbclid'] as const

export type Touch = Partial<Record<(typeof PARAMS)[number], string>> & {
  visitor_id: string
  referrer?: string
  path: string
  at: string
}

function storage(kind: 'local' | 'session'): Storage | null {
  try {
    return kind === 'local' ? window.localStorage : window.sessionStorage
  } catch {
    return null
  }
}

function read(key: string): Touch | null {
  try {
    return JSON.parse(storage('local')?.getItem(key) ?? 'null')
  } catch {
    return null
  }
}

export function visitorId(): string {
  const store = storage('local')
  let id = store?.getItem(VISITOR_KEY) ?? ''
  if (!/^[A-Za-z0-9-]{8,40}$/.test(id)) {
    id = crypto.randomUUID?.() ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`
    store?.setItem(VISITOR_KEY, id)
  }
  return id
}

function externalReferrer(): string {
  try {
    const ref = document.referrer ? new URL(document.referrer) : null
    return ref && ref.host !== window.location.host ? ref.href.slice(0, 300) : ''
  } catch {
    return ''
  }
}

function currentTouch(): Touch {
  const query = new URLSearchParams(window.location.search)
  const touch: Touch = { visitor_id: visitorId(), path: window.location.pathname, at: new Date().toISOString() }
  for (const key of PARAMS) {
    const value = query.get(key)?.trim()
    if (value) touch[key] = value.slice(0, 120)
  }
  const referrer = externalReferrer()
  if (referrer) touch.referrer = referrer
  return touch
}

const isTagged = (t: Touch) => PARAMS.some((k) => t[k]) || Boolean(t.referrer)
const sourceKey = (t: Touch) => [t.utm_source, t.utm_medium, t.utm_campaign, t.gclid && 'g', t.yclid && 'y', t.fbclid && 'f', t.referrer && new URL(t.referrer).host].join('|')

/** Call once on app start. Never throws and never blocks rendering. */
export function captureVisit() {
  try {
    const touch = currentTouch()
    const local = storage('local')
    if (!read(FIRST_KEY)) local?.setItem(FIRST_KEY, JSON.stringify(touch))
    if (isTagged(touch) || !read(LAST_KEY)) local?.setItem(LAST_KEY, JSON.stringify(touch))

    // Only public pages count as marketing visits; signed-in app pages do not.
    const publicPage = ['/', '/welcome', '/register', '/login'].includes(touch.path)
    const session = storage('session')
    const key = sourceKey(touch)
    if (!publicPage && !isTagged(touch)) return
    if (session?.getItem(SENT_KEY) === key) return
    session?.setItem(SENT_KEY, key)
    // Plain axios: no auth header, no refresh/redirect logic of the app client.
    void axios.post('/api/marketing/visit/', touch, { timeout: 5000 }).catch(() => {})
  } catch {
    /* tracking must never break the page */
  }
}

/** First and last touch for the signup request. */
export function signupAttribution() {
  try {
    return { first: read(FIRST_KEY) ?? undefined, last: read(LAST_KEY) ?? undefined }
  } catch {
    return {}
  }
}
