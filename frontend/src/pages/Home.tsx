import { useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'

/*
 * Landing (/welcome).
 * G'oya: kutubxona kitobining orqasiga yopishtirilgan formulyar (sana muhrli varaq).
 * Sahifaning asosiy elementi — shu varaqning jonli nusxasi: "Kitob berish" muhr bosadi,
 * "Qaytarib olish" qaytgan sanani bosadi. Qolgan hamma narsa jim va sodda.
 */

const INK = '#101c38' // kitob muqovasi tusidagi to'q ko'k
const MUHR = '#5b3a9e' // sana muhri siyohi
const VARAQ = '#fbf8ef' // formulyar qog'ozi
const SAHIFA = '#e9eef5'

const DISPLAY: CSSProperties = { fontFamily: "'Fraunces', Georgia, serif", fontWeight: 700 }
const MONO: CSSProperties = { fontFamily: "'IBM Plex Mono', ui-monospace, monospace" }

interface Qator {
  id: number
  oquvchi: string
  kitob: string
  berilgan: string
  muddat: string
  qaytgan?: string
}

const KUN = 24 * 60 * 60 * 1000
const sana = (d: Date) =>
  `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`

// Namuna ma'lumotlar: faqat ko'rsatish uchun, haqiqiy o'quvchi emas.
const NAMUNA: { oquvchi: string; kitob: string }[] = [
  { oquvchi: 'Madina Karimova, 7-sinf', kitob: 'O‘tkan kunlar' },
  { oquvchi: 'Sardor Aliyev, 9-sinf', kitob: 'Sariq devni minib' },
  { oquvchi: 'Nilufar Tursunova, 5-sinf', kitob: 'Kichkina shahzoda' },
  { oquvchi: 'Jasur Qodirov, 10-sinf', kitob: 'Mehrobdan chayon' },
]

function Formulyar() {
  const [qatorlar, setQatorlar] = useState<Qator[]>(() => {
    const t = Date.now()
    return [
      {
        id: 0,
        oquvchi: 'Aziza Rahimova, 6-sinf',
        kitob: 'Alisher Navoiy. Tanlangan asarlar',
        berilgan: sana(new Date(t - 9 * KUN)),
        muddat: sana(new Date(t + 5 * KUN)),
      },
    ]
  })
  const [keyingi, setKeyingi] = useState(0)

  const ochiqlar = qatorlar.filter((q) => !q.qaytgan).length

  function ber() {
    const n = NAMUNA[keyingi % NAMUNA.length]
    const t = Date.now()
    setQatorlar((old) => [
      { id: old.length + 1, ...n, berilgan: sana(new Date(t)), muddat: sana(new Date(t + 14 * KUN)) },
      ...old,
    ])
    setKeyingi((k) => k + 1)
  }

  function qaytar() {
    setQatorlar((old) => {
      const i = [...old].reverse().findIndex((q) => !q.qaytgan)
      if (i < 0) return old
      const idx = old.length - 1 - i
      return old.map((q, j) => (j === idx ? { ...q, qaytgan: sana(new Date()) } : q))
    })
  }

  return (
    <div>
      <div
        className="relative rounded-sm px-5 pb-5 pt-6 shadow-[0_18px_40px_-18px_rgba(16,28,56,0.45)] sm:px-7"
        style={{ background: VARAQ, color: INK, transform: 'rotate(0.6deg)' }}
      >
        <div className="flex items-baseline justify-between gap-3 border-b-2 pb-2" style={{ borderColor: INK }}>
          <span className="text-xs font-semibold uppercase tracking-[0.18em]" style={MONO}>
            Kitob formulyari
          </span>
          <span className="text-xs" style={MONO}>
            Qo‘lda: {ochiqlar} ta
          </span>
        </div>

        <ul className="min-h-[19rem]" aria-live="polite">
          {qatorlar.map((q, i) => (
            <li
              key={q.id}
              className="relative border-b border-dashed py-3 pr-2"
              style={{ borderColor: 'rgba(16,28,56,0.3)' }}
            >
              <div className="text-base font-semibold leading-snug">{q.kitob}</div>
              <div className="mt-0.5 text-sm" style={{ color: 'rgba(16,28,56,0.75)' }}>
                {q.oquvchi}
              </div>
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[13px]" style={MONO}>
                <span>Berildi {q.berilgan}</span>
                <span>Muddat {q.muddat}</span>
              </div>
              <span
                key={q.qaytgan ? 'q' : 'b'}
                className={i === 0 || q.qaytgan ? 'muhr-bos' : ''}
                style={{
                  ...MONO,
                  position: 'absolute',
                  right: 0,
                  top: 10,
                  border: `2px solid ${MUHR}`,
                  color: MUHR,
                  padding: '2px 8px',
                  fontSize: 13,
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                  transform: 'rotate(-4deg)',
                  opacity: 0.92,
                }}
              >
                {q.qaytgan ? `QAYTDI ${q.qaytgan}` : 'BERILDI'}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={ber}
          className="min-h-12 rounded-md px-5 text-base font-semibold text-white transition hover:brightness-110 active:translate-y-px"
          style={{ background: INK }}
        >
          Kitob berish
        </button>
        <button
          type="button"
          onClick={qaytar}
          disabled={ochiqlar === 0}
          className="min-h-12 rounded-md border-2 px-5 text-base font-semibold transition hover:bg-white/60 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ borderColor: INK, color: INK }}
        >
          Qaytarib olish
        </button>
        <span className="text-sm" style={{ color: 'rgba(16,28,56,0.7)' }}>
          Bosib ko‘ring. Bu namuna, ma’lumot saqlanmaydi.
        </span>
      </div>
    </div>
  )
}

const ISHLAR: { nom: string; matn: string }[] = [
  { nom: 'Berish va qaytarish', matn: 'O‘quvchini toping, kitobni tanlang, bering. Qaytganda bir bosish bilan qabul qiling.' },
  { nom: 'Nusxalar', matn: 'Har bir nusxa inventar raqami bilan. Qaysi biri javonda, qaysi biri o‘quvchida — shu zahoti ko‘rinadi.' },
  { nom: 'Band va navbat', matn: 'Kitob qo‘lda bo‘lsa, o‘quvchi navbatga turadi. Qaytgach navbatdagi kishi ko‘rinib turadi.' },
  { nom: 'Muddat va jarima', matn: 'Muddati o‘tganlar alohida ajraladi. Kechikish uchun jarima o‘zi hisoblanadi, to‘lovni belgilab borasiz.' },
  { nom: 'O‘quvchi va o‘qituvchilar', matn: 'Ro‘yxat, fanlar, arizalar. O‘qituvchi arizasini ko‘rib chiqib, tasdiqlaysiz yoki rad etasiz.' },
  { nom: 'Hisobotlar', matn: 'Eng ko‘p o‘qilgan kitoblar, qarzdorlar, fond holati — boshqaruv panelida, hisoblab o‘tirmasdan.' },
]

const QADAMLAR = [
  { nom: 'Kutubxonani ro‘yxatdan o‘tkazing', matn: 'Nomi va turini kiriting. Ma’lumotlaringiz boshqa kutubxonalardan alohida saqlanadi.' },
  { nom: 'Kitob va o‘quvchilarni kiriting', matn: 'Kitoblarni qo‘shing. O‘quvchilar Telegram bot orqali o‘zlari ariza yuboradi.' },
  { nom: 'Kitob bera boshlang', matn: 'Qo‘llanma har bir sahifada yonida. Qiynalsangiz, AI yordamchidan so‘rang.' },
]

export function Home() {
  return (
    <div className="min-h-screen" style={{ background: SAHIFA, color: INK }}>
      <header className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-1 sm:gap-3">
          <Link to="/yordam" className="hidden rounded-md px-3 py-2 text-sm font-medium hover:bg-white/60 sm:block">
            Qo‘llanma
          </Link>
          <Link to="/login" className="rounded-md px-3 py-2 text-sm font-semibold hover:bg-white/60">
            Kirish
          </Link>
          <Link
            to="/register"
            className="rounded-md px-4 py-2 text-sm font-semibold text-white hover:brightness-110"
            style={{ background: INK }}
          >
            Ro‘yxatdan o‘tish
          </Link>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-start gap-12 px-4 pb-20 pt-10 lg:grid-cols-[1.05fr_1fr] lg:pt-16">
          <div className="lg:pt-6">
            <h1 className="text-[2.6rem] leading-[1.05] sm:text-6xl" style={DISPLAY}>
              Kitob formulyari endi ekranda
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed" style={{ color: 'rgba(16,28,56,0.8)' }}>
              Berish, qaytarish, muddat va jarima — daftar o‘rniga bitta joyda. Kutubxonachi uchun,
              o‘zbek tilida, telefonda ham ishlaydi.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/register"
                className="rounded-md px-6 py-3.5 text-base font-semibold text-white hover:brightness-110"
                style={{ background: INK }}
              >
                Ro‘yxatdan o‘tish
              </Link>
              <Link
                to="/login"
                className="rounded-md border-2 px-6 py-3.5 text-base font-semibold hover:bg-white/60"
                style={{ borderColor: INK }}
              >
                Kirish
              </Link>
            </div>
          </div>
          <Formulyar />
        </section>

        {/* Ilovaning o'zi: haqiqiy skrinshotlar */}
        <section className="mx-auto max-w-6xl px-4 pb-20">
          <h2 className="max-w-2xl text-3xl leading-tight sm:text-4xl" style={DISPLAY}>
            Ilovaning o‘zi shunday ko‘rinadi
          </h2>
          <p className="mt-3 max-w-xl text-base" style={{ color: 'rgba(16,28,56,0.75)' }}>
            Bu rasm emas, ishlab turgan tizimdan olingan ekranlar (namunaviy ma’lumotlar bilan).
          </p>
          <div className="mt-8 grid items-start gap-6 lg:grid-cols-2">
            {[
              { src: '/landing/panel.jpg', nom: 'Boshqaruv paneli', alt: 'Boshqaruv paneli: muddati o‘tgan berishlar, navbatlar, jarimalar va fond holati' },
              { src: '/landing/berish.jpg', nom: 'Berish / Qaytarish', alt: 'Berish va qaytarish jadvali, har qatorda Qaytarish tugmasi' },
            ].map((k) => (
              <figure key={k.src} className="overflow-hidden rounded-lg border bg-white shadow-[0_18px_40px_-22px_rgba(16,28,56,0.5)]" style={{ borderColor: 'rgba(16,28,56,0.18)' }}>
                <div className="flex items-center gap-1.5 border-b px-3 py-2" style={{ borderColor: 'rgba(16,28,56,0.12)', background: '#f3f5f9' }}>
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: '#d9dde6' }} />
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: '#d9dde6' }} />
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: '#d9dde6' }} />
                  <figcaption className="ml-2 text-xs" style={MONO}>{k.nom}</figcaption>
                </div>
                <img src={k.src} alt={k.alt} loading="lazy" className="block h-auto w-full" />
              </figure>
            ))}
          </div>
        </section>

        {/* Nimalar qila olasiz */}
        <section className="bg-white/55 py-16">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 lg:grid-cols-[0.8fr_1.4fr]">
            <h2 className="text-3xl leading-tight sm:text-4xl" style={DISPLAY}>
              Kutubxonachi kuniga nima qiladi — shu hammasi bor
            </h2>
            <dl className="divide-y" style={{ borderColor: 'rgba(16,28,56,0.18)' }}>
              {ISHLAR.map((i) => (
                <div
                  key={i.nom}
                  className="grid gap-1 py-4 sm:grid-cols-[13rem_1fr] sm:gap-6"
                  style={{ borderColor: 'rgba(16,28,56,0.18)' }}
                >
                  <dt className="text-base font-semibold" style={MONO}>
                    {i.nom}
                  </dt>
                  <dd className="text-base leading-relaxed" style={{ color: 'rgba(16,28,56,0.8)' }}>
                    {i.matn}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* Bot va AI */}
        <section style={{ background: INK, color: '#eaf0fb' }}>
          <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-16 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl leading-tight sm:text-4xl" style={DISPLAY}>
                Yozib bering, qolganini tizim qiladi
              </h2>
              <p className="mt-5 max-w-md text-lg leading-relaxed" style={{ color: 'rgba(234,240,251,0.8)' }}>
                Ctrl+K bosing va oddiy gap bilan yozing. AI yordamchi buyruqni tushunib, kerakli sahifani
                ochadi. O‘quvchilar esa Telegram bot orqali o‘zlari ro‘yxatdan o‘tadi.
              </p>
            </div>
            <div className="rounded-md p-5" style={{ background: 'rgba(255,255,255,0.07)', ...MONO }}>
              <div className="text-xs uppercase tracking-[0.18em]" style={{ color: 'rgba(234,240,251,0.6)' }}>
                Buyruq
              </div>
              <div className="mt-2 text-lg">Madinaga «Kichkina shahzoda»ni ber</div>
              <div className="my-4 border-t border-dashed" style={{ borderColor: 'rgba(234,240,251,0.3)' }} />
              <div className="text-xs uppercase tracking-[0.18em]" style={{ color: 'rgba(234,240,251,0.6)' }}>
                Natija
              </div>
              <div className="mt-2 text-base" style={{ color: '#f6d77a' }}>
                Berish oynasi ochildi: o‘quvchi va kitob tanlangan
              </div>
            </div>
          </div>
        </section>

        {/* Qadamlar */}
        <section className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-3xl sm:text-4xl" style={DISPLAY}>
            Qanday boshlanadi
          </h2>
          <ol className="mt-8 grid gap-8 md:grid-cols-3">
            {QADAMLAR.map((q, i) => (
              <li key={q.nom} className="border-t-2 pt-4" style={{ borderColor: INK }}>
                <div className="text-sm" style={{ ...MONO, color: MUHR }}>
                  {i + 1}-qadam
                </div>
                <h3 className="mt-2 text-xl font-semibold leading-snug">{q.nom}</h3>
                <p className="mt-2 text-base leading-relaxed" style={{ color: 'rgba(16,28,56,0.8)' }}>
                  {q.matn}
                </p>
              </li>
            ))}
          </ol>
          <div className="mt-12 flex flex-wrap items-center gap-4">
            <Link
              to="/register"
              className="rounded-md px-7 py-4 text-lg font-semibold text-white hover:brightness-110"
              style={{ background: INK }}
            >
              Ro‘yxatdan o‘tish
            </Link>
            <Link to="/yordam" className="text-lg font-semibold underline underline-offset-4">
              Avval qo‘llanmani o‘qiyman
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t py-6 text-center text-sm" style={{ borderColor: 'rgba(16,28,56,0.18)', color: 'rgba(16,28,56,0.7)' }}>
        © {new Date().getFullYear()} Kutubxona
      </footer>
    </div>
  )
}
