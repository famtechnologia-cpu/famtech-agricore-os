const CACHE_NAME = 'agricore-v1'
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/devices',
  '/alerts',
  '/rules',
  '/maintenance',
  '/reports',
  '/workers',
  '/map',
]

// Install: pre-cache static shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  )
  self.clients.claim()
})

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // API requests: network first, no cache
  if (url.pathname.startsWith('/farms') || url.pathname.startsWith('/auth') || url.pathname.startsWith('/devices')) {
    event.respondWith(
      fetch(request).catch(() => new Response(JSON.stringify({ error: 'offline', cached: false }), {
        headers: { 'Content-Type': 'application/json' },
        status: 503,
      }))
    )
    return
  }

  // Static: stale-while-revalidate
  event.respondWith(
    caches.match(request).then(cached => {
      const networkFetch = fetch(request).then(response => {
        const clone = response.clone()
        caches.open(CACHE_NAME).then(cache => cache.put(request, clone))
        return response
      })
      return cached || networkFetch
    })
  )
})

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-actions') {
    event.waitUntil(syncOfflineActions())
  }
})

async function syncOfflineActions() {
  // Reads queued actions from IndexedDB and replays them
  console.log('[SW] Syncing offline actions...')
}
