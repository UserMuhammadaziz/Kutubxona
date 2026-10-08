// Service worker: PWA uchun offline qobiq (app shell) va statik assetlar keshi.
// Manzili /sw.js — scope barcha sahifalarni qamrab oladi (Django route qiladi).
const VERSION = 'v1'
const SHELL_CACHE = `kutubxona-shell-${VERSION}`
// Hash'langan build fayllari immutable, shuning uchun kesh versiyasiz —
// aks holda yangi buildda eski tab ochiq turganda assetlar o'chib ketardi.
const STATIC_CACHE = 'kutubxona-static'
const SHELL_URL = '/'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.add(new Request(SHELL_URL, { cache: 'reload' })))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('kutubxona-shell-') && key !== SHELL_CACHE)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  // API doim yangi bo'lishi kerak (JWT, joriy ma'lumot) — keshlanmaydi.
  if (url.pathname.startsWith('/api/')) return

  // Navigatsiya: network-first, offline'da keshdagi SPA qobig'i.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(SHELL_CACHE).then((cache) => cache.put(SHELL_URL, copy))
          }
          return response
        })
        .catch(() =>
          caches
            .match(SHELL_URL)
            .then(
              (cached) =>
                cached ||
                new Response('Internet yo\'q', {
                  status: 503,
                  headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                }),
            ),
        ),
    )
    return
  }

  // Statik assetlar (hash'langan): cache-first.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request)
        if (cached) return cached
        const response = await fetch(request)
        if (response.ok) cache.put(request, response.clone())
        return response
      }),
    )
  }
})
