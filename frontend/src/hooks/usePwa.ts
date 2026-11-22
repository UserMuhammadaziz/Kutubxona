import { useCallback, useEffect, useState } from 'react'

/** Chromium'ning `beforeinstallprompt` hodisasi (lib.dom'da yo'q). */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'kutubxona-install-dismissed'

function isStandalone(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function isIos(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

/** PWA holati: o'rnatish taklifi, internet borligi, yangi versiya mavjudligi. */
export function usePwa() {
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [online, setOnline] = useState(() => navigator.onLine)
  const [updateReady, setUpdateReady] = useState<ServiceWorkerRegistration | null>(null)
  // Android ba'zan PWA'ni "kompyuter ko'rinishi"da ochadi: sahifa 980px kenglikda
  // chizilib, butun interfeys kichrayib ketadi. Buni aniqlab, foydalanuvchiga
  // aniq ko'rsatma beramiz.
  const [desktopMode, setDesktopMode] = useState(false)
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(DISMISS_KEY) === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault()
      setInstallEvent(e as BeforeInstallPromptEvent)
    }
    const onInstalled = () => setInstallEvent(null)
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  // Viewport'ni har qayta ochilishda tasdiqlaymiz va kichrayish sababini aniqlaymiz.
  useEffect(() => {
    const check = () => {
      const meta = document.querySelector('meta[name="viewport"]')
      if (meta) meta.setAttribute('content', 'width=device-width, initial-scale=1.0, viewport-fit=cover')
      const phone = Math.min(screen.width, screen.height) < 600
      setDesktopMode(isStandalone() && phone && window.innerWidth > 760)
    }
    check()
    window.addEventListener('resize', check)
    window.addEventListener('orientationchange', check)
    window.addEventListener('pageshow', check)
    return () => {
      window.removeEventListener('resize', check)
      window.removeEventListener('orientationchange', check)
      window.removeEventListener('pageshow', check)
    }
  }, [])

  // Yangi service worker o'rnatilib, eskisi hali boshqarib turganda — yangilanish bor.
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return
    let cancelled = false
    let cleanup = () => {}
    void navigator.serviceWorker.getRegistration().then((reg) => {
      if (!reg || cancelled) return
      const check = () => {
        if (reg.waiting && navigator.serviceWorker.controller) setUpdateReady(reg)
      }
      check()
      // Yangi versiyani o'zimiz qidiramiz: ochilganda emas, vaqti-vaqti bilan va oynaga qaytilganda.
      const poll = () => void reg.update().catch(() => undefined)
      const timer = window.setInterval(poll, 5 * 60_000)
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') poll()
      })
      cleanup = () => window.clearInterval(timer)
      reg.addEventListener('updatefound', () => {
        reg.installing?.addEventListener('statechange', check)
      })
    })
    return () => {
      cancelled = true
      cleanup()
    }
  }, [])

  const install = useCallback(async () => {
    if (!installEvent) return
    await installEvent.prompt()
    await installEvent.userChoice
    setInstallEvent(null)
  }, [installEvent])

  const dismiss = useCallback(() => {
    setDismissed(true)
    try {
      localStorage.setItem(DISMISS_KEY, '1')
    } catch {
      /* private rejim — shunchaki shu sessiyada yashiriladi */
    }
  }, [])

  const applyUpdate = useCallback(() => {
    // Sahifa manzili va kirish tokeni (localStorage) reload'dan keyin ham saqlanadi.
    updateReady?.waiting?.postMessage({ type: 'SKIP_WAITING' })
    window.location.reload()
  }, [updateReady])

  // Yangilanish tayyor bo'lishi bilan avtomatik o'tamiz, lekin foydalanuvchi
  // forma to'ldirayotgan yoki oyna ochiq bo'lsa, yozganlari yo'qolmasligi uchun kutamiz.
  useEffect(() => {
    if (!updateReady) return
    const busy = () => {
      const el = document.activeElement
      const typing = el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement
      return typing || !!document.querySelector('[role="dialog"]')
    }
    const tryApply = () => {
      if (!busy()) applyUpdate()
    }
    tryApply()
    const timer = window.setInterval(tryApply, 3000)
    return () => window.clearInterval(timer)
  }, [updateReady, applyUpdate])

  const standalone = typeof window !== 'undefined' && isStandalone()
  return {
    online,
    canInstall: !!installEvent && !dismissed && !standalone,
    showIosHint: isIos() && !standalone && !dismissed,
    install,
    dismiss,
    updateReady: !!updateReady,
    applyUpdate,
    desktopMode,
  }
}
