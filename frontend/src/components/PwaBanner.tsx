import { useState } from 'react'
import { usePwa } from '../hooks/usePwa'
import { Button } from './ui'

/** Offline holat, yangi versiya, «ilova sifatida o'rnatish» va kichrayish ogohlantirishi. */
export function PwaBanner() {
  const { online, canInstall, showIosHint, install, dismiss, updateReady, applyUpdate, desktopMode } =
    usePwa()
  const [desktopHintYopildi, setDesktopHintYopildi] = useState(false)

  return (
    <>
      <div className="pointer-events-none fixed inset-x-0 bottom-36 z-40 flex flex-col items-center gap-2 px-4 lg:bottom-4">
      {!online && (
        <div
          role="status"
          className="pointer-events-auto rounded-lg bg-slate-900 px-4 py-2 text-sm text-white shadow-lg dark:bg-slate-100 dark:text-slate-900"
        >
          Internet yo‘q — ma’lumotlar yangilanmaydi
        </div>
      )}
      {updateReady && (
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg bg-paper px-4 py-2 text-sm shadow-lg ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
          <span>Yangi versiya tayyor</span>
          <Button size="sm" onClick={applyUpdate}>
            Yangilash
          </Button>
        </div>
      )}
      {canInstall && (
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg bg-paper px-4 py-2 text-sm shadow-lg ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
          <span>Ilova sifatida o‘rnating</span>
          <Button size="sm" onClick={() => void install()}>
            O‘rnatish
          </Button>
          <button onClick={dismiss} className="text-slate-500 hover:text-slate-700 dark:text-slate-400">
            Keyin
          </button>
        </div>
      )}
      {showIosHint && !canInstall && (
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg bg-paper px-4 py-2 text-sm shadow-lg ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
          <span>Safari: «Ulashish» → «Bosh ekranga qo‘shish»</span>
          <button onClick={dismiss} className="text-slate-500 hover:text-slate-700 dark:text-slate-400">
            Yopish
          </button>
        </div>
      )}
      </div>

      {desktopMode && !desktopHintYopildi && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/70 p-5">
          <div className="w-full max-w-sm rounded-2xl bg-paper p-6 text-center shadow-2xl dark:bg-slate-800">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl dark:bg-amber-900/30">
              ⚠️
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Ilova kichik ko‘rinishda ochildi
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Brauzerda bu sayt uchun <b>«Kompyuter ko‘rinishi»</b> yoqilgan bo‘lishi mumkin. Chrome
              menyusidan u rejimni o‘chirib, ilovani yopib qayta oching — interfeys to‘liq ekranga
              moslashadi.
            </p>
            <div className="mt-5 flex flex-col gap-2">
              <Button onClick={() => window.location.reload()}>Qayta yuklash</Button>
              <Button variant="secondary" onClick={() => setDesktopHintYopildi(true)}>
                Tushundim
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
