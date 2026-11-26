/**
 * Profildagi «Xatolik haqida xabar berish» uchun umumiy yordamchi.
 *
 * Ikki yo'l bilan ishlaydi:
 *  - qo'lda: foydalanuvchi Profilda matn yozib yuboradi;
 *  - avtomatik: ushlanmagan JS xatolari, rad etilgan promise'lar va 5xx API
 *    javoblari Profildagi tugma yoqilgan bo'lsa yuboriladi.
 *
 * Bu yerdagi so'rov `api` (axios) orqali emas, to'g'ridan-to'g'ri `fetch` bilan
 * qilinadi — aks holda xatolik xabari yuborilishi yana yangi xato keltirib,
 * cheksiz takrorlanish (loop) yuz berishi mumkin.
 */
import { isRequestLocked } from './requestLock'

const AUTO_KEY = 'kutubxona_xato_avtomatik'
const ACCESS_KEY = 'kutubxona_access'
const ENDPOINT = '/api/auth/xatolik-xabari/'

export function avtomatikYoqilgan(): boolean {
  return localStorage.getItem(AUTO_KEY) !== '0'
}

export function avtomatikHolatniSaqla(yoqilgan: boolean): void {
  localStorage.setItem(AUTO_KEY, yoqilgan ? '1' : '0')
}

let oxirgiMatn = ''
let oxirgiVaqt = 0

export async function xatolikYubor(
  matn: string,
  sahifa: string = window.location.pathname,
  tur: 'qolda' | 'avtomatik' = 'qolda',
): Promise<boolean> {
  const token = localStorage.getItem(ACCESS_KEY)
  const tozaMatn = matn.trim().slice(0, 2000)
  if (!token || !tozaMatn) return false
  try {
    const javob = await fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ matn: tozaMatn, sahifa, tur }),
    })
    return javob.ok
  } catch {
    return false
  }
}

/** Xatoni matnga aylantiradi (turli xil throw qiymatlarini qamrab oladi). */
export function xatoMatni(xato: unknown): string {
  if (xato instanceof Error) return `${xato.name}: ${xato.message}`
  if (typeof xato === 'string') return xato
  try {
    return JSON.stringify(xato)
  } catch {
    return String(xato)
  }
}

export function avtomatikXatolikniYubor(xato: unknown): void {
  if (!avtomatikYoqilgan() || isRequestLocked()) return
  const matn = xatoMatni(xato).slice(0, 2000)
  if (!matn) return
  // Bir xil xato qayta-qayta yuborilmasligi uchun 1 daqiqa ichida takrorlamaymiz.
  const hozir = Date.now()
  if (matn === oxirgiMatn && hozir - oxirgiVaqt < 60_000) return
  oxirgiMatn = matn
  oxirgiVaqt = hozir
  void xatolikYubor(matn, window.location.pathname, 'avtomatik')
}

/** Ilova ishga tushganda bir marta chaqiriladi. */
export function avtomatikXatoUshlagichlarniOrnat(): void {
  window.addEventListener('error', (hodisa) => {
    avtomatikXatolikniYubor(hodisa.error || hodisa.message)
  })
  window.addEventListener('unhandledrejection', (hodisa) => {
    avtomatikXatolikniYubor(hodisa.reason)
  })
}
