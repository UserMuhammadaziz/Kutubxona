import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { keepPreviousData, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import { ToastProvider } from './components/Toast.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      // Sahifa almashganda eski ma'lumot ko'rinib tursin (jumpsiz almashuv).
      placeholderData: keepPreviousData,
    },
  },
})

// PWA: service worker faqat production build'da va ishonchli HTTPS muhitda
// ro'yxatdan o'tadi. IP manzillarda (masalan http://16.171.23.72 yoki
// https://IP «sertifikat ogohlantirishidan o'tib» kirilganda) SW skripti
// «An SSL certificate error occurred when fetching the script» xatosi bilan
// yuklanmaydi — bunday hollarda ro'yxatdan o'tkazilmaydi, konsol toza qoladi.
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const isIpHost = /^\d{1,3}(\.\d{1,3}){3}$/.test(window.location.hostname)
    if (!window.isSecureContext || isIpHost) return
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  </StrictMode>,
)
