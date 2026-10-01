import { useEffect, useState } from 'react'

/**
 * Qiymatni kechiktirilgan holda qaytaradi.
 *
 * Qidiruv maydonlari uchun: har bir tugma bosilishida so'rov yuborilmasligi
 * uchun. Kirish maydoni `qiymat` ga, so'rov esa `kechikkan` ga bog'lanadi.
 *
 *   const [qidiruv, setQidiruv] = useState('')
 *   const kechikkan = useDebouncedValue(qidiruv, 300)
 *   useQuery({ queryKey: ['readers', kechikkan], queryFn: ... })
 */
export function useDebouncedValue<T>(qiymat: T, kutishMs = 300): T {
  const [kechikkan, setKechikkan] = useState(qiymat)

  useEffect(() => {
    const t = window.setTimeout(() => setKechikkan(qiymat), kutishMs)
    return () => window.clearTimeout(t)
  }, [qiymat, kutishMs])

  return kechikkan
}
