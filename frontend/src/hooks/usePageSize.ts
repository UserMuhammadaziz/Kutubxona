import { create } from 'zustand'

const KEY = 'page-size'
const ALLOWED = [10, 20, 50]

function load(): number {
  try {
    const n = Number(localStorage.getItem(KEY))
    return ALLOWED.includes(n) ? n : 20
  } catch {
    return 20
  }
}

interface PageSizeState {
  pageSize: number
  setPageSize: (n: number) => void
}

const useStore = create<PageSizeState>((set) => ({
  pageSize: load(),
  setPageSize: (n) => {
    try {
      localStorage.setItem(KEY, String(n))
    } catch {
      /* storage may be unavailable; the choice still applies for this session */
    }
    set({ pageSize: n })
  },
}))

/** Rows per page, shared by all lists and remembered across visits. */
export function usePageSize(): [number, (n: number) => void] {
  const pageSize = useStore((s) => s.pageSize)
  const setPageSize = useStore((s) => s.setPageSize)
  return [pageSize, setPageSize]
}
