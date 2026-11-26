/** Organization type and dashboard widget catalogue shared by settings, dashboard and forms. */

export type OrganizationType = 'library' | 'school'

export const ORG_TYPE_OPTIONS: { value: OrganizationType; label: string; hint: string }[] = [
  { value: 'library', label: 'Kutubxona', hint: 'Kitobxondan FISH, telefon, manzil va tug‘ilgan sana so‘raladi.' },
  { value: 'school', label: 'Maktab', hint: 'Kitobxon rolini tanlaydi: o‘quvchi sinfini, o‘qituvchi fanini kiritadi.' },
]

export const ORG_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  ORG_TYPE_OPTIONS.map((o) => [o.value, o.label]),
)

export const isSchool = (org: { type?: string } | null | undefined) => org?.type === 'school'

/** Keys match `apps/organization/dashboard.py`. */
export type DashboardWidget =
  | 'overdue_loans'
  | 'active_reservations'
  | 'total_debt'
  | 'unpaid_fines'
  | 'total_books'
  | 'total_copies'
  | 'available_copies'
  | 'issued_copies'
  | 'students_count'
  | 'teachers_count'
  | 'members_count'
  | 'pending_applications'
  | 'approved_applications'
  | 'readers_by_class'
  | 'recent_activity'
  | 'top_books'

export const DASHBOARD_WIDGET_INFO: Record<DashboardWidget, { label: string; hint: string; kind: 'stat' | 'panel' }> = {
  overdue_loans: { label: "Muddati o'tgan", hint: 'qaytarilmagan berishlar', kind: 'stat' },
  active_reservations: { label: 'Navbatda', hint: "kutayotgan o'quvchilar", kind: 'stat' },
  total_debt: { label: 'Umumiy qarz', hint: "to'lanmagan jarimalar summasi", kind: 'stat' },
  unpaid_fines: { label: "To'lanmagan jarimalar", hint: 'ta jarima', kind: 'stat' },
  total_books: { label: 'Jami kitoblar', hint: 'nomdagi kitoblar', kind: 'stat' },
  total_copies: { label: 'Jami nusxalar', hint: 'fonddagi barcha nusxalar', kind: 'stat' },
  available_copies: { label: 'Javonda', hint: 'berishga tayyor nusxalar', kind: 'stat' },
  issued_copies: { label: 'Berilgan', hint: "o'quvchilarda turgan nusxalar", kind: 'stat' },
  students_count: { label: "O'quvchilar", hint: "faol o'quvchilar", kind: 'stat' },
  teachers_count: { label: "O'qituvchilar", hint: "faol o'qituvchilar", kind: 'stat' },
  members_count: { label: 'Jami kitobxonlar', hint: 'faol o‘quvchi va o‘qituvchilar', kind: 'stat' },
  pending_applications: { label: 'Kutilayotgan arizalar', hint: 'tasdiqlanishi kerak', kind: 'stat' },
  approved_applications: { label: 'Tasdiqlangan arizalar', hint: 'jami qabul qilingan', kind: 'stat' },
  readers_by_class: { label: 'Sinflar bo‘yicha', hint: 'har sinfdagi o‘quvchilar soni', kind: 'panel' },
  recent_activity: { label: 'So‘nggi harakatlar', hint: 'oxirgi berish va qaytarishlar', kind: 'panel' },
  top_books: { label: 'Eng ko‘p o‘qilgan kitoblar', hint: 'eng ko‘p berilgan 5 ta kitob', kind: 'panel' },
}
