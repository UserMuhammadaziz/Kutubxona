import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  GraduationCap,
  Lock,
  MessageCircle,
  Repeat,
  Smartphone,
  Sparkles,
  Wallet,
} from 'lucide-react'
import type { ComponentType } from 'react'
import { Logo } from '../components/Logo'

type Ikon = ComponentType<{ className?: string }>

const IMKONIYATLAR: { nomi: string; matn: string; ikon: Ikon }[] = [
  { ikon: Repeat, nomi: 'Berish va qaytarish', matn: 'Kitobni bir necha bosishda bering va qabul qiling. Muddati o‘tganlar o‘zi ajralib turadi.' },
  { ikon: BookOpen, nomi: 'Kitoblar va nusxalar', matn: 'Har bir nusxa inventar raqami bilan. Qaysi kitob javonda, qaysi biri qo‘lda — bir qarashda.' },
  { ikon: GraduationCap, nomi: 'O‘quvchi va o‘qituvchilar', matn: 'Ro‘yxat, kartalar, fanlar va arizalar. O‘qituvchi arizasini tasdiqlash yoki rad etish.' },
  { ikon: Lock, nomi: 'Band qilish va navbat', matn: 'Kitob band bo‘lsa, o‘quvchi navbatga turadi. Bo‘shagach sizga ko‘rinadi.' },
  { ikon: Wallet, nomi: 'Jarimalar', matn: 'Kechikish uchun jarima o‘zi hisoblanadi. To‘langan va to‘lanmagan summa alohida ko‘rinadi.' },
  { ikon: BarChart3, nomi: 'Statistika', matn: 'Eng ko‘p o‘qilgan kitoblar, qarzdorlar va fond holati — boshqaruv panelida.' },
]

const QADAMLAR = [
  { n: '1', nomi: 'Ro‘yxatdan o‘ting', matn: 'Kutubxonangiz nomini kiriting. Ma’lumotlaringiz boshqalarnikidan alohida saqlanadi.' },
  { n: '2', nomi: 'Kitob va o‘quvchilarni qo‘shing', matn: 'Kitoblarni, nusxalarni va o‘quvchilarni kiriting. O‘quvchilar Telegram bot orqali ham ariza yuboradi.' },
  { n: '3', nomi: 'Ishlashni boshlang', matn: 'Kitob bering, qaytarib oling, jarimalarni kuzating. Qo‘llanma har bir qadamda yordam beradi.' },
]

const QULAYLIKLAR: { nomi: string; matn: string; ikon: Ikon }[] = [
  { ikon: Bot, nomi: 'AI yordamchi', matn: 'Savolingizni o‘zbekcha yozing — tizim bo‘yicha yo‘l ko‘rsatadi. Ctrl+K bilan buyruq ham bering: «Aliga kitob ber».' },
  { ikon: MessageCircle, nomi: 'Telegram bot', matn: 'O‘quvchi va o‘qituvchi botdan ro‘yxatdan o‘tadi, arizasi sizga keladi.' },
  { ikon: Smartphone, nomi: 'Telefonda ham ishlaydi', matn: 'Ilova sifatida o‘rnatiladi, pastki menyu bilan qulay. Yozuv o‘lchamini o‘zingiz tanlaysiz.' },
  { ikon: Building2, nomi: 'Har kutubxona alohida', matn: 'Kutubxona, maktab, universitet yoki ofis — har biri o‘z ma’lumoti bilan ishlaydi.' },
]

/** Ochiq landing sahifa (/welcome): imkoniyatlarni ko'rsatadi, ro'yxatdan o'tish va kirishga yo'naltiradi. */
export function Home() {
  return (
    <div className="min-h-screen bg-canvas text-slate-900 dark:bg-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-canvas/90 backdrop-blur dark:border-slate-700/70 dark:bg-slate-900/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Logo />
          <nav className="flex items-center gap-2 sm:gap-4">
            <a href="#imkoniyatlar" className="hidden text-sm font-medium text-slate-600 hover:text-brand-700 sm:block dark:text-slate-300">
              Imkoniyatlar
            </a>
            <Link to="/yordam" className="hidden text-sm font-medium text-slate-600 hover:text-brand-700 sm:block dark:text-slate-300">
              Qo‘llanma
            </Link>
            <Link to="/login" className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800">
              Kirish
            </Link>
            <Link to="/register" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
              Boshlash
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 pb-14 pt-14 sm:pt-20">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-sm font-medium text-brand-800 dark:bg-brand-900/40 dark:text-brand-200">
                <Sparkles className="h-4 w-4" aria-hidden="true" /> AI yordamchi va Telegram bot bilan
              </span>
              <h1 className="mt-5 text-4xl font-bold leading-tight sm:text-5xl">
                Kutubxonani <span className="text-brand-600 dark:text-brand-400">qog‘ozsiz</span>, oson boshqaring
              </h1>
              <p className="mt-5 max-w-xl text-lg text-slate-600 dark:text-slate-300">
                Kitoblar, o‘quvchilar, berish-qaytarish va jarimalar — hammasi bir joyda. Daftar va Excel o‘rniga,
                kutubxonachi uchun sodda qilib yasalgan tizim.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/register" className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white shadow-md shadow-brand-600/20 hover:bg-brand-700">
                  Ro‘yxatdan o‘tish <ArrowRight className="h-5 w-5" aria-hidden="true" />
                </Link>
                <Link to="/login" className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800">
                  Kirish
                </Link>
              </div>
              <ul className="mt-8 space-y-2 text-slate-600 dark:text-slate-300">
                {['Kompyuter va telefonda ishlaydi', 'O‘zbek tilida', 'Ma’lumotlar sizniki, boshqalardan alohida'].map((t) => (
                  <li key={t} className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" /> {t}
                  </li>
                ))}
              </ul>
            </div>

            {/* Ilova ko'rinishi (bezak) */}
            <div className="rounded-2xl border border-slate-200 bg-paper p-5 shadow-xl dark:border-slate-700 dark:bg-slate-800" aria-hidden="true">
              <div className="mb-4 flex items-center justify-between">
                <span className="font-semibold">Boshqaruv paneli</span>
                <span className="text-sm text-slate-500">Bugungi holat</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { l: 'Javonda', i: BookOpen },
                  { l: 'Berilgan', i: Repeat },
                  { l: 'Navbatda', i: Clock },
                  { l: 'Muddati o‘tgan', i: Bell },
                ].map(({ l, i: Icon }) => (
                  <div key={l} className="rounded-xl bg-slate-50 p-4 dark:bg-slate-700/60">
                    <Icon className="h-5 w-5 text-brand-600 dark:text-brand-300" />
                    <div className="mt-3 h-3 w-16 rounded bg-slate-200 dark:bg-slate-600" />
                    <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">{l}</div>
                  </div>
                ))}
              </div>
              <div className="mt-4 space-y-2">
                {[70, 55, 40].map((w) => (
                  <div key={w} className="flex items-center gap-3 rounded-lg bg-slate-50 p-3 dark:bg-slate-700/60">
                    <div className="h-8 w-8 rounded-full bg-brand-100 dark:bg-brand-900/50" />
                    <div className="h-3 rounded bg-slate-200 dark:bg-slate-600" style={{ width: `${w}%` }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Imkoniyatlar */}
        <section id="imkoniyatlar" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-14">
          <h2 className="text-3xl font-bold">Kutubxonachiga kerakli hamma narsa</h2>
          <p className="mt-3 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
            Kundalik ish uchun kerak bo‘lgan asosiy imkoniyatlar.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {IMKONIYATLAR.map(({ ikon: Icon, nomi, matn }) => (
              <div key={nomi} className="rounded-2xl border border-slate-200 bg-paper p-6 dark:border-slate-700 dark:bg-slate-800">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                  <Icon className="h-6 w-6" />
                </span>
                <h3 className="mt-4 text-lg font-semibold">{nomi}</h3>
                <p className="mt-2 text-slate-600 dark:text-slate-300">{matn}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Qulayliklar */}
        <section className="bg-brand-900 text-white">
          <div className="mx-auto max-w-6xl px-4 py-14">
            <h2 className="text-3xl font-bold">Ishni yengillashtiradigan qo‘shimchalar</h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {QULAYLIKLAR.map(({ ikon: Icon, nomi, matn }) => (
                <div key={nomi} className="flex gap-4 rounded-2xl bg-white/10 p-6">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15">
                    <Icon className="h-6 w-6" />
                  </span>
                  <div>
                    <h3 className="text-lg font-semibold">{nomi}</h3>
                    <p className="mt-1 text-brand-100">{matn}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Qadamlar */}
        <section className="mx-auto max-w-6xl px-4 py-14">
          <h2 className="text-3xl font-bold">Qanday boshlanadi</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {QADAMLAR.map((q) => (
              <div key={q.n} className="rounded-2xl border border-slate-200 bg-paper p-6 dark:border-slate-700 dark:bg-slate-800">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">{q.n}</span>
                <h3 className="mt-4 text-lg font-semibold">{q.nomi}</h3>
                <p className="mt-2 text-slate-600 dark:text-slate-300">{q.matn}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-4 pb-16">
          <div className="rounded-3xl bg-brand-600 px-6 py-12 text-center text-white">
            <h2 className="text-3xl font-bold">Bugunoq sinab ko‘ring</h2>
            <p className="mx-auto mt-3 max-w-xl text-brand-100">Ro‘yxatdan o‘tish bir necha daqiqa oladi.</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link to="/register" className="rounded-xl bg-white px-6 py-3 font-semibold text-brand-800 hover:bg-brand-50">
                Ro‘yxatdan o‘tish
              </Link>
              <Link to="/yordam" className="rounded-xl border border-white/50 px-6 py-3 font-semibold hover:bg-white/10">
                Qo‘llanmani o‘qish
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
        © {new Date().getFullYear()} Kutubxona
      </footer>
    </div>
  )
}
