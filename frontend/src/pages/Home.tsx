import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'

/*
 * Landing (/welcome). Qoidalar: burchaklar to'g'ri (radius 0), soya yo'q, bitta shrift,
 * bitta aksent rang, 1px qora chiziqlar. Asosiy "rasm" — ilovaning haqiqiy skrinshoti.
 */

const INK = '#0b1220'
const AKSENT = '#1d4ed8'
const CHIZIQ = '1px solid #0b1220'
const SHRIFT: CSSProperties = { fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }

const btn = 'inline-flex min-h-12 items-center px-6 text-base font-semibold'

const BORLAR: { nom: string; matn: string }[] = [
  { nom: 'Berish va qaytarish', matn: 'O‘quvchini toping, kitobni tanlang, bering. Qaytganda qatordagi tugmani bosing.' },
  { nom: 'Nusxalar', matn: 'Har bir nusxaning inventar raqami bor. Qaysi biri javonda, qaysi biri o‘quvchida — ro‘yxatda ko‘rinadi.' },
  { nom: 'Muddati o‘tganlar', matn: 'Qaytarilmagan kitoblar boshqaruv panelida qizil raqam bilan alohida chiqadi.' },
  { nom: 'Jarimalar', matn: 'Kechikish uchun jarima hisoblanadi. To‘langan va to‘lanmagan summa alohida turadi.' },
  { nom: 'Band va navbat', matn: 'Kitob qo‘lda bo‘lsa, o‘quvchi navbatga turadi. Navbatdagilar sonini panelda ko‘rasiz.' },
  { nom: 'O‘quvchi va o‘qituvchilar', matn: 'Ikkalasi alohida ro‘yxatda. O‘qituvchilar Telegram bot orqali ariza yuboradi, siz tasdiqlaysiz.' },
  { nom: 'Kutubxonalar alohida', matn: 'Har bir kutubxonaning ma’lumoti boshqalarnikidan ajratilgan. Kutubxona, maktab, universitet yoki ofis bo‘lishi mumkin.' },
  { nom: 'AI yordamchi', matn: 'Tizim bo‘yicha savolga o‘zbekcha javob beradi. Ctrl+K orqali oddiy gap bilan buyruq berasiz.' },
]

export function Home() {
  return (
    <div className="min-h-screen bg-white" style={{ ...SHRIFT, color: INK }}>
      <header style={{ borderBottom: CHIZIQ }}>
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Logo />
          <nav className="flex items-center gap-1 sm:gap-2">
            <Link to="/yordam" className="hidden px-3 py-2 text-sm font-medium hover:underline sm:block">
              Qo‘llanma
            </Link>
            <Link to="/login" className="px-3 py-2 text-sm font-medium hover:underline">
              Kirish
            </Link>
            <Link to="/register" className="px-4 py-2 text-sm font-semibold text-white" style={{ background: INK }}>
              Ro‘yxatdan o‘tish
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 pt-14 sm:pt-20">
          <h1 className="max-w-4xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-6xl">
            Kim qaysi kitobni olgan — bir qarashda.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed sm:text-xl" style={{ color: '#3b4558' }}>
            Kutubxonachi uchun berish, qaytarish, muddat va jarima hisobi. Daftar va Excel o‘rniga. O‘zbek tilida,
            kompyuter va telefonda.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register" className={btn + ' text-white'} style={{ background: AKSENT }}>
              Ro‘yxatdan o‘tish
            </Link>
            <Link to="/login" className={btn} style={{ border: CHIZIQ }}>
              Kirish
            </Link>
          </div>

          <figure className="mt-14" style={{ border: CHIZIQ }}>
            <img
              src="/landing/panel.jpg"
              alt="Boshqaruv paneli: muddati o‘tgan berishlar, navbatlar, jarimalar, fond holati, so‘nggi harakatlar"
              className="block h-auto w-full"
              width={1311}
              height={758}
            />
          </figure>
          <p className="mt-2 text-sm" style={{ color: '#3b4558' }}>
            Boshqaruv paneli. Ishlab turgan tizimdan olingan ekran, namunaviy ma’lumotlar bilan.
          </p>
        </section>

        {/* Berish / qaytarish */}
        <section className="mx-auto mt-20 max-w-6xl px-4">
          <div className="grid items-center gap-10 lg:grid-cols-[1fr_1.4fr]">
            <div>
              <h2 className="text-3xl font-bold leading-tight sm:text-4xl">Qaytarish — qator oxiridagi bitta tugma</h2>
              <p className="mt-4 text-lg leading-relaxed" style={{ color: '#3b4558' }}>
                Faol berishlar jadvalida kim, qaysi nusxani, qachon olgani va muddati ko‘rinadi. Kitob qaytganda tugmani
                bosasiz — nusxa yana javonga qaytadi.
              </p>
            </div>
            <figure style={{ border: CHIZIQ }}>
              <img
                src="/landing/berish.jpg"
                alt="Berish va qaytarish jadvali: kitob, o‘quvchi, berilgan sana, muddat, Qaytarish tugmasi"
                className="block h-auto w-full"
                loading="lazy"
                width={1311}
                height={758}
              />
            </figure>
          </div>
        </section>

        {/* Nimalar bor */}
        <section className="mx-auto mt-24 max-w-6xl px-4">
          <h2 className="text-3xl font-bold sm:text-4xl">Nimalar bor</h2>
          <dl className="mt-8 grid sm:grid-cols-2" style={{ borderTop: CHIZIQ, borderLeft: CHIZIQ }}>
            {BORLAR.map((b) => (
              <div key={b.nom} className="p-6" style={{ borderRight: CHIZIQ, borderBottom: CHIZIQ }}>
                <dt className="text-lg font-semibold">{b.nom}</dt>
                <dd className="mt-2 text-base leading-relaxed" style={{ color: '#3b4558' }}>
                  {b.matn}
                </dd>
              </div>
            ))}
          </dl>
        </section>

        {/* Boshlash */}
        <section className="mx-auto mt-24 max-w-6xl px-4">
          <h2 className="text-3xl font-bold sm:text-4xl">Boshlash</h2>
          <ol className="mt-8 grid md:grid-cols-3" style={{ borderTop: CHIZIQ, borderLeft: CHIZIQ }}>
            {[
              ['Ro‘yxatdan o‘ting', 'Kutubxona nomi va turini kiriting.'],
              ['Kitoblarni kiriting', 'Kitob va nusxalarni qo‘shing. O‘quvchilar Telegram bot orqali o‘zlari ariza yuboradi.'],
              ['Kitob bera boshlang', 'Qo‘llanma tizim ichida. Savol bo‘lsa, AI yordamchidan so‘rang.'],
            ].map(([n, m], i) => (
              <li key={n} className="p-6" style={{ borderRight: CHIZIQ, borderBottom: CHIZIQ }}>
                <div className="text-sm font-semibold" style={{ color: AKSENT }}>
                  {i + 1}-qadam
                </div>
                <div className="mt-1 text-lg font-semibold">{n}</div>
                <p className="mt-2 text-base leading-relaxed" style={{ color: '#3b4558' }}>
                  {m}
                </p>
              </li>
            ))}
          </ol>
        </section>

        {/* CTA */}
        <section className="mt-24" style={{ background: INK, color: '#fff' }}>
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-4 py-14">
            <h2 className="max-w-xl text-3xl font-bold leading-tight sm:text-4xl">Kutubxonangizni bugun ro‘yxatdan o‘tkazing</h2>
            <div className="flex flex-wrap gap-3">
              <Link to="/register" className={btn} style={{ background: '#fff', color: INK }}>
                Ro‘yxatdan o‘tish
              </Link>
              <Link to="/yordam" className={btn} style={{ border: '1px solid #fff' }}>
                Qo‘llanma
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-6 text-center text-sm" style={{ color: '#3b4558' }}>
        © {new Date().getFullYear()} Kutubxona
      </footer>
    </div>
  )
}
