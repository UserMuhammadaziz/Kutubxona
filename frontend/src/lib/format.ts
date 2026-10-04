export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  // "YYYY-MM-DD" — vaqtsiz sana. `new Date()` uni UTC daparse qilib, brauzer
  // vaqt zonasi UTC dan orqada bo'lsa (masalan UTC-5) bir kun oldinga
  // ko'rsatardi. Shuning uchun bunday qiymatlarni to'g'ridan-to'g'ri
  // formatlaymiz, timezone o'zgartirishidan foydalanmaymiz.
  const faqatSana = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (faqatSana) return `${faqatSana[1]}.${faqatSana[2]}.${faqatSana[3]}`
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('uz-UZ', { year: 'numeric', month: '2-digit', day: '2-digit' })
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
  const sana = d.toLocaleDateString('uz-UZ', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  const vaqt = d.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })
  return `${sana}, ${vaqt}`
}

export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(n)) return String(value)
  return `${n.toLocaleString('uz-UZ')} so'm`
}
