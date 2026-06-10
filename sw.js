// 每日靈糧 Service Worker — 同源檔案 network-first（更新會即時生效、離線也能開）
const CACHE = 'daily-bread-v1';
const SHELL = [
  './', './index.html', './planner.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png',
  './data/schedule.json', './data/yt_map.json', './data/summary.json',
  './data/bible_books.json', './data/reading_order.json', './data/split_days.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()).catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.map(k => k !== CACHE ? caches.delete(k) : null)))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const u = new URL(e.request.url);
  // 只處理自家網站的檔案；經文 API / YouTube / Firebase 等外部資源不攔截，直接走網路
  if (u.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return r;
    }).catch(() => caches.match(e.request).then(m => m || caches.match('./index.html')))
  );
});
