import { Link } from 'react-router-dom'
import { Logo } from '../components/Logo'

const IMKONIYATLAR = [
  { nomi: 'Boshqaruv paneli', matn: 'Fond, berilgan kitoblar, muddati o‘tganlar va jarimalar bir joyda.' },
  { nomi: 'O‘quvchilar', matn: 'O‘quvchi va o‘qituvchilar ro‘yxati, arizalar va statistika.' },
  { nomi: 'Band va berish', matn: 'Kitobni band qilish, berish va qaytarish jarayonlari.' },
]

/** Ochiq tanishuv sahifasi (/welcome): ro'yxatdan o'tish va kirishga yo'naltiradi. */
export function Home() {
  return (
    <div className="min-h-screen bg-canvas dark:bg-slate-900">
      <header className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
        <Logo />
        <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-brand-600 dark:text-slate-300">
          Kirish
        </Link>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-12">
        <section className="text-center">
          <h1 className="text-4xl font-bold leading-tight text-slate-900 dark:text-slate-100 sm:text-5xl">
            Kutubxonani oson boshqaring
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-500 dark:text-slate-400">
            Kutubxona, maktab, universitet yoki ofis uchun kitoblar, o‘quvchilar va berish-qaytarish tizimi.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/register" className="rounded-lg bg-brand-600 px-6 py-3 font-medium text-white hover:bg-brand-700">
              Ro‘yxatdan o‘tish
            </Link>
            <Link to="/yordam" className="rounded-lg border border-slate-300 px-6 py-3 font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800">
              Qo‘llanma
            </Link>
          </div>
        </section>

        <section className="mt-16 grid gap-4 sm:grid-cols-3">
          {IMKONIYATLAR.map((i) => (
            <div key={i.nomi} className="rounded-xl bg-paper p-6 dark:bg-slate-800">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">{i.nomi}</h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{i.matn}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}
