// CampusFlow Service Worker — Web Push Handler (sw.js)
/* eslint-disable no-restricted-globals */

self.addEventListener('push', event => {
  if (!event.data) {
    return;
  }

  try {
    const data = event.data.json();
    const title = data.title || 'CampusFlow Notification';
    const options = {
      body: data.body || '',
      icon: '/favicon.svg',
      badge: '/favicon.svg',
      data: data.data || {},
      requireInteraction: data.priority === 'CRITICAL',
    };

    event.waitUntil(self.registration.showNotification(title, options));
  } catch (err) {
    console.error('Error processing push event:', err);
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();

  const rawUrl = event.notification.data?.url || '/notifications';
  // Safe deep link validation: ensure relative path or same origin
  const targetUrl = rawUrl.startsWith('/') ? rawUrl : '/notifications';

  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then(windowClients => {
        for (const client of windowClients) {
          if ('focus' in client) {
            if (client.url.includes(self.location.origin)) {
              client.navigate(targetUrl);
              return client.focus();
            }
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});
