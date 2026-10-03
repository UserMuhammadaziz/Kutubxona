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

export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(n)) return String(value)
  return `${n.toLocaleString('uz-UZ')} so'm`
}
