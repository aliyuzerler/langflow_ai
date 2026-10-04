/* Langflow PWA service worker.
 *
 * Strategy:
 *  - App shell (/, /index.html, manifest, icons) is cached on install.
 *  - Navigations are network-first with a cached-shell fallback when offline.
 *  - Static assets (same-origin build chunks) are stale-while-revalidate.
 *  - API traffic (/api/*, websockets, cross-origin) is NEVER intercepted.
 *
 * Bump APP_VERSION to invalidate old caches after a deploy.
 */
const APP_VERSION = "langflow-pwa-v1";
const SHELL_CACHE = `${APP_VERSION}-shell`;
const ASSET_CACHE = `${APP_VERSION}-assets`;

const SHELL_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/favicon.ico",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => !key.startsWith(APP_VERSION))
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  // Never touch API calls, websockets or cross-origin traffic.
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/docs")) return;

  if (request.mode === "navigate") {
    // Network-first for the app shell; offline falls back to cached index.
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put("/index.html", copy));
          return response;
        })
        .catch(() => caches.match("/index.html")),
    );
    return;
  }

  if (
    url.pathname.startsWith("/assets/") ||
    url.pathname.startsWith("/icons/") ||
    url.pathname === "/manifest.json" ||
    url.pathname === "/favicon.ico"
  ) {
    // Stale-while-revalidate for hashed build assets and icons.
    event.respondWith(
      caches.match(request).then((cached) => {
        const refresh = fetch(request)
          .then((response) => {
            if (response.ok) {
              const copy = response.clone();
              caches.open(ASSET_CACHE).then((cache) => cache.put(request, copy));
            }
            return response;
          })
          .catch(() => cached);
        return cached || refresh;
      }),
    );
  }
});
