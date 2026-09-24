export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
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
