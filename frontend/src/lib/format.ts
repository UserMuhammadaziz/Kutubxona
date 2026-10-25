export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  // "YYYY-MM-DD" — vaqtsiz sana. `new Date()` uni UTC daparse qilib, brauzer
  // vaqt zonasi UTC dan orqada bo'lsa (masalan UTC-5) bir kun oldinga
  // ko'rsatardi. Shuning uchun bunday qiymatlarni to'g'ridan-to'g'ri
  // formatlaymiz, timezone o'zgartirishidan foydalanmaymiz.
  const faqatSana = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (faqatSana) return `${faqatSana[3]}.${faqatSana[2]}.${faqatSana[1]}`
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return kunOy(d)
}

// `toLocaleDateString('uz-UZ')` brauzerga qarab "2026-10-21" yoki "21/10/2026"
// beradi; sahifada bir xil ko'rinish uchun qo'lda DD.MM.YYYY yig'iladi.
function kunOy(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`
}

/** Noma'lum kod (`band_qilingan`) xom holda chiqmasligi uchun: "Band qilingan". */
export function humanize(code: string): string {
  const t = code.replace(/_/g, ' ').trim()
  return t.charAt(0).toUpperCase() + t.slice(1)
}

/**
 * Sana + vaqtni mahalliy formatda ko'rsatadi (band so'rovi sanasi uchun).
 *
 * `so_rov_sanasi` DRF tomonidan `2026-10-04T07:02:10Z` ko'rinishida
 * yuboriladi. Avval jadvalda `value.slice(0, 16)` bilan kesilib ko'rsatilardi —
 * bu UTC vaqtini mahalliy vaqt sifatida ko'rsatib, bir necha soat xato
 * ko'rsatardi. Bu yerda `Date` orqali mahalliy vaqt zonasi qo'llaniladi.
 */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const sana = kunOy(d)
  const vaqt = d.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })
  return `${sana}, ${vaqt}`
}

export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(n)) return String(value)
  return `${n.toLocaleString('uz-UZ')} so'm`
}
