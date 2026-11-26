/**
 * Client-side twin of `apps/oquvchi/search.py`: case, apostrophe variants and
 * new-alphabet spellings (oʻ = o' = õ = o, gʻ = ğ = g) do not matter.
 */
export function searchKey(value: string | null | undefined): string {
  return (value ?? '')
    .toLocaleLowerCase()
    .replace(/[õöóòōŏ]/g, 'o')
    .replace(/[ğǵĝ]/g, 'g')
    .replace(/['‘’ʻʼ`´‛]/g, '')
    .replace(/[‐‑‒–—]/g, '-')
}

/** True when every word of `query` occurs in `text`. */
export function matchesSearch(text: string | null | undefined, query: string): boolean {
  const haystack = searchKey(text)
  return searchKey(query).split(/\s+/).filter(Boolean).every((word) => haystack.includes(word))
}
