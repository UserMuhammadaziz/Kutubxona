import { create } from 'zustand'

const STORAGE_KEY = 'kutubxona-font-size'

export type FontSize = 'kichik' | 'orta' | 'katta'

export const FONT_SIZES: { key: FontSize; label: string; percent: number; hint: string }[] = [
  { key: 'kichik', label: 'Kichik', percent: 100, hint: 'Standart' },
  { key: 'orta', label: "O'rta", percent: 112.5, hint: 'Qulay' },
  { key: 'katta', label: 'Katta', percent: 125, hint: 'Juda aniq' },
]

function getInitial(): FontSize {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'kichik' || saved === 'orta' || saved === 'katta') return saved
  } catch {
    /* ignore */
  }
  return 'kichik'
}

export function applyFontSize(size: FontSize) {
  const p = FONT_SIZES.find((f) => f.key === size)?.percent ?? 100
  document.documentElement.style.fontSize = `${p}%`
}

interface FontSizeState {
  size: FontSize
  setSize: (s: FontSize) => void
}

export const useFontSizeStore = create<FontSizeState>((set) => ({
  size: getInitial(),
  setSize: (size) => {
    try {
      localStorage.setItem(STORAGE_KEY, size)
    } catch {
      /* ignore */
    }
    applyFontSize(size)
    set({ size })
  },
}))

applyFontSize(useFontSizeStore.getState().size)
