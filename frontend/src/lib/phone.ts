/** Uzbek phone helpers. Stored/sent value is always "+998901234567"; the input shows "+998 90 123 45 67". */

const PREFIX = '998'

/** Digits of the national part (max 9), whatever the user typed or pasted. */
function nationalDigits(raw: string): string {
  let d = raw.replace(/\D/g, '')
  if (d.startsWith(PREFIX)) d = d.slice(PREFIX.length)
  else if (d.length === 10 && d.startsWith('0')) d = d.slice(1)
  return d.slice(0, 9)
}

/** Raw input -> canonical "+998XXXXXXXXX" (partial while typing). */
export function normalizePhone(raw: string): string {
  return '+' + PREFIX + nationalDigits(raw)
}

/** Canonical or raw -> "+998 90 123 45 67" (partial while typing). */
export function formatPhone(raw: string): string {
  const d = nationalDigits(raw)
  const parts = [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean)
  return ('+' + PREFIX + (parts.length ? ' ' + parts.join(' ') : '')).trim()
}

export function isCompletePhone(value: string): boolean {
  return /^\+998\d{9}$/.test(value)
}
