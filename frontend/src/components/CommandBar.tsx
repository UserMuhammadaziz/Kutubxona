import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api, errorMessage } from '../api/client'
import { loansApi } from '../api/resources'
import type { Berish } from '../types'
import { Icons } from './icons'
import { useAuthStore, isAdmin } from '../store/auth'
import { matchSections } from '../lib/sections'
import { Reminders } from './Reminders'
import { useToast } from './Toast'

type Payload = Record<string, string | undefined>

interface AiCommand {
  action: string
  payload: Payload
  summary: string
}

const EXAMPLES = [
  '9-A sinf o‘quvchisi Aliyev Jasurga Boburnoma kitobini ber',
  '3402-nusxani qaytarib ol',
  'Muddati o‘tgan kitoblarni ko‘rsat',
]

/** Brauzerning ovozni tanish interfeysi (hamma brauzerda ham yo'q). */
type SpeechRec = { lang: string; onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null; onend: (() => void) | null; start: () => void }
function speechCtor(): (new () => SpeechRec) | null {
  const w = window as unknown as { SpeechRecognition?: new () => SpeechRec; webkitSpeechRecognition?: new () => SpeechRec }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

/** Ctrl+K: tabiiy tildagi buyruq → AI → interfeysdagi tegishli amal. */
export function CommandBar() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [listening, setListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Qaytarishni tasdiqlash uchun topilgan faol berishlar.
  const [matches, setMatches] = useState<Berish[] | null>(null)
  const [sel, setSel] = useState(0)
  const admin = isAdmin(useAuthStore((st) => st.user))
  // 1–2 xonali raqam + Enter: ro'yxatdagi shu raqamli bo'lim ochiladi.
  const raqam = /^\d{1,2}$/.test(text.trim()) ? Number(text.trim()) : null
  const sections = matchSections(raqam ? '' : text, admin)
  const inputRef = useRef<HTMLInputElement>(null)

  const close = useCallback(() => {
    setOpen(false)
    setText('')
    setError(null)
    setMatches(null)
  }, [])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((o) => !o)
      } else if (e.key === 'Escape') {
        close()
      }
    }
    // Shtrix-kod skaneri klaviatura kabi tez yozib Enter bosadi: kodni panelga olamiz.
    let buf = ''
    let last = 0
    function onScan(e: KeyboardEvent) {
      const t = e.target as HTMLElement
      if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT') return
      const now = Date.now()
      if (now - last > 50) buf = ''
      last = now
      if (e.key === 'Enter' && buf.length >= 4) {
        setText(buf)
        setOpen(true)
        buf = ''
      } else if (e.key.length === 1) buf += e.key
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('keydown', onScan)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('keydown', onScan)
    }
  }, [close])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function prepareReturn(p: Payload) {
    const inv = p.inventory_number?.toLowerCase()
    const who = p.reader_query?.toLowerCase()
    const { results } = await loansApi.list({ holati: 'faol' })
    const found = results.filter(
      (b) =>
        (inv && b.inventar_raqami?.toLowerCase() === inv) ||
        (!inv && who && b.oquvchi_fish.toLowerCase().includes(who)),
    )
    if (!found.length) {
      setError('Mos faol berish topilmadi.')
      return
    }
    setMatches(found)
  }

  async function run(cmd: AiCommand) {
    const p = cmd.payload
    const go = (url: string) => {
      navigate(url)
      close()
    }
    const q = (v?: string) => encodeURIComponent(v ?? '')
    switch (cmd.action) {
      case 'SEARCH_READER':
        return go(`/readers?q=${q(p.query)}`)
      case 'SEARCH_BOOK':
        return go(`/books?q=${q(p.query)}`)
      case 'ISSUE_BOOK':
        return go(`/loans?berish=1&reader=${q(p.reader_query)}&book=${q(p.book_title)}`)
      case 'RETURN_BOOK':
        return prepareReturn(p)
      case 'APPROVE_HOLD':
        return go('/bandlar')
      case 'SHOW_OVERDUE':
        return go('/loans?kechikkan=1')
      default:
        setError(cmd.summary || 'Buyruq tushunarsiz. Qayta aytib ko‘ring.')
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (busy) return
    // Matn bo'lim nomiga mos kelsa — AI'siz to'g'ridan-to'g'ri o'tamiz.
    const bolim = raqam ? sections[raqam - 1] : sections[Math.min(sel, sections.length - 1)]
    if (raqam && !bolim) {
      setError(`${raqam}-bo‘lim yo‘q (1–${sections.length}).`)
      return
    }
    if (bolim) {
      navigate(bolim.to)
      close()
      return
    }
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    setMatches(null)
    try {
      const { data } = await api.post<AiCommand>('/ai/librarian-command/', { prompt: text })
      await run(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function confirmReturn(b: Berish) {
    setBusy(true)
    try {
      const res = await loansApi.return(b.id)
      for (const k of ['loans', 'copies', 'fines', 'reservations']) qc.invalidateQueries({ queryKey: [k] })
      toast.success(res.jarima_summasi ? `Qaytarildi. Jarima: ${res.jarima_summasi}` : 'Kitob qaytarildi.')
      close()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function startVoice() {
    const Ctor = speechCtor()
    if (!Ctor) {
      setError('Brauzer ovozli kiritishni qo‘llamaydi.')
      return
    }
    const rec = new Ctor()
    rec.lang = 'uz-UZ'
    rec.onresult = (e) => setText(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    setListening(true)
    rec.start()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[15vh]" role="dialog" aria-label="AI buyruqlar paneli">
      <div className="absolute inset-0 bg-slate-900/50 dark:bg-slate-950/70" onClick={close} />
      <div className="relative w-full max-w-xl rounded-xl bg-paper p-4 shadow-xl dark:bg-slate-800">
        <form onSubmit={onSubmit} className="flex items-center gap-2">
          <input
            ref={inputRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value)
              setSel(0)
            }}
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault()
                const d = e.key === 'ArrowDown' ? 1 : -1
                setSel((i) => (i + d + sections.length) % Math.max(sections.length, 1))
              }
            }}
            maxLength={300}
            placeholder="Buyruq yozing yoki ayting…"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-transparent px-3 py-2.5 text-sm text-slate-900 dark:border-slate-600 dark:text-slate-100"
          />
          {speechCtor() && (
            <button
              type="button"
              onClick={startVoice}
              aria-label="Ovoz bilan kiritish"
              className={`rounded-lg px-3 py-2.5 text-sm ${listening ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200'}`}
            >
              {listening ? '●' : 'Ovoz'}
            </button>
          )}
          <button
            type="submit"
            disabled={busy || !text.trim()}
            className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? '…' : 'Bajar'}
          </button>
        </form>

        <Reminders onNavigate={close} />

        {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

        {matches && (
          <ul className="mt-3 space-y-2">
            {matches.map((b) => (
              <li key={b.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-700">
                <span className="min-w-0 text-slate-800 dark:text-slate-100">
                  <b>{b.kitob_nomi}</b> ({b.inventar_raqami || 'asli'}) — {b.oquvchi_fish}
                </span>
                <button
                  autoFocus={matches.length === 1}
                  onClick={() => void confirmReturn(b)}
                  disabled={busy}
                  className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-white disabled:opacity-50"
                >
                  Qaytarish
                </button>
              </li>
            ))}
          </ul>
        )}

        {!matches && sections.length > 0 && (
          <ul className="mt-3 max-h-64 overflow-y-auto" role="listbox" aria-label="Bo‘limlar">
            {sections.map((b, i) => (
              <li key={b.to} role="option" aria-selected={raqam ? i === raqam - 1 : i === sel}>
                <button
                  type="button"
                  ref={(el) => {
                    if (el && i === sel) el.scrollIntoView({ block: 'nearest' })
                  }}
                  onMouseEnter={() => setSel(i)}
                  onClick={() => {
                    navigate(b.to)
                    close()
                  }}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm ${(raqam ? i === raqam - 1 : i === sel) ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300' : 'text-slate-700 dark:text-slate-200'}`}
                >
                  <span className="mr-2 inline-block w-5 text-slate-400">{i + 1}</span>
                  {b.label}
                </button>
              </li>
            ))}
          </ul>
        )}

        {!matches && !error && sections.length === 0 && (
          <ul className="mt-3 space-y-1 text-xs text-slate-500 dark:text-slate-400">
            {EXAMPLES.map((x) => (
              <li key={x}>
                <button type="button" onClick={() => setText(x)} className="text-left hover:underline">
                  {x}
                </button>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 flex items-center gap-1 text-[11px] text-slate-400">
          {Icons.search({ className: 'h-3.5 w-3.5' })} Ctrl+K — ochish/yopish · ↑↓ + Enter yoki raqam + Enter — bo‘limga o‘tish · Esc — yopish
        </p>
      </div>
    </div>
  )
}
