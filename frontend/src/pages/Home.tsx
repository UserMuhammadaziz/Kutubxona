import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { LiveDemo } from '../components/LiveDemo'

/*
 * Landing (/welcome). Iliq bej fon, to'q yashil aksent, yumshoq burchaklar (16-24px),
 * bitta shrift. Imkoniyatlar bir xil kartalarda emas, turli o'lchamdagi mozaikada.
 * Hero'dagi panel — LiveDemo (jonli namuna), skrinshot emas.
 */

const FON = '#ece9de'
const QUM = '#e2d6c0'
const OQ = '#faf8f2'
const YASHIL = '#0f3d2e'
const YASHIL_OCH = '#1f9d63'
const INK = '#1f1b16'
const SOYA = '#5c554b'
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

export function Home() {
  return (
    <div className="min-h-screen" style={{ ...SHRIFT, background: FON, color: INK }}>
      <header className="mx-auto flex h-20 max-w-6xl items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-1 sm:gap-2">
          <Link to="/demo" className="hidden px-3 py-2 text-sm font-medium hover:underline sm:block">
            Sinab ko‘rish
          </Link>
          <Link to="/yordam" className="hidden px-3 py-2 text-sm font-medium hover:underline md:block">
            Qo‘llanma
          </Link>
          <Link
            to="/login"
            className="rounded-full border px-4 py-2 text-sm font-semibold"
            style={{ borderColor: YASHIL, color: YASHIL }}
          >
            Tizimga kirish
          </Link>
          <Link to="/register" className="rounded-full px-5 py-2.5 text-sm font-semibold text-white" style={{ background: YASHIL }}>
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
            <Link to="/demo" className={btn} style={{ background: OQ }}>
              Sinab ko‘rish
            </Link>
          </div>

          <figure className="mt-12 overflow-hidden rounded-[24px] p-2 sm:p-3" style={{ background: QUM }}>
            <LiveDemo />
          </figure>
          <p className="mt-2 text-sm" style={{ color: SOYA }}>
            Bu ishlaydigan namuna: tugmalarni bosib ko‘ring. To‘liq sinov uchun{' '}
            <Link to="/demo" className="font-semibold underline">
              sinab ko‘rish sahifasiga
            </Link>{' '}
            o‘ting.
          </p>
        </section>

        {/* Raqamlar */}
        <section className="mx-auto mt-12 grid max-w-6xl gap-3 px-4 sm:grid-cols-3">
          {[
            ['Qizil', 'raqam: muddati o‘tgan berishlar panelda darrov ko‘rinadi'],
            ['Nusxa', 'har birining inventar raqami bor: javonda yoki o‘quvchida ekani ko‘rinadi'],
            ['Jarima', 'kechikkan kunga qarab o‘zi hisoblanadi'],
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
              <Link to="/register" className={btn} style={{ background: '#fff', color: YASHIL }}>
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
