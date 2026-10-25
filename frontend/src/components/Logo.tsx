import { useId } from 'react'

interface LogoMarkProps {
  className?: string
}

/** Ilova belgisi — ochiq kitob va bookmark belgisi gradient kare ichida. */
export function LogoMark({ className = 'h-7 w-7' }: LogoMarkProps) {
  const gid = `logo-mark-bg-${useId().replace(/:/g, '')}`
  return (
    <svg viewBox="0 0 64 64" className={className} role="img" aria-label="Kutubxona">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#60A5FA" />
          <stop offset="0.55" stopColor="#2563EB" />
          <stop offset="1" stopColor="#1E40AF" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill={`url(#${gid})`} />
      <path
        d="M31 22.5C27 19 20 17.5 12 18v27.5c8-.5 15 1 19 4.5z"
        fill="#fff"
        fillOpacity=".96"
      />
      <path
        d="M33 22.5c4-3.5 11-5 19-4.5v27.5c-8-.5-15 1-19 4.5z"
        fill="#fff"
        fillOpacity=".76"
      />
      <path d="M40 18.2h6V32l-3-3-3 3z" fill="#FBBF24" />
    </svg>
  )
}

interface LogoProps {
  /** Matn bilan birga ko'rsatilsinmi (lockup). */
  withWordmark?: boolean
  markClassName?: string
  className?: string
}

/** Yagona brend lockup: belgi + «Kutubxona» matni. */
export function Logo({ withWordmark = true, markClassName, className }: LogoProps) {
  if (!withWordmark) return <LogoMark className={markClassName} />
  return (
    <span className={`flex items-center gap-2 ${className ?? ''}`}>
      <LogoMark className={markClassName ?? 'h-7 w-7'} />
      <span className="flex flex-col leading-none">
        <span className="text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">
          Kutubxona
        </span>
        <span className="mt-0.5 text-[9.5px] font-medium tracking-[0.16em] text-slate-500 uppercase dark:text-slate-400">
          Tuman kutubxonasi
        </span>
      </span>
    </span>
  )
}
