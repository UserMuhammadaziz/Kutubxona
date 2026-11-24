import { CheckCircle2, ClipboardList, BellRing, ShieldCheck, Rocket } from 'lucide-react'
import { LogoMark } from './Logo'

const STEPS = [
  { icon: ClipboardList, title: 'Ariza yuborasiz', text: 'Tashkilot nomi va telefon raqami yetarli.' },
  { icon: ShieldCheck, title: 'Administrator tasdiqlaydi', text: 'Ariza ko‘rib chiqiladi, odatda tez.' },
  { icon: BellRing, title: 'Darhol xabar olasiz', text: 'Tasdiqlanganda brauzerga bildirishnoma keladi.' },
  { icon: Rocket, title: 'Kutubxonani sozlaysiz', text: 'Kitoblar, o‘quvchilar va Telegram botni ulaysiz.' },
]

/** Brand panel for the registration page: floating book spines and a step-by-step reveal. */
export function AuthAside() {
  const spines = [
    { x: 10, y: 60, w: 38, h: 200, d: 0 },
    { x: 56, y: 20, w: 44, h: 240, d: 120 },
    { x: 108, y: 80, w: 34, h: 180, d: 240 },
    { x: 150, y: 40, w: 48, h: 220, d: 360 },
    { x: 206, y: 100, w: 36, h: 160, d: 480 },
    { x: 250, y: 55, w: 52, h: 205, d: 600 },
  ]
  return (
    <aside className="relative flex flex-col justify-between overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 px-6 py-8 text-white sm:px-10 lg:px-14 lg:py-12">
      <div className="animate-float pointer-events-none absolute -bottom-6 -right-4">
        <svg aria-hidden="true" className="h-64 w-auto text-white/[0.08] lg:h-[26rem]" viewBox="0 0 320 260" fill="currentColor">
          {spines.map((s) => (
            <rect key={s.x} className="animate-spine" style={{ animationDelay: `${s.d}ms` }} x={s.x} y={s.y} width={s.w} height={s.h} rx="4" />
          ))}
        </svg>
      </div>

      <div className="animate-fade-up relative flex items-center gap-3">
        <LogoMark className="h-10 w-10 shadow-lg shadow-black/20" />
        <span className="text-lg font-semibold tracking-tight">Kutubxona</span>
      </div>

      <div className="relative my-10 max-w-lg lg:my-0">
        <h1 className="animate-fade-up font-['Cormorant_Garamond',serif] text-4xl font-semibold leading-[1.1] sm:text-5xl" style={{ animationDelay: '150ms' }}>
          Kutubxonangizni
          <br />
          bir necha daqiqada ulang.
        </h1>
        <ol className="mt-8 hidden space-y-5 sm:block">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="animate-fade-up flex gap-3" style={{ animationDelay: `${400 + i * 180}ms` }}>
              <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15 ${i === 0 ? 'animate-ring' : ''}`}>
                <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
              </span>
              <span>
                <span className="block text-sm font-semibold">
                  {i + 1}. {title}
                </span>
                <span className="block text-[13px] leading-snug text-brand-100/80">{text}</span>
              </span>
            </li>
          ))}
        </ol>
        <p className="animate-fade-up mt-8 hidden items-center gap-2 text-sm text-brand-100/90 sm:flex" style={{ animationDelay: '1200ms' }}>
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Bot tokenini keyin, kutubxona profilida ulaysiz.
        </p>
      </div>

      <p className="relative hidden text-xs text-brand-100/60 lg:block">© {new Date().getFullYear()} Kutubxona tizimi</p>
    </aside>
  )
}
