/** Ctrl+K panelida ko'rinadigan bo'limlar (Layout'dagi menyu bilan bir xil yo'llar). */
export const SECTIONS = [
  { to: '/', label: 'Boshqaruv paneli' },
  { to: '/books', label: 'Kitoblar' },
  { to: '/copies', label: 'Nusxalar' },
  { to: '/readers', label: 'O‘quvchilar' },
  { to: '/teachers', label: 'O‘qituvchilar' },
  { to: '/applications', label: 'Arizalar' },
  { to: '/loans', label: 'Berish / Qaytarish' },
  { to: '/bandlar', label: 'Bandlar' },
  { to: '/reservations', label: 'Navbatlar' },
  { to: '/fines', label: 'Jarimalar' },
  { to: '/guide', label: 'Qo‘llanma' },
  { to: '/staff', label: 'Xodimlar', adminOnly: true },
]

const norm = (s: string) => s.toLowerCase().replace(/[‘’ʻʼ'`]/g, '').trim()

/** Bo'sh so'rovda hammasi; aks holda nomida so'rov qatnashgan bo'limlar. */
export function matchSections(query: string, admin: boolean) {
  const q = norm(query)
  return SECTIONS.filter((s) => (admin || !s.adminOnly) && norm(s.label).includes(q))
}
