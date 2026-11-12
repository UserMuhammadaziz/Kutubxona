import { useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { useAuthStore } from '../store/auth'
import { Layout } from '../components/Layout'
import { Logo, LogoMark } from '../components/Logo'
import { StatsCard } from '../components/StatCard'
import { formatMoney } from '../lib/format'

export function Home() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: () => statsApi.dashboard(),
    enabled: !!tokenStore.getAccess(),
  })

  const hydrate = useAuthStore((s) => s.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  if (status === 'idle' || status === 'loading') {
    return <Spinner />
  }

  if (status === 'unauthenticated') {
    return (
      <div className="min-h-screen bg-canvas">
        <Navigate to="/login" replace />
      </div>
    )
  }

  return (
    <Layout>
      <nav className="border-b border-slate-200 dark:border-slate-700 pb-4">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <LogoMark className="h-8 w-8" />
            <span className="text-xl font-semibold text-brand-600">Kutubxona</span>
          </span>
          <nav className="hidden sm:flex items-center gap-8">
            <NavLink to="/" className="text-slate-600 dark:text-slate-400 hover:text-brand-600 font-medium">
              <svg
                className="inline-block align-middle h-4 w-4"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M10 4a1 1 0 011 1h3a1 1 0 110 2h-3a1 1 0 01-1-1zm0 6a1 1 0 011 1h5a1 1 0 110 2h-5a1 1 0 01-1-1zm0 6a1 1 0 011 1h2a1 1 0 110 2h-2a1 1 0 01-1-1zm5-14h2a2 2 0 012 2v8a2 2 0 01-2h-2v-8a2 2 0 012-2zm-7 4h2a2 2 0 012 2v4a2 2 0 01-2h-2v-4a2 2 0 012-2zm7 4h2a2 2 0 012 2v4a2 2 0 01-2h-2v-4a2 2 0 012-2z" />
              </svg>
              Boshqaruv paneli
            </NavLink>
            <NavLink to="/books" className="text-slate-600 dark:text-slate-400 hover:text-brand-600 font-medium">
              Kitoblar
            </NavLink>
          </nav>
        </div>
        {/* Foydalanuvchini hisoblash */
        {data && (
          <div className="mt-6 grid grid-cols-2 gap-4">
            <StatsCard
              label="Jami kitoblar"
              value={data.jami_kitoblar}
              tone="amber"
            />
            <StatsCard
              label="Jami nusxalar"
              value={data.jami_nusxalar}
              tone="brand"
            />
            <StatsCard
              label="Faol berishlar"
              value={data.fool_navbatlar}
              tone="green"
            />
            <StatsCard
              label="Tolangan jarima"
              value={data.tolanmagan_jarimalar_soni}
              tone="red"
            />
          </div>
        )}
      </nav>

      <main className="py-8">
        <div className="max-w-7xl mx-auto px-4">
          {/* Hero Section */
          <section className="mb-12">
            <div className="bg-paper rounded-2xl p-8 dark:bg-slate-800">
              <div className="max-w-2xl mx-auto text-center">
                <div className="inline-flex items-baseline rounded-full bg-gradient-to-r from-brand-600 to-brand-700 px-3 py-1 text-xs font-medium text-white mb-6">
                  <span>Kutubxona SaaS</span>
                </div>
                <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 dark:text-slate-100 leading-tight">
                  Kitoblarni boshqarish, raqobatlansiz
                </h1>
                <p className="mt-6 text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
                  Platforma boʻlabsiz aylanib, barcha tashkilotlar uchun maxsus resurslarni boshqarish imkonini beradi.
                </p>
              </div>
            </div>
          </section>

          {/* Features Section */
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">Asosiy imkoniyathlar</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="group bg-paper rounded-xl p-6 dark:bg-slate-800 hover:shadow-xl hover:transition-shadow duration-300">
                <div className="h-12 w-12 rounded-xl bg-brand-100 flex items-center justify-center group-hover:bg-brand-200 transition-colors mb-4">
                  <svg className="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6a2 2 0 00-2 2v6h4V6h2v8h4V8h2v6zm10-4h-4V6h4v6h4V6h4v6h-4v6h-4V6h-4v6zm-4 12h-4v-6h4v6zM6 6v6h2V6H6zm7.5-3c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t1.5-.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm0 12c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t1.5.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm-8.5-3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm8.5 3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 transition-colors mb-2">Tasavvur qiluvchi panel</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm">
                  Barcha tashkilotlar uchun maksimal ko‘nizlikda kutubxona boshqarish.
                </p>
              </div>
              <div className="group bg-paper rounded-xl p-6 dark:bg-slate-800 hover:shadow-xl hover:transition-shadow duration-300">
                <div className="h-12 w-12 rounded-xl bg-brand-100 flex items-center justify-center group-hover:bg-brand-200 transition-colors mb-4">
                  <svg className="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6a2 2 0 00-2 2v6h4V6h2v8h4V8h2v6zm10-4h-4V6h4v6h4V6h4v6h-4v6h-4V6h-4v6zm-4 12h-4v-6h4v6zM6 6v6h2V6H6zm7.5-3c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t.67 1.5 1.5-.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm0 12c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t1.5.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm-8.5-3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm8.5 3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 transition-colors mb-2">O'quvchilar boshqlash</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm">
                  Oquvchilar ro‘yxati, arizalari va statistikasi boshqaruvi.
                </p>
              </div>
              <div className="group bg-paper rounded-xl p-6 dark:bg-slate-800 hover:shadow-xl hover:transition-shadow duration-300">
                <div className="h-12 w-12 rounded-xl bg-brand-100 flex items-center justify-center group-hover:bg-brand-200 transition-colors mb-4">
                  <svg className="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6a2 2 0 00-2 2v6h4V6h2v8h4V8h2v6zm10-4h-4V6h4v6h4V6h4v6h-4v6h-4V6h-4v6zm-4 12h-4v-6h4v6zM6 6v6h2V6H6zm7.5-3c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t.67 1.5 1.5-.5c.83 0 1.5.67 1.5 1.5s-.67 1.5 1.5 1.5t-1.5-.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm0 12c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5t1.5.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm8.5-3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5zm8.5 3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5t-1.5-.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 transition-colors mb-2">Band va berish</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm">
                  Kitoblarni band qilish, berish va qaytarish jarayonlari.
                </p>
              </div>
            </div>
          </section>

          {/* Supported Organizations */
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">Yanada keladigan tashkilotlar</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-paper rounded-xl p-4 dark:bg-slate-800">
                <div className="h-10 w-10 rounded-xl bg-brand-100 flex items-center justify-center mb-3">
                  <svg className="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v8c0 6 8 10 8 10z" />
                    <path d="M14 9.5l-5 4.5L5 9.5l5 4.5L14 9.5zM14 13l-5-4.5L5 13l5-4.5L14 13z" />
                  </svg>
                </div>
                <h3 className="text-base font-medium text-slate-900 dark:text-slate-100">Kutubxonalar</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                  Kitob, nusxa va o‘quvchilar boshqaruvi.
                </p>
              </div>
              <div className="bg-paper rounded-xl p-4 dark:bg-slate-800">
                <div className="h-10 w-10 rounded-xl bg-brand-100 flex items-center justify-center mb-3">
                  <svg className="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M21 16.08c-.45 2.33-1.75 4.69-3.32 6.59.96.52 2-.03 2-.57v-2.06c0-.54-.56-.99-.99-.82-2.01.16-3.97-1.05-4.42-2.09-.16-.46-.16-1.02 0-1.49.45-1.76 1.75-3.82 2.65-.37 1.45-.7 3.14-.88 4.83-.17.55-.27.98-.32 1.33-.05.35-.41.62-.7.79-1.21-.08-1.63-.54-2.27-1.36.09-.32.08-.76 0-1.13-.12-.55-.3-1.49-.77-2.32-1.18-.47-1.26-1.24-2.19-2.36-2.73-.47-.25-.76-.47-1.02-.63-.09-.05-.26-.05-.37 0-.05.06-.21.16-.42.42-.63.75-1.28.93-1.86.16-.17.27-.32.32-.58.05-.26.09-.52.09-.77 0-.26 0-.52 0-.78 0 0-1.53 1.24-2.69 2.36.16.25.32.55.32.87v.5c0 .67.18 1.33.45 2h.05c.56 1.64 1.8 2.97 3.61 3.79 1.36.7 2.77 1.02 4.31 1.02 2.15 0 3.64-.71 4.66-1.89 1.06-.2 1.87-.6 2.43-1.24.56-.64.82-1.53.82-2.69 0-1.37-.6-2.44-1.58-3.13-.93-.67-2.12-1.06-3.58-1.06-2.76 0-4.63 2.18-4.75 5.06.06.38.06.86 0 1.22-.06 1.18-.83 2.33-1.96 2.98-1.25.74-2.65.94-4.7.94-4.94 0-6.18-3.78-5.05-7.04-.97-.67-2.25-1.22-4.48-1.15-.64.04-1.25.34-1.7.87-.54.67-1.08 1.35-1.36 2.18-.3.83-.53 1.76-.53 2.73 0 1.36.53 2.72 1.3 3.76 1.53 1.86 2.9 2.68 4.13 2.68 1.17 0 2.25-.38 3.14-1.12.89-.74 1.56-1.77 1.95-2.88.38-1.11.53-2.41.53-3.89 0-1.78-.43-3.39-1.3-4.65-1.57-.68-.78-1.34-1.62-1.87-2.43-.28-.47-.43-.86-.43-1.34 0-.59.28-1.09.43-1.5.37-.75.67-1.65 1.12-2.5.61-.95.94-2.04 1.12-3.24.18-1.27.04-2.74-.05-4.22z" />
                  </svg>
                </div>
                <h3 className="text-base font-medium text-slate-900 dark:text-slate-100">Universitetlar</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                    Fanlar va/materiallar boshqaruvi.
                </p>
              </div>
              <div className="bg-paper rounded-xl p-4 dark:bg-slate-800">
                <div className="h-10 w-10 rounded-xl bg-brand-100 flex items-center justify-center mb-3">
                  <svg className="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v8c0 6 8 10 8 10z" />
                    <path d="M14 9.5l-5 4.5L5 9.5l5 4.5L14 9.5zM14 13l-5-4.5L5 13l5-4.5L14 13z" />
                  </svg>
                </div>
                <h3 className="text-base font-medium text-slate-900 dark:text-slate-100">Ofislar</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                    Zaminlar va xizmatlar.
                </p>
              </div>
            </div>
          </section>

          {/* CTA Section */
          <section className="mt-12 bg-gradient-to-b from-brand-50 to-canvas dark:from-brand-950 dark:to-slate-900 rounded-2xl p-8">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                O'z tashkilotingizni yarating
              </h2>
              <p className="text-slate-500 dark:text-slate-400 mb-8">
                SaaS platformasining barcha imkoniyatiyla ega bo‘ling. Endi ro‘yxatdan o‘tib, tashkilotingizni yaratish va admin tasdiqlashini kuting.
              </p>
              <div className="space-y-3">
                <NavLink
                  to="/register"
                  className="inline-block bg-brand-600 text-white font-medium py-3 px-8 rounded-lg hover:bg-brand-700 transition-colors">
                  Ro‘yxatdan o‘tish
                </NavLink>
                <NavLink
                  to="/login"
                  className="inline-block bg-white text-brand-600 font-medium py-3 px-8 rounded-lg hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-200 transition-colors">
                  Kiritish (boshqalar uchun)
                </NavLink>
              </div>
            </div>
          </section>
        </div>
      </main>
    </Layout>
  )
}