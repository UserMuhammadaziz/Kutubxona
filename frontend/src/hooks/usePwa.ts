import { useCallback, useEffect, useRef, useState } from 'react'

/** Chromium'ning `beforeinstallprompt` hodisasi (lib.dom'da yo'q). */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'kutubxona-install-dismissed'
const DESKTOP_DISMISS_KEY = 'kutubxona-desktop-hint-dismissed'

function isStandalone(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function isIos(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

function sessionFlag(key: string): boolean {
  try {
    return sessionStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

/**
 * Android "Kompyuter ko'rinishi" rejimini aniqlaydi.
 * Faqat sensorli qurilmada, PWA sifatida ochilganda va layout viewport
 * qurilma (visual) viewport'idan keng bo'lganda ogohlantiramiz — kichik
 * desktop oynalari endi noto'g'ri aniqlanmaydi. Ba'zi Android versiyalarida
 * screen.width ham 980 bo'ladi, shuning uchun sahifa masshtabi (scale < 1)
 * ham qo'shimcha belgi sifatida ishlatiladi.
 */
function isDesktopMode(): boolean {
  if (!isStandalone()) return false
  if (typeof window.matchMedia !== 'function' || !window.matchMedia('(pointer: coarse)').matches) {
    return false
  }
  const layoutWidth = document.documentElement.clientWidth || window.innerWidth
  const visualWidth = window.visualViewport?.width ?? window.innerWidth
  const scale = window.visualViewport?.scale ?? 1
  return layoutWidth > 760 && (layoutWidth > visualWidth * 1.2 || scale < 0.85)
}

/** PWA holati: o'rnatish taklifi, internet borligi, yangi versiya mavjudligi. */
export function usePwa() {
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [online, setOnline] = useState(() => navigator.onLine)
  const [updateReady, setUpdateReady] = useState<ServiceWorkerRegistration | null>(null)
  const [desktopMode, setDesktopMode] = useState(false)
  const [desktopDismissed, setDesktopDismissed] = useState(() => sessionFlag(DESKTOP_DISMISS_KEY))
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(DISMISS_KEY) === '1'
    } catch {
      return false
    }
  })

  // Yangilanishni faqat bir marta qo'llaymiz: bir nechta bosish / bir nechta
  // controllerchange hodisasi ikki marta reload qilmasligi kerak.
  const applyingRef = useRef(false)
  const applyTimerRef = useRef<number | null>(null)
  const pollTimerRef = useRef<number | null>(null)

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
      setDesktopMode(isDesktopMode())
    }
    check()
    window.addEventListener('resize', check)
    window.addEventListener('orientationchange', check)
    window.addEventListener('pageshow', check)
    const vv = window.visualViewport
    vv?.addEventListener('resize', check)
    return () => {
      window.removeEventListener('resize', check)
      window.removeEventListener('orientationchange', check)
      window.removeEventListener('pageshow', check)
      vv?.removeEventListener('resize', check)
    }
  }, [])

  // Yangi service worker o'rnatilib, eskisi hali boshqarib turganda — yangilanish bor.
  // Barcha obunachilar nomli va cleanup orqali o'chiriladi (StrictMode xavfsiz).
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return
    let cancelled = false
    const cleanups: Array<() => void> = []

    const onControllerChange = () => {
      if (!applyingRef.current) {
        // Boshqa tab yangilagan bo'lsa, eskirgan «Yangilash» eslatmasini o'chiramiz.
        setUpdateReady(null)
        return
      }
      applyingRef.current = false
      // Yangi worker boshqaruvni olgandan keyin faqat bir marta yangilaymiz.
      window.location.reload()
    }
    navigator.serviceWorker.addEventListener('controllerchange', onControllerChange)
    cleanups.push(() => navigator.serviceWorker.removeEventListener('controllerchange', onControllerChange))

    void navigator.serviceWorker
      .getRegistration()
      .then((reg) => {
        if (!reg || cancelled) return

        const checkWaiting = () => {
          if (reg.waiting && navigator.serviceWorker.controller) setUpdateReady(reg)
        }
        const poll = () => void reg.update().catch(() => undefined)

        pollTimerRef.current = window.setInterval(poll, 5 * 60_000)
        const onVisibility = () => {
          if (document.visibilityState === 'visible') poll()
        }
        document.addEventListener('visibilitychange', onVisibility)

        const onInstallingStateChange = () => checkWaiting()
        const onUpdateFound = () => {
          const installing = reg.installing
          if (!installing) return
          installing.addEventListener('statechange', onInstallingStateChange)
          cleanups.push(() => installing.removeEventListener('statechange', onInstallingStateChange))
        }
        reg.addEventListener('updatefound', onUpdateFound)

        cleanups.push(() => {
          document.removeEventListener('visibilitychange', onVisibility)
          reg.removeEventListener('updatefound', onUpdateFound)
          if (pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current)
            pollTimerRef.current = null
          }
        })

        checkWaiting()
        poll()
      })
      .catch(() => undefined)

    return () => {
      cancelled = true
      cleanups.forEach((cleanup) => cleanup())
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

  const dismissDesktopMode = useCallback(() => {
    setDesktopDismissed(true)
    try {
      sessionStorage.setItem(DESKTOP_DISMISS_KEY, '1')
    } catch {
      /* sessionStorage taqiqlangan — faqat shu render yashiriladi */
    }
  }, [])

  const applyUpdate = useCallback(() => {
    if (applyingRef.current || !updateReady?.waiting || !navigator.serviceWorker.controller) return
    applyingRef.current = true
    if (applyTimerRef.current !== null) {
      window.clearInterval(applyTimerRef.current)
      applyTimerRef.current = null
    }
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
    try {
      updateReady.waiting.postMessage({ type: 'SKIP_WAITING' })
    } catch {
      applyingRef.current = false
    }
    // Reload controllerchange ichida qilinadi — eski worker hali boshqarib
    // turgan paytda reload qilsak, update yana takrorlanaveradi.
  }, [updateReady])

  // Yangilanish tayyor bo'lishi bilan avtomatik o'tamiz, lekin foydalanuvchi
  // forma to'ldirayotgan yoki oyna ochiq bo'lsa, yozganlari yo'qolmasligi uchun kutamiz.
  useEffect(() => {
    if (!updateReady || applyingRef.current) return
    const busy = () => {
      const el = document.activeElement
      const typing = el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement
      return typing || !!document.querySelector('[role="dialog"]')
    }
    const tryApply = () => {
      if (!busy()) applyUpdate()
    }
    tryApply()
    if (applyingRef.current) return
    applyTimerRef.current = window.setInterval(() => {
      if (applyingRef.current) {
        if (applyTimerRef.current !== null) window.clearInterval(applyTimerRef.current)
        applyTimerRef.current = null
        return
      }
      tryApply()
    }, 3000)
    return () => {
      if (applyTimerRef.current !== null) {
        window.clearInterval(applyTimerRef.current)
        applyTimerRef.current = null
      }
    }
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
    desktopMode: desktopMode && !desktopDismissed,
    dismissDesktopMode,
  }
}
