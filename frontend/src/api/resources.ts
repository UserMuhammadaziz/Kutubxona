import { api } from './client'
import type {
  Paginated,
  Announcement,
  AnnouncementAudience,
  AnnouncementPreview,
  User,
  UserCreatePayload,
  Kitob,
  KitobDetail,
  KitobPayload,
  Nusxa,
  NusxaDetail,
  NusxaCreatePayload,
  NusxaHolati,
  Oquvchi,
  OquvchiDetail,
  OquvchiCreatePayload,
  OquvchiRol,
  Berish,
  BerishCreatePayload,
  BerishHolati,
  QaytarishResponse,
  Jarima,
  Navbat,
  NavbatHolati,
  Ariza,
  ArizaHolati,
  ArizaRol,
  TopBook,
  DashboardStats,
  BandQilish,
  BandQilishMeni,
  BandQilishYaratishPayload,
  BandHolati,
} from '../types'

// ---- Auth ----

export interface RegisterPayload {
  kutubxona_nomi: string
  turi: 'library' | 'school' | 'university' | 'office' | 'other'
  full_name: string
  /** Contact phone, +998901234567 */
  telefon: string
  password: string
  password_confirm: string
}

export interface OrganizationInfo {
  id: number
  nomi: string
  turi: string
  manzil?: string
  telefon?: string
  email?: string
  tavsif?: string
  logo_url?: string
  /** Default loan period in days. */
  muddat_kun?: number
  /** Fine per overdue day (so'm). */
  kunlik_jarima?: string | number
  /** Max books a reader may hold at once. */
  limit_kitob?: number
  /** Hours a reader has to claim a book offered from the queue. */
  taklif_soat?: number
  /** Days before the due date to send a reminder. */
  eslatma_kunlar_oldin?: number
  kitob_xabarlari_yoqilgan?: boolean
  /** Current user's role inside this organization (membership role). */
  rol?: string | null
  status?: string
  /** Per-library feature switches (missing key = off). */
  capabilities?: { search_inline?: boolean }
}

// ---- Telegram bot (per organization) ----

export interface TelegramBotInfo {
  id: number
  username: string
  telegram_bot_id: number
  holati: string
  webhook_ornatilgan: boolean
  webhook_url: string
  oxirgi_tekshiruv: string | null
  oxirgi_xato: string
  yaratilgan: string
}

export interface TelegramBotState {
  ulangan: boolean
  bot?: TelegramBotInfo
}

export const telegramApi = {
  get: () => api.get<TelegramBotState>('/telegram/settings/').then((r) => r.data),
  connect: (token: string) =>
    api.post<TelegramBotState>('/telegram/settings/', { token }).then((r) => r.data),
  disconnect: () => api.delete<TelegramBotState>('/telegram/settings/').then((r) => r.data),
  action: (action: 'test' | 'webhook') =>
    api.post<TelegramBotState>(`/telegram/actions/${action}/`).then((r) => r.data),
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access: string; refresh: string }>('/auth/token/', { username, password }).then((r) => r.data),
  me: () => api.get<User>('/auth/me/').then((r) => r.data),
  organization: () => api.get<OrganizationInfo | null>('/auth/organization/').then((r) => r.data),
  updateOrganization: (id: number, payload: Partial<Omit<OrganizationInfo, 'id' | 'rol' | 'status' | 'turi'>>) =>
    api.patch<OrganizationInfo>(`/organizations/${id}/`, payload).then((r) => r.data),
  register: (payload: RegisterPayload) =>
    api.post<{ access: string; refresh: string; user: User; organization: any }>('/auth/register/', payload).then((r) => r.data),
}

// ---- Books ----

export interface BookListParams {
  page?: number
  page_size?: number
  janr?: string
  muallif?: string
  nashr_yili?: number
}

export const booksApi = {
  list: (params?: BookListParams) => api.get<Paginated<Kitob>>('/books/', { params }).then((r) => r.data),
  search: (q: string) => api.get<Kitob[]>('/books/search/', { params: { q } }).then((r) => r.data),
  get: (id: number) => api.get<KitobDetail>(`/books/${id}/`).then((r) => r.data),
  create: (payload: KitobPayload) => api.post<KitobDetail>('/books/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<KitobPayload>) =>
    api.patch<KitobDetail>(`/books/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/books/${id}/`),
  queue: (id: number) => api.get<Navbat[]>(`/books/${id}/queue/`).then((r) => r.data),
}

// ---- Copies ----

export interface CopyListParams {
  page?: number
  page_size?: number
  kitob?: number
  holati?: NusxaHolati
  javon?: string
  search?: string
}

export const copiesApi = {
  list: (params?: CopyListParams) => api.get<Paginated<Nusxa>>('/copies/', { params }).then((r) => r.data),
  get: (id: number) => api.get<NusxaDetail>(`/copies/${id}/`).then((r) => r.data),
  create: (payload: NusxaCreatePayload) => api.post<Nusxa>('/copies/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Pick<Nusxa, 'holati' | 'javon' | 'izoh'>>) =>
    api.patch<Nusxa>(`/copies/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/copies/${id}/`),
}

// ---- Readers ----

export interface ReaderListParams {
  page?: number
  page_size?: number
  search?: string
  rol?: OquvchiRol | ''
  faol?: boolean
  sinf?: string
  has_telegram?: boolean
  has_debt?: boolean
  has_active_loans?: boolean
}

export const readersApi = {
  list: (params?: ReaderListParams) =>
    api.get<Paginated<Oquvchi>>('/readers/', { params }).then((r) => r.data),
  get: (id: number) => api.get<OquvchiDetail>(`/readers/${id}/`).then((r) => r.data),
  create: (payload: OquvchiCreatePayload) => api.post<Oquvchi>('/readers/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Oquvchi>) =>
    api.patch<Oquvchi>(`/readers/${id}/`, payload).then((r) => r.data),
  sendMessage: (id: number, text: string) =>
    api.post<{ sent: boolean }>(`/readers/${id}/message/`, { text }).then((r) => r.data),
}

// ---- Applications (Arizalar) ----

export interface ApplicationListParams {
  page?: number
  page_size?: number
  holati?: ArizaHolati | ''
  rol?: ArizaRol | ''
  sinf?: string
  search?: string
}

export const applicationsApi = {
  list: (params?: ApplicationListParams) =>
    api.get<Paginated<Ariza>>('/applications/', { params }).then((r) => r.data),
  approve: (id: number) => api.post<Ariza>(`/applications/${id}/approve/`).then((r) => r.data),
  reject: (id: number, izoh?: string) =>
    api.post<Ariza>(`/applications/${id}/reject/`, { izoh }).then((r) => r.data),
}

// ---- Loans ----

export interface LoanListParams {
  page?: number
  page_size?: number
  holati?: BerishHolati | ''
  oquvchi?: number
  q?: string
  grade?: string
  issued_from?: string
  issued_to?: string
  overdue?: boolean
}

export const loansApi = {
  list: (params?: LoanListParams) => api.get<Paginated<Berish>>('/loans/', { params }).then((r) => r.data),
  create: (payload: BerishCreatePayload) => api.post<Berish>('/loans/', payload).then((r) => r.data),
  return: (id: number) => api.post<QaytarishResponse>(`/loans/${id}/return/`).then((r) => r.data),
  overdue: () => api.get<Berish[]>('/loans/overdue/').then((r) => r.data),
}

// ---- Fines ----

export interface FineListParams {
  page?: number
  page_size?: number
  tolandimi?: boolean
  berish__oquvchi?: number
  search?: string
}

export const finesApi = {
  list: (params?: FineListParams) => api.get<Paginated<Jarima>>('/fines/', { params }).then((r) => r.data),
  pay: (id: number) => api.post<Jarima>(`/fines/${id}/pay/`).then((r) => r.data),
}

// ---- Reservations ----

export interface ReservationListParams {
  page?: number
  page_size?: number
  holati?: NavbatHolati | ''
  kitob?: number
  oquvchi?: number
}

export const reservationsApi = {
  list: (params?: ReservationListParams) =>
    api.get<Paginated<Navbat>>('/reservations/', { params }).then((r) => r.data),
  create: (payload: { kitob: number; oquvchi: number }) =>
    api.post<{ id: number; orin: number }>('/reservations/', payload).then((r) => r.data),
  confirm: (id: number) => api.post<Navbat>(`/reservations/${id}/confirm/`).then((r) => r.data),
  remove: (id: number) => api.delete(`/reservations/${id}/`),
}

// ---- Holds (Band qilish) ----

export interface HoldListParams {
  page?: number
  page_size?: number
  holati?: BandHolati | ''
  kitob?: number
}

export const holdsApi = {
  list: (params?: HoldListParams) =>
    api.get<Paginated<BandQilish>>('/holds/', { params }).then((r) => r.data),
  create: (payload: BandQilishYaratishPayload) =>
    api.post<BandQilish>('/holds/', payload).then((r) => r.data),
  my: (telegram_id: number) =>
    api.get<BandQilishMeni[]>('/holds/my/', { params: { telegram_id } }).then((r) => r.data),
  approve: (id: number, izoh?: string) =>
    api.post<BandQilish>(`/holds/${id}/approve/`, { izoh }).then((r) => r.data),
  reject: (id: number, izoh?: string) =>
    api.post<BandQilish>(`/holds/${id}/reject/`, { izoh }).then((r) => r.data),
  cancel: (id: number, telegram_id: number) =>
    api.post<BandQilish>(`/holds/${id}/cancel/`, { telegram_id }).then((r) => r.data),
}

// ---- Staff ----

export const staffApi = {
  list: (params?: { page?: number; page_size?: number }) => api.get<Paginated<User>>('/staff/', { params }).then((r) => r.data),
  create: (payload: UserCreatePayload) => api.post<User>('/staff/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<UserCreatePayload>) =>
    api.patch<User>(`/staff/${id}/`, payload).then((r) => r.data),
}

// ---- Stats ----

export const statsApi = {
  topBooks: (limit = 10) => api.get<TopBook[]>('/stats/top-books/', { params: { limit } }).then((r) => r.data),
  dashboard: () => api.get<DashboardStats>('/stats/dashboard/').then((r) => r.data),
}

// ---- Announcements ----

export const announcementsApi = {
  list: (page = 1) =>
    api.get<Paginated<Announcement>>('/announcements/', { params: { page } }).then((r) => r.data),
  preview: (audience: AnnouncementAudience, grade: string) =>
    api.post<AnnouncementPreview>('/announcements/preview/', { audience, grade }).then((r) => r.data),
  send: (payload: { text: string; audience: AnnouncementAudience; grade: string }) =>
    api.post<Announcement>('/announcements/send/', payload).then((r) => r.data),
}

// ---- Platform (master) ----

export type OrgStatus = 'pending' | 'active' | 'rejected' | 'suspended' | 'archived'

export interface PlatformOrg {
  id: number
  nomi: string
  slug: string
  turi: string
  status: OrgStatus
  faol: boolean
  kitoblar: number
  oquvchilar: number
  berishlar: number
  azoliklar: number
  bot_ulangan: boolean
  egasi_ismi: string
  telefon: string
  status_reason: string
  yaratilgan: string
}

export interface PlatformStats {
  jami: number
  holatlar: Record<OrgStatus, number>
  tashkilotlar: PlatformOrg[]
}

export interface PlatformPlan {
  id: number
  code: string
  nomi: string
  narx_oylik: string
  faol: boolean
}

export interface AuditEntry {
  id: number
  organization_nomi: string | null
  actor_username: string | null
  action: string
  target_type: string
  target_id: string
  yaratilgan: string
}

export interface PlatformOrgForm {
  nomi: string
  slug?: string
  turi: string
  tavsif: string
  telefon: string
  email: string
  manzil: string
  logo_url: string
  muddat_kun: number
  kunlik_jarima: number
  limit_kitob: number
  /** Create-only: owner account (reused when the phone already exists). */
  owner?: { telefon: string; full_name: string; password: string }
}

export const platformApi = {
  get: (id: number) => api.get<PlatformOrgForm & { id: number }>(`/saas/organizations/${id}/`).then((r) => r.data),
  create: (payload: PlatformOrgForm) => api.post<PlatformOrg>('/saas/organizations/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<PlatformOrgForm>) =>
    api.patch<PlatformOrg>(`/saas/organizations/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/saas/organizations/${id}/`).then((r) => r.data),
  stats: () => api.get<PlatformStats>('/saas/organizations/stats/').then((r) => r.data),
  setStatus: (id: number, action: 'approve' | 'reject' | 'suspend' | 'activate' | 'archive', reason = '') =>
    api.post(`/saas/organizations/${id}/${action}/`, reason ? { reason } : {}).then((r) => r.data),
  setSubscription: (id: number, payload: { plan?: string; status?: string }) =>
    api.post(`/saas/organizations/${id}/subscription/`, payload).then((r) => r.data),
  plans: () =>
    api.get<Paginated<PlatformPlan> | PlatformPlan[]>('/saas/plans/').then((r) => (Array.isArray(r.data) ? r.data : r.data.results)),
  audit: (page = 1) => api.get<Paginated<AuditEntry>>('/saas/audit/', { params: { page } }).then((r) => r.data),
}

export type HealthState = 'ok' | 'down' | 'stale' | 'missing'

export interface PlatformHealth {
  checked_at: string
  web: { status: HealthState }
  database: { status: HealthState; error: string }
  cache: { status: HealthState; error: string }
  heartbeats: {
    name: string
    status: HealthState
    last_seen: string | null
    age_seconds: number | null
    limit_seconds: number
  }[]
  bots: {
    organization: string
    username: string
    state: string
    webhook: boolean
    last_check: string | null
    last_error: string
    stale: boolean
  }[]
}

export const healthApi = {
  platform: () => api.get<PlatformHealth>('/saas/health/').then((r) => r.data),
}
