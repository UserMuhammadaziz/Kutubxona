// ---- Shared ----

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  error: string
  detail: string
}

export type Rol = 'kutubxonachi' | 'administrator'

// ---- Auth / User ----

export interface User {
  id: number
  username: string
  full_name: string
  rol: Rol
  telefon: string
  is_active: boolean
}

export interface UserCreatePayload {
  username: string
  full_name: string
  rol: Rol
  telefon: string
  is_active?: boolean
  password: string
}

// ---- Kitob (Book) ----

export type Janr = 'badiiy' | 'ilmiy' | 'darslik' | 'bolalar' | 'tarixiy' | 'boshqa'

export const JANR_LABELS: Record<Janr, string> = {
  badiiy: 'Badiiy',
  ilmiy: 'Ilmiy',
  darslik: 'Darslik',
  bolalar: "Bolalar",
  tarixiy: 'Tarixiy',
  boshqa: 'Boshqa',
}

export interface Kitob {
  id: number
  nomi: string
  muallif: string
  isbn: string | null
  janr: Janr
  til: string
  narh: string | null
  buyurtma_soni: number | null
  holati: KitobHolati
  nashr_yili: number
  nashriyot: string | null
  tavsif: string | null
  qoshilgan_sana: string
  mavjud_nusxalar: number
  jami_nusxalar: number
  faol_navbatlar: number
}

export interface KitobDetail {
  id: number
  nomi: string
  muallif: string
  isbn: string | null
  janr: Janr
  til: string
  narh: string | null
  buyurtma_soni: number | null
  holati: KitobHolati
  nashr_yili: number
  nashriyot: string | null
  tavsif: string | null
  qoshilgan_sana: string
  nusxalar: NusxaBrief[]
}

export interface KitobPayload {
  nomi: string
  muallif: string
  isbn?: string
  janr: Janr
  til?: string
  narh?: string
  buyurtma_soni?: string
  holati?: string
  nashr_yili: number
  nashriyot?: string
  tavsif?: string
}

export const TIL_LABELS: Record<string, string> = {
  ozbek_lotin: "O'zbek tili",
  ozbek_krill: 'Узбек тили',
  rus: 'Rus tili',
  ingliz: 'Ingliz tili',
  boshqa: 'Boshqa',
}

export type KitobHolati = 'mavjud' | 'yoqolgan'

export const HOLAT_LABELS: Record<KitobHolati, string> = {
  mavjud: 'Mavjud',
  yoqolgan: "Yo'qolgan",
}

// ---- Nusxa (Copy) ----

export type NusxaHolati = 'mavjud' | 'berilgan' | 'band' | 'tamirda' | 'yoqolgan'

export const NUSXA_HOLATI_LABELS: Record<NusxaHolati, string> = {
  mavjud: 'Mavjud',
  berilgan: 'Berilgan',
  band: 'Band',
  tamirda: "Ta'mirda",
  yoqolgan: 'Yo‘qolgan',
}

export interface NusxaBrief {
  id: number
  inventar_raqami: string
  holati: NusxaHolati
  javon: string | null
}

export interface Nusxa {
  id: number
  kitob: number
  kitob_nomi: string
  inventar_raqami: string
  holati: NusxaHolati
  javon: string | null
  qabul_sana: string
  izoh: string | null
}

export interface NusxaDetail extends Nusxa {
  berish_tarixi: Berish[]
}

export interface NusxaCreatePayload {
  kitob: number
  inventar_raqami: string
  javon?: string
  qabul_sana?: string
  izoh?: string
}

// ---- Oquvchi (Reader) ----

export interface Oquvchi {
  id: number
  fish: string
  telefon: string
  telegram_id: number | null
  karta_raqami: string
  tugilgan_sana: string | null
  manzil: string | null
  royxat_sanasi: string
  faol: boolean
}

export interface OquvchiDetail extends Oquvchi {
  joriy_kitoblari: BerishMeni[]
  jarimalari: JarimaMeni[]
}

export interface OquvchiCreatePayload {
  fish: string
  telefon: string
  tugilgan_sana?: string
  manzil?: string
}

// ---- Ariza (Application) ----

export type ArizaHolati = 'kutmoqda' | 'tasdiqlandi' | 'bekor'

export const ARIZA_HOLATI_LABELS: Record<ArizaHolati, string> = {
  kutmoqda: 'Kutmoqda',
  tasdiqlandi: 'Tasdiqlandi',
  bekor: 'Bekor qilindi',
}

export interface Ariza {
  id: number
  telegram_id: number
  fish: string
  telefon: string
  tugilgan_sana: string | null
  manzil: string
  holati: ArizaHolati
  ariza_sanasi: string
  tasdiqlangan_sana: string | null
  izoh: string
}

// ---- Berish (Loan) ----

export type BerishHolati = 'faol' | 'qaytarilgan' | 'yoqolgan'

export const BERISH_HOLATI_LABELS: Record<BerishHolati, string> = {
  faol: 'Faol',
  qaytarilgan: 'Qaytarilgan',
  yoqolgan: 'Yo‘qolgan',
}

export interface Berish {
  id: number
  nusxa: number
  kitob_nomi: string
  inventar_raqami: string
  oquvchi: number
  oquvchi_fish: string
  bergan_xodim: number
  olgan_xodim: number | null
  berilgan_sana: string
  qaytarish_muddati: string
  qaytarilgan_sana: string | null
  holati: BerishHolati
  eslatma_yuborilgan: boolean
}

export interface BerishMeni {
  id: number
  kitob_nomi: string
  inventar_raqami: string
  berilgan_sana: string
  qaytarish_muddati: string
  qolgan_kun: number
}

export interface BerishCreatePayload {
  nusxa: number
  oquvchi: number
}

export interface QaytarishResponse {
  berish: Berish
  jarima_summasi: string | null
  navbatga_taklif_ketdimi: boolean
}

// ---- Jarima (Fine) ----

export interface Jarima {
  id: number
  berish: number
  oquvchi_fish: string
  kitob_nomi: string
  kechikkan_kunlar: number
  kunlik_stavka: string
  summa: string
  tolandimi: boolean
  tolangan_sana: string | null
  qabul_qilgan: number | null
  yangilangan: string
}

export interface JarimaMeni {
  id: number
  kitob_nomi: string
  kechikkan_kunlar: number
  summa: string
  tolandimi: boolean
}

// ---- Navbat (Reservation) ----

export type NavbatHolati = 'kutmoqda' | 'taklif_qilindi' | 'yakunlandi' | 'bekor'

export const NAVBAT_HOLATI_LABELS: Record<NavbatHolati, string> = {
  kutmoqda: 'Kutmoqda',
  taklif_qilindi: 'Taklif qilindi',
  yakunlandi: 'Yakunlandi',
  bekor: 'Bekor qilindi',
}

export interface Navbat {
  id: number
  kitob: number
  kitob_nomi: string
  oquvchi: number
  oquvchi_fish: string
  navbat_sanasi: string
  holati: NavbatHolati
  ajratilgan_nusxa: number | null
  taklif_vaqti: string | null
  taklif_muddati: string | null
  javob_vaqti: string | null
  bekor_sababi: string | null
}

export interface NavbatMeni {
  id: number
  kitob_nomi: string
  holati: NavbatHolati
  navbat_sanasi: string
  orin: number | null
}

// ---- Stats ----

export interface TopBook {
  id: number
  nomi: string
  muallif: string
  berishlar_soni: number
}

export interface DashboardStats {
  jami_kitoblar: number
  jami_nusxalar: number
  mavjud_nusxalar: number
  berilgan_nusxalar: number
  muddati_otgan_berishlar: number
  faol_navbatlar: number
  tolanmagan_jarimalar_soni: number
  umumiy_qarz: string
}
