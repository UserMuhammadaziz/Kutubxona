import { usePwa } from '../hooks/usePwa'
import { Button } from './ui'

/** Offline holat, yangi versiya va «ilova sifatida o'rnatish» takliflari. */
export function PwaBanner() {
  const { online, canInstall, showIosHint, install, dismiss, updateReady, applyUpdate } = usePwa()

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-20 z-40 flex flex-col items-center gap-2 px-4 lg:bottom-4">
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
  )
}
