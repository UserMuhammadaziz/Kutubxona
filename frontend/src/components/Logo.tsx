interface LogoMarkProps {
  className?: string
}

/** Ilova belgisi — ochiq kitob va bookmark belgisi gradient kare ichida. */
export function LogoMark({ className = 'h-7 w-7' }: LogoMarkProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} role="img" aria-label="Kutubxona">
      <defs>
        <linearGradient id="logo-mark-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#9B5CFF" />
          <stop offset="0.55" stopColor="#863BFF" />
          <stop offset="1" stopColor="#5B15E0" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="url(#logo-mark-bg)" />
      <path
        d="M31 24.5C27.5 21.6 22.5 20.2 17 20v22.5c5.5-.2 10.5 1.2 14 4z"
        fill="#fff"
        fillOpacity=".96"
      />
      <path
        d="M33 24.5c3.5-2.9 8.5-4.3 14-4.5V42c-5.5.2-10.5 1.6-14 4.5z"
        fill="#fff"
        fillOpacity=".76"
      />
      <path d="M37 22.4h5V34l-2.5-2.8L37 34z" fill="#FBBF24" />
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
