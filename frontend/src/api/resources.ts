import type { DashboardWidget, OrganizationType } from '../lib/organization'
import { api } from './client'
import { signupAttribution } from '../lib/tracking'
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
  FaollikReytingi,
  RecentActivity,
  XatolikXabari,
  XatolikXabariNatijasi,
} from '../types'

// ---- Auth ----

export interface RegisterPayload {
  kutubxona_nomi: string
  type: OrganizationType
  full_name: string
  /** Contact phone, +998901234567 */
  telefon: string
  password: string
  password_confirm: string
}

export interface OrganizationInfo {
  id: number
  nomi: string
  type: OrganizationType
  /** Effective ordered widget keys shown on the dashboard. */
  dashboard_widgets?: DashboardWidget[]
  /** Widget keys this organization's type may show. */
  available_dashboard_widgets?: DashboardWidget[]
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
  daily_report_enabled?: boolean
  /** Local time `HH:MM:SS` when the daily Excel report goes to staff. */
  daily_report_time?: string
  daily_report_recipients?: 'all' | 'librarians'
  /** Current user's role inside this organization (membership role). */
  rol?: string | null
  status?: string
  status_reason?: string
  status_changed_at?: string | null
  yaratilgan?: string
  /** Platform contacts; empty strings when not configured. */
  support?: { phone: string; telegram: string }
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
  webhook_url: string | null
  polling?: boolean
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
  updateOrganization: (id: number, payload: Partial<Omit<OrganizationInfo, 'id' | 'rol' | 'status' | 'available_dashboard_widgets'>>) =>
    api.patch<OrganizationInfo>(`/organizations/${id}/`, payload).then((r) => r.data),
  uploadLogo: (id: number, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return api.post<OrganizationInfo>(`/organizations/${id}/logo/`, body).then((r) => r.data)
  },
  deleteLogo: (id: number) => api.delete<OrganizationInfo>(`/organizations/${id}/logo/`).then((r) => r.data),
  register: (payload: RegisterPayload) =>
    api
      .post<{ access: string; refresh: string; user: User; organization: any }>('/auth/register/', {
        ...payload,
        attribution: signupAttribution(),
      })
      .then((r) => r.data),
  changePassword: (payload: ParolAlmashtirishPayload) =>
    api.post<{ detail: string }>('/auth/change-password/', payload).then((r) => r.data),
  updateProfile: (payload: ProfilYangilashPayload) =>
    api.patch<User>('/auth/profile/', payload).then((r) => r.data),
}

export interface ProfilYangilashPayload {
  username?: string
  full_name?: string
  telefon?: string
}

export interface ParolAlmashtirishPayload {
  joriy_parol: string
  yangi_parol: string
  yangi_parol_takror: string
}

// ---- Books ----

export interface BookListParams {
  page?: number
  page_size?: number
  janr?: string
  muallif?: string
  nashr_yili?: number
  search?: string
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
  create: (payload: NusxaCreatePayload) =>
    api.post<Nusxa & { created_count: number }>('/copies/', payload).then((r) => r.data),
  /** Copy counts per status; `holati` is left out on purpose. */
  summary: (params?: Omit<CopyListParams, 'holati' | 'page' | 'page_size'>) =>
    api.get<{ total: number; by_status: Partial<Record<NusxaHolati, number>> }>('/copies/summary/', { params }).then((r) => r.data),
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
  deleteSelected: (ids: number[]) =>
    api.post<OchirishNatijasi>('/readers/ochirish/', { ids }).then((r) => r.data),
}

export interface OchirishNatijasi {
  ochirildi: number
  ochirilmadi: { id: number; fish: string; sabab: string }[]
}

// ---- Xabarlar (Profil sahifasidan) ----

export interface XabarYuborishPayload {
  tur: 'shaxs' | 'sinf' | 'hamma'
  rol: OquvchiRol
  oquvchi?: number
  sinf?: string
  matn: string
}

export interface XabarNatijasi {
  jami: number
  yuborildi: number
  telegramsiz: number
  xatolik: number
}

export const messagesApi = {
  classes: (rol: OquvchiRol) =>
    api.get<string[]>('/messages/classes/', { params: { rol } }).then((r) => r.data),
  send: (payload: XabarYuborishPayload) =>
    api.post<XabarNatijasi>('/messages/send/', payload).then((r) => r.data),
}

// ---- Profil: xatolik haqida xabar ----

export interface XatolikXabariPayload {
  matn: string
  sahifa?: string
  tur?: 'qolda' | 'avtomatik'
}

export const xatolikApi = {
  list: () => api.get<XatolikXabari[]>('/auth/xatolik-xabari/').then((r) => r.data),
  send: (payload: XatolikXabariPayload) =>
    api.post<XatolikXabariNatijasi>('/auth/xatolik-xabari/', payload).then((r) => r.data),
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
  recentActivity: (limit = 8) =>
    api.get<RecentActivity[]>('/stats/recent-activity/', { params: { limit } }).then((r) => r.data),
  dashboard: () => api.get<DashboardStats>('/stats/dashboard/').then((r) => r.data),
  faollikReytingi: () =>
    api.get<FaollikReytingi>('/stats/ratings/activity/').then((r) => r.data),
  period: (params: PeriodParams) => api.get<PeriodReport>('/stats/period/', { params }).then((r) => r.data),
  exportPeriod: async (params: PeriodParams) => {
    const r = await api.get<Blob>('/stats/period/export/', { params, responseType: 'blob' })
    const match = /filename="([^"]+)"/.exec(String(r.headers['content-disposition'] ?? ''))
    const url = URL.createObjectURL(r.data)
    const link = document.createElement('a')
    link.href = url
    link.download = match?.[1] ?? 'hisobot.xlsx'
    link.click()
    URL.revokeObjectURL(url)
  },
  remind: (loanId: number) => api.post<{ delivered: boolean }>('/stats/remind/', { loan_id: loanId }).then((r) => r.data),
}

export type PeriodPreset = 'today' | 'yesterday' | 'tomorrow' | 'week' | 'month' | 'custom'
export interface PeriodParams {
  preset: PeriodPreset
  start?: string
  end?: string
}
export interface PeriodLoan {
  id: number
  reader_id: number
  reader: string
  role: string
  class_name: string
  phone: string
  telegram_linked: boolean
  book: string
  inventory_number: string
  issued_at: string
  due_date: string
  returned_at: string | null
  status: 'on_time' | 'late' | 'not_returned'
  late_days: number
  issued_by: string
  received_by: string
  reminder: { sent_at: string | null; delivered: boolean; kind: string } | null
}
export interface PeriodFine {
  id: number
  reader: string
  class_name: string
  book: string
  late_days: number
  amount: string
  paid: boolean
  paid_at: string | null
  received_by: string
}
export interface PeriodReport {
  period: { start: string; end: string; today: string }
  summary: {
    due: number
    returned_on_time: number
    returned_late: number
    not_returned: number
    overdue_total: number
    issued: number
    returned: number
    fines_new_count: number
    fines_new_amount: string
    fines_paid_count: number
    fines_paid_amount: string
    fines_unpaid_amount: string
    reservations_new: number
    reservations_fulfilled: number
    applications_new: number
    applications_approved: number
    new_readers: number
    reminders_sent: number
    reminders_delivered: number
  }
  due: PeriodLoan[]
  not_returned: PeriodLoan[]
  overdue: PeriodLoan[]
  issued: PeriodLoan[]
  returned: PeriodLoan[]
  fines_new: PeriodFine[]
  fines_paid: PeriodFine[]
  by_staff: { name: string; issued: number; received: number }[]
  by_class: { class_name: string; overdue: number }[]
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
  type: OrganizationType
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
  subscription: PlatformSubscription | null
}

export type SubscriptionStatus = 'trial' | 'active' | 'past_due' | 'canceled' | 'expired'

export interface PlatformSubscription {
  plan: string
  plan_name: string
  status: SubscriptionStatus
  /** Same as `status`, or "expired" when the period has ended. */
  effective_status: SubscriptionStatus
  trial_ends_at: string | null
  current_period_end: string | null
  limits: PlanLimits
}

/** `null` means unlimited. */
export interface PlanLimits {
  max_staff: number | null
  max_resources: number | null
  max_customers: number | null
}

export interface PlatformStats {
  jami: number
  holatlar: Record<OrgStatus, number>
  tashkilotlar: PlatformOrg[]
}

export interface PlatformPlan extends PlanLimits {
  id: number
  code: string
  nomi: string
  tavsif: string
  narx_oylik: string
  tartib: number
  faol: boolean
  organization_count: number
  is_default: boolean
}

export type PlatformPlanForm = PlanLimits & Pick<PlatformPlan, 'nomi' | 'tavsif' | 'narx_oylik' | 'faol'>

export interface AuditEntry {
  id: number
  organization_nomi: string | null
  actor_username: string | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown> | null
  yaratilgan: string
}

export interface PlatformOrgForm {
  nomi: string
  slug?: string
  type: OrganizationType
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
  setSubscription: (
    id: number,
    payload: { plan?: string; status?: SubscriptionStatus; trial_ends_at?: string | null; current_period_end?: string | null },
  ) =>
    api.post(`/saas/organizations/${id}/subscription/`, payload).then((r) => r.data),
  plans: () =>
    api.get<Paginated<PlatformPlan> | PlatformPlan[]>('/saas/plans/').then((r) => (Array.isArray(r.data) ? r.data : r.data.results)),
  createPlan: (payload: PlatformPlanForm) => api.post<PlatformPlan>('/saas/plans/', payload).then((r) => r.data),
  updatePlan: (id: number, payload: Partial<PlatformPlanForm> & { tartib?: number }) =>
    api.patch<PlatformPlan>(`/saas/plans/${id}/`, payload).then((r) => r.data),
  removePlan: (id: number) => api.delete(`/saas/plans/${id}/`).then((r) => r.data),
  audit: (page = 1) => api.get<Paginated<AuditEntry>>('/saas/audit/', { params: { page } }).then((r) => r.data),
  details: (id: number) => api.get<PlatformOrgDetails>(`/saas/organizations/${id}/details/`).then((r) => r.data),
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

export interface MarketingSourceRow {
  source: string
  medium: string
  visits: number
  visitors: number
  signups: number
  approved: number
  conversion: number
}

export interface MarketingCampaignRow {
  source: string
  medium: string
  campaign: string
  visits: number
  visitors: number
  signups: number
  conversion: number
}

export interface MarketingSignup {
  organization_id: number
  organization_name: string
  status: string
  created_at: string
  first_seen_at: string | null
  source: string
  medium: string
  campaign: string
  term: string
  content: string
  referrer_host: string
  landing_path: string
  last_source: string
  last_medium: string
}

export interface MarketingReport {
  days: number
  totals: { visits: number; visitors: number; signups: number; approved: number; conversion: number }
  sources: MarketingSourceRow[]
  campaigns: MarketingCampaignRow[]
  daily: { date: string; visits: number; visitors: number; signups: number }[]
  recent_signups: MarketingSignup[]
}

export const marketingApi = {
  report: (days: number) => api.get<MarketingReport>('/marketing/report/', { params: { days } }).then((r) => r.data),
}

export interface PlatformPerson {
  id: number
  full_name: string
  username: string
  phone: string
  email: string
  date_joined: string
  last_login: string | null
}

export interface MarketingTouch {
  source: string
  medium: string
  campaign: string
  term?: string
  content?: string
  referrer_host?: string
  landing_path?: string
  click_id?: string
  at?: string | null
}

export interface MarketingVisit extends MarketingTouch {
  created_at: string
}

export interface PlatformOrgDetails {
  organization: {
    id: number
    name: string
    slug: string
    type: string
    status: OrgStatus
    status_reason: string
    status_changed_at: string | null
    approved_at: string | null
    approved_by: string
    created_at: string
    phone: string
    email: string
    address: string
    description: string
    logo_url: string
  }
  owner: PlatformPerson | null
  members: (PlatformPerson & { role: string; role_display: string; active: boolean; joined_at: string; telegram_linked: boolean })[]
  subscription: PlatformSubscription | null
  usage: {
    books: number
    copies: number
    readers: number
    loans: number
    open_loans: number
    overdue_loans: number
    pending_applications: number
    reservations: number
  }
  bot: { username: string; status: string; status_display: string; webhook_set: boolean; last_checked_at: string | null; last_error: string } | null
  push_subscriptions: number
  attribution: { first: MarketingTouch; last: MarketingTouch; signed_up_at: string; visits: MarketingVisit[] } | null
  timeline: { id: number; action: string; actor: string; metadata: Record<string, unknown>; created_at: string }[]
}
