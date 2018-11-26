var CACHE_VERSION = 17;

// Shorthand identifier mapped to specific versioned cache.
var CURRENT_CACHES = {
  main: 'main-cache-v' + CACHE_VERSION
};

var URLS = ['/', '/contact', '/faq', '/demande', '/mentions-legales', '/stats']

self.addEventListener('activate', function(event) {
  var expectedCacheNames = Object.values(CURRENT_CACHES);

  // Active worker won't be treated as activated until promise
  // resolves successfully.
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          console.log('Found cache:', cacheName)
          if (!expectedCacheNames.includes(cacheName)) {
            console.log('Deleting out of date cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', function(event) {
  if (event.request.method != 'GET') return;

  console.log('Handling fetch event for:', event.request);
  console.log('With cache:', CURRENT_CACHES['main'])

  event.respondWith(
    // Opens Cache objects that start with 'main'.
    caches.open(CURRENT_CACHES['main']).then(function(cache) {
      return cache.match(event.request).then(function(response) {
        if (response) {
          console.log('Found response in cache:', response);
          return response;
        }

        console.log('Fetching request from the network:', event.request.url);

        return fetch(event.request).then(function(networkResponse) {
          return networkResponse;
        });
      }).catch(function(error) {
        // Handles exceptions that arise from match() or fetch().
        console.error('Error in fetch handler:', error);
        throw error;
      });
    })
  );
});

self.addEventListener('install', function (event) {
  console.log('Installing ServiceWorker', CURRENT_CACHES['main'])

  event.waitUntil(
    caches.open(CURRENT_CACHES['main']).then(function(cache) {
      return cache.addAll(URLS)
    })
  )
})
