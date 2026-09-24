import { api } from './client'
import type {
  Paginated,
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
  Berish,
  BerishCreatePayload,
  QaytarishResponse,
  Jarima,
  Navbat,
  Ariza,
  TopBook,
  DashboardStats,
} from '../types'

// ---- Auth ----

export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access: string; refresh: string }>('/auth/token/', { username, password }).then((r) => r.data),
  me: () => api.get<User>('/auth/me/').then((r) => r.data),
}

// ---- Books ----

export interface BookListParams {
  page?: number
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
  kitob?: number
  holati?: NusxaHolati
  javon?: string
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

export const readersApi = {
  list: (params?: { page?: number; search?: string }) =>
    api.get<Paginated<Oquvchi>>('/readers/', { params }).then((r) => r.data),
  get: (id: number) => api.get<OquvchiDetail>(`/readers/${id}/`).then((r) => r.data),
  create: (payload: OquvchiCreatePayload) => api.post<Oquvchi>('/readers/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Oquvchi>) =>
    api.patch<Oquvchi>(`/readers/${id}/`, payload).then((r) => r.data),
}

// ---- Applications (Arizalar) ----

export const applicationsApi = {
  list: (params?: { page?: number; holati?: string }) =>
    api.get<Paginated<Ariza>>('/applications/', { params }).then((r) => r.data),
  approve: (id: number) => api.post<Ariza>(`/applications/${id}/approve/`).then((r) => r.data),
  reject: (id: number, izoh?: string) =>
    api.post<Ariza>(`/applications/${id}/reject/`, { izoh }).then((r) => r.data),
}

// ---- Loans ----

export const loansApi = {
  list: (params?: { page?: number; holati?: string; oquvchi?: number }) =>
    api.get<Paginated<Berish>>('/loans/', { params }).then((r) => r.data),
  create: (payload: BerishCreatePayload) => api.post<Berish>('/loans/', payload).then((r) => r.data),
  return: (id: number) => api.post<QaytarishResponse>(`/loans/${id}/return/`).then((r) => r.data),
  overdue: () => api.get<Berish[]>('/loans/overdue/').then((r) => r.data),
}

// ---- Fines ----

export const finesApi = {
  list: (params?: { page?: number; tolandimi?: boolean; berish__oquvchi?: number }) =>
    api.get<Paginated<Jarima>>('/fines/', { params }).then((r) => r.data),
  pay: (id: number) => api.post<Jarima>(`/fines/${id}/pay/`).then((r) => r.data),
}

// ---- Reservations ----

export const reservationsApi = {
  list: (params?: { page?: number; holati?: string; kitob?: number; oquvchi?: number }) =>
    api.get<Paginated<Navbat>>('/reservations/', { params }).then((r) => r.data),
  create: (payload: { kitob: number; oquvchi: number }) =>
    api.post<{ id: number; orin: number }>('/reservations/', payload).then((r) => r.data),
  confirm: (id: number) => api.post<Navbat>(`/reservations/${id}/confirm/`).then((r) => r.data),
  remove: (id: number) => api.delete(`/reservations/${id}/`),
}

// ---- Staff ----

export const staffApi = {
  list: (params?: { page?: number }) => api.get<Paginated<User>>('/staff/', { params }).then((r) => r.data),
  create: (payload: UserCreatePayload) => api.post<User>('/staff/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<UserCreatePayload>) =>
    api.patch<User>(`/staff/${id}/`, payload).then((r) => r.data),
}

// ---- Stats ----

export const statsApi = {
  topBooks: (limit = 10) => api.get<TopBook[]>('/stats/top-books/', { params: { limit } }).then((r) => r.data),
  dashboard: () => api.get<DashboardStats>('/stats/dashboard/').then((r) => r.data),
}
