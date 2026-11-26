import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { toJpeg } from 'html-to-image'
import { api, errorMessage } from '../api/client'
import { Icons } from './icons'
import { Button, ErrorBanner, Field, Label, Modal, Select, Textarea } from './ui'
import { useToast } from './Toast'
import {
  detectCategory,
  detectModule,
  getConsoleErrors,
  getFailedRequests,
  type ConsoleEntry,
  type FailedRequest,
  type IssueCategory,
} from '../lib/diagnostics'

const CATEGORY_LABELS: Record<IssueCategory, string> = {
  bug: 'Xatolik',
  validation: 'Forma / ma’lumot xatosi',
  performance: 'Sekin ishlash',
  other: 'Boshqa',
}

const MODULE_LABELS: Record<string, string> = {
  auth: 'Kirish / autentifikatsiya',
  books: 'Kitoblar',
  copies: 'Nusxalar',
  readers: 'O‘quvchilar',
  loans: 'Berish / Qaytarish',
  fines: 'Jarimalar',
  reservations: 'Navbat / Band',
  announcements: 'E’lonlar',
  staff: 'Xodimlar',
  telegram: 'Telegram bot',
  dashboard: 'Boshqaruv paneli',
  organization: 'Tashkilot',
  other: 'Boshqa',
}

/** Sidebar-bottom button: grabs a screenshot, auto-detects category/module and attaches console errors. */
export function ReportIssueButton({ onOpen }: { onOpen?: () => void }) {
  const { pathname } = useLocation()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState<IssueCategory>('other')
  const [moduleName, setModuleName] = useState('other')
  const [message, setMessage] = useState('')
  const [screenshot, setScreenshot] = useState('')
  const [consoleErrors, setConsoleErrors] = useState<ConsoleEntry[]>([])
  const [failed, setFailed] = useState<FailedRequest[]>([])

  async function start() {
    onOpen?.()
    setBusy(true)
    setError(null)
    setMessage('')
    // Snapshot diagnostics and screenshot BEFORE the dialog opens.
    setConsoleErrors(getConsoleErrors())
    setFailed(getFailedRequests())
    setCategory(detectCategory())
    setModuleName(detectModule(pathname))
    try {
      setScreenshot(
        await toJpeg(document.body, {
          quality: 0.6,
          pixelRatio: Math.min(window.devicePixelRatio, 1),
          cacheBust: true,
          skipFonts: true,
          filter: (n) => !(n instanceof HTMLElement && n.dataset.noCapture !== undefined),
        }),
      )
    } catch {
      setScreenshot('')
    }
    setBusy(false)
    setOpen(true)
  }

  async function send() {
    setSending(true)
    setError(null)
    try {
      await api.post('/issue-reports/', {
        category,
        module: moduleName,
        message: message.trim(),
        page_url: window.location.href.slice(0, 500),
        user_agent: navigator.userAgent.slice(0, 300),
        console_errors: consoleErrors,
        failed_requests: failed,
        screenshot,
      })
      setOpen(false)
      toast.success('Xabar yuborildi. Rahmat!')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <button
        type="button"
        data-no-capture
        onClick={start}
        disabled={busy}
        className="mx-3 mb-3 flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-60 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        {Icons.alert({ className: 'h-4 w-4' })}
        {busy ? 'Tayyorlanmoqda...' : 'Muammo haqida xabar'}
      </button>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Muammo haqida xabar"
        description="Skrinshot va konsol xatolari avtomatik biriktiriladi."
      >
        <ErrorBanner message={error} />
        <Field>
          <Label htmlFor="r-module">Modul (avtomatik aniqlandi)</Label>
          <Select id="r-module" value={moduleName} onChange={(e) => setModuleName(e.target.value)}>
            {Object.entries(MODULE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
        </Field>
        <Field>
          <Label htmlFor="r-category">Tasnif (avtomatik aniqlandi)</Label>
          <Select id="r-category" value={category} onChange={(e) => setCategory(e.target.value as IssueCategory)}>
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
        </Field>
        <Field>
          <Label htmlFor="r-message">Nima bo‘ldi? (ixtiyoriy)</Label>
          <Textarea id="r-message" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} />
        </Field>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Biriktiriladi: {consoleErrors.length} ta konsol xatosi, {failed.length} ta muvaffaqiyatsiz so‘rov
          {screenshot ? ', skrinshot' : ''}.
        </p>
        {screenshot && (
          <img src={screenshot} alt="Skrinshot" className="mt-2 max-h-40 rounded-lg border border-slate-200 dark:border-slate-700" />
        )}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={() => setOpen(false)} disabled={sending}>
            Bekor qilish
          </Button>
          <Button type="button" onClick={send} loading={sending}>
            Yuborish
          </Button>
        </div>
      </Modal>
    </>
  )
}
