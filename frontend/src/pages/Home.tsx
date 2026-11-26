import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Icons } from '../components/icons'
import { useThemeStore } from '../store/theme'

/*
 * Landing (/welcome). Iliq bej fon, to'q yashil aksent, yumshoq burchaklar (16-24px),
 * bitta shrift. Imkoniyatlar bir xil kartalarda emas, turli o'lchamdagi mozaikada.
 * Skrinshotlar — dev serverdagi real ilovadan (namunaviy ma'lumotlar bilan).
 */

const FON = 'var(--l-bg)'
const QUM = 'var(--l-sand)'
const OQ = 'var(--l-card)'
const YASHIL = 'var(--l-green)'
const YASHIL_OCH = 'var(--l-accent)'
const INK = 'var(--l-ink)'
const SOYA = 'var(--l-muted)'
const SHRIFT: CSSProperties = { fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }

const btn = 'inline-flex min-h-12 items-center rounded-full px-6 text-base font-semibold'

function Tile({
  className = '',
  bg,
  color = INK,
  children,
}: {
  className?: string
  bg: string
  color?: string
  children: ReactNode
}) {
  return (
    <div className={'flex flex-col overflow-hidden rounded-[22px] p-6 ' + className} style={{ background: bg, color }}>
      {children}
    </div>
  )
}

// Bump when the files in public/landing are retaken: nginx caches them for days.
const SHOTS_VERSION = '2611'

/** App screenshot that follows the theme and swaps to a phone capture on small screens. */
function Screenshot({
  name,
  alt,
  width,
  height,
  className,
  lazy = false,
}: {
  name: 'panel' | 'loans'
  alt: string
  width: number
  height: number
  className: string
  lazy?: boolean
}) {
  const theme = useThemeStore((t) => t.theme)
  const suffix = `${theme === 'dark' ? 'dark' : 'light'}-${SHOTS_VERSION}.webp`
  return (
    <picture>
      <source
        media="(max-width: 639px)"
        srcSet={`/landing/${name}-mobile-${suffix}`}
        width={780}
        height={1560}
      />
      <img
        src={`/landing/${name}-${suffix}`}
        alt={alt}
        width={width}
        height={height}
        loading={lazy ? 'lazy' : undefined}
        className={`block h-auto w-full ${className}`}
      />
    </picture>
  )
}

export function Home() {
  const theme = useThemeStore((t) => t.theme)
  const toggleTheme = useThemeStore((t) => t.toggle)
  return (
    <div className="landing min-h-screen" style={{ ...SHRIFT, background: FON, color: INK }}>
      <header className="mx-auto flex h-20 max-w-6xl items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-1 sm:gap-2">
          <Link to="/yordam" className="hidden px-3 py-2 text-sm font-medium hover:underline md:block">
            Qo‘llanma
          </Link>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Yorug rejimga o‘tish' : 'Qorong‘i rejimga o‘tish'}
            className="rounded-full p-2.5 hover:bg-black/10 dark:hover:bg-white/10"
          >
            {theme === 'dark' ? Icons.sun({ className: 'h-5 w-5' }) : Icons.moon({ className: 'h-5 w-5' })}
          </button>
          <Link
            to="/login"
            className="whitespace-nowrap rounded-full border px-4 py-2 text-sm font-semibold"
            style={{ borderColor: 'var(--l-green-ink)', color: 'var(--l-green-ink)' }}
          >
            Tizimga kirish
          </Link>
          {/* Phones: the hero repeats this button right below, so the header keeps only login. */}
          <Link
            to="/register"
            className="hidden whitespace-nowrap rounded-full px-5 py-2.5 text-sm font-semibold text-white sm:block"
            style={{ background: YASHIL }}
          >
            Ro‘yxatdan o‘tish
          </Link>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 pt-10 sm:pt-16">
          <h1 className="max-w-4xl text-4xl font-bold leading-[1.06] tracking-tight sm:text-6xl">
            Kim qaysi kitobni olgani <span style={{ color: YASHIL_OCH }}>doim ko‘z oldingizda.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed sm:text-xl" style={{ color: SOYA }}>
            Kitob berish, qaytarish, muddat va jarima hisobi bir joyda. Daftar va Excel kerak emas. Hammasi o‘zbek
            tilida, kompyuter va telefonda ishlaydi.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register" className={btn + ' text-white'} style={{ background: YASHIL }}>
              Ro‘yxatdan o‘tish
            </Link>
          </div>

          <figure className="mt-12 overflow-hidden rounded-[24px] p-2 sm:p-3" style={{ background: QUM }}>
            <Screenshot
              name="panel"
              alt="Boshqaruv paneli: fond holati, muddati o‘tgan berishlar, jarimalar, so‘nggi harakatlar va muammo haqida xabar tugmasi"
              width={2560}
              height={1960}
              className="rounded-[16px]"
            />
          </figure>
        </section>

        {/* Raqamlar */}
        <section className="mx-auto mt-12 grid max-w-6xl gap-3 px-4 sm:grid-cols-3">
          {[
            ['2', 'muddati o‘tgan berish — panelda qizil raqam bilan ajralib turadi'],
            ['28', 'nusxa — qaysi biri javonda, qaysi biri o‘quvchida ko‘rinadi'],
            ['35 000 so‘m', 'to‘lanmagan jarima — kechikish bo‘yicha o‘zi hisoblanadi'],
          ].map(([n, m]) => (
            <div key={n} className="rounded-[22px] p-5" style={{ background: OQ }}>
              <div className="text-2xl font-bold sm:text-3xl">{n}</div>
              <p className="mt-1 text-sm leading-snug" style={{ color: SOYA }}>
                {m}
              </p>
            </div>
          ))}
        </section>

        {/* Mozaika */}
        <section className="mx-auto mt-24 max-w-6xl px-4">
          <h2 className="text-3xl font-bold sm:text-4xl">Kundalik ish uchun nimalar bor</h2>

          <div className="mt-8 grid gap-3 lg:grid-cols-6">
            <Tile bg={OQ} className="lg:col-span-4 lg:row-span-2">
              <h3 className="text-2xl font-bold sm:text-3xl">Berish va qaytarish</h3>
              <p className="mt-2 max-w-md text-base leading-relaxed" style={{ color: SOYA }}>
                O‘quvchini toping, kitobni tanlang, bering. Qaytganda qator oxiridagi tugmani bosasiz — nusxa
                javonga qaytadi.
              </p>
              <Screenshot
                name="loans"
                alt="Berish va qaytarish jadvali: kitob, kitobxon, berilgan sana, muddat, Qaytarish tugmasi"
                width={1958}
                height={1364}
                className="mt-5 rounded-[14px]"
                lazy
              />
            </Tile>

            <Tile bg={YASHIL} color="#fff" className="lg:col-span-2">
              <h3 className="text-xl font-bold">AI yordamchi</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: '#cfe5da' }}>
                Tizim haqida savol bersangiz, o‘zbekcha javob beradi. Ctrl+K bosib, oddiy gap bilan buyruq ham berishingiz mumkin.
              </p>
            </Tile>

            <Tile bg={QUM} className="lg:col-span-2">
              <h3 className="text-xl font-bold">Band va navbat</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                Kitob qo‘lda bo‘lsa, o‘quvchi navbatga turadi. Navbatdagilar sonini panelda ko‘rasiz.
              </p>
            </Tile>

            <Tile bg={QUM} className="lg:col-span-2">
              <h3 className="text-xl font-bold">Nusxalar</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                Har bir nusxaning inventar raqami bor. Qaysi biri javonda, qaysi biri qo‘lda — ro‘yxatda.
              </p>
            </Tile>

            <Tile bg={OQ} className="lg:col-span-2">
              <h3 className="text-xl font-bold">Jarimalar</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                Kechikish uchun jarima hisoblanadi. To‘langan va to‘lanmagan summa alohida turadi.
              </p>
            </Tile>

            <Tile bg={OQ} className="lg:col-span-2">
              <h3 className="text-xl font-bold">O‘quvchi va o‘qituvchilar</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                Ikkalasi alohida ro‘yxatda. O‘qituvchilar Telegram bot orqali ariza yuboradi, siz tasdiqlaysiz.
              </p>
            </Tile>

            <Tile bg={QUM} className="lg:col-span-6">
              <h3 className="text-xl font-bold">Kutubxonalar alohida</h3>
              <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                Har bir kutubxonaning ma’lumoti boshqalarnikidan ajratilgan. Maktab, universitet, mahalla
                kutubxonasi yoki ofis kutubxonasi bo‘lishi mumkin.
              </p>
            </Tile>
          </div>
        </section>

        {/* Boshlash */}
        <section className="mx-auto mt-24 max-w-6xl px-4">
          <h2 className="text-3xl font-bold sm:text-4xl">Boshlash</h2>
          <ol className="mt-8 grid gap-3 md:grid-cols-3">
            {[
              ['Ro‘yxatdan o‘ting', 'Kutubxona nomi va turini kiriting.'],
              ['Kitoblarni kiriting', 'Kitob va nusxalarni qo‘shing. O‘quvchilar Telegram bot orqali o‘zlari ariza yuboradi.'],
              ['Kitob bera boshlang', 'Qo‘llanma tizim ichida. Savol bo‘lsa, AI yordamchidan so‘rang.'],
            ].map(([n, m], i) => (
              <li key={n} className="rounded-[22px] p-6" style={{ background: OQ }}>
                <div className="text-sm font-semibold" style={{ color: YASHIL_OCH }}>
                  {i + 1}-qadam
                </div>
                <div className="mt-1 text-lg font-semibold">{n}</div>
                <p className="mt-2 text-base leading-relaxed" style={{ color: SOYA }}>
                  {m}
                </p>
              </li>
            ))}
          </ol>
        </section>

        {/* CTA */}
        <section className="mx-auto mt-24 max-w-6xl px-4">
          <div
            className="flex flex-wrap items-center justify-between gap-6 rounded-[28px] px-6 py-12 sm:px-12"
            style={{ background: YASHIL, color: '#fff' }}
          >
            <h2 className="max-w-xl text-3xl font-bold leading-tight sm:text-4xl">
              Kutubxonangizni bugun ro‘yxatdan o‘tkazing
            </h2>
            <div className="flex flex-wrap gap-3">
              <Link to="/register" className={btn} style={{ background: '#fff', color: '#163a9e' }}>
                Ro‘yxatdan o‘tish
              </Link>
              <Link to="/yordam" className={btn} style={{ border: '1px solid #ffffff80' }}>
                Qo‘llanma
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-8 text-center text-sm" style={{ color: SOYA }}>
        © {new Date().getFullYear()} Kutubxona
      </footer>
    </div>
  )
}
