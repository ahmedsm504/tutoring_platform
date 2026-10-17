importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyC-X81jKdtfaMRblBEsIEl01OVga2Hqe2E",
    authDomain: "alagme-notifications.firebaseapp.com",
    projectId: "alagme-notifications",
    storageBucket: "alagme-notifications.firebasestorage.app",
    messagingSenderId: "914317417493",
    appId: "1:914317417493:web:2a9acda899a263a1c1821c"
});

const messaging = firebase.messaging();

// إشعارات المقالات (فيها notification) المتصفح بيعرضها لوحده.
// إشعارات الشات (data بس) إحنا اللي بنعرضها: رسايل نفس المحادثة بتتجمع في إشعار واحد.
messaging.onBackgroundMessage((payload) => {
    if (payload.notification) return;
    const d = payload.data || {};
    if (!d.title) return;
    self.registration.showNotification(d.title, {
        body: d.body || '',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/favicon.png',
        tag: d.tag || 'chat',
        renotify: true,
        dir: 'rtl',
        lang: 'ar',
        data: { url: d.url || '/' }
    });
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
        for (const c of list) {
            if (c.url.indexOf(url) !== -1 && 'focus' in c) return c.focus();
        }
        return clients.openWindow(url);
    }));
});
