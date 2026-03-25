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

messaging.onBackgroundMessage((payload) => {
    const { title, body } = payload.notification;
    const url = payload.data?.url || '/';

    self.registration.showNotification(title, {
        body: body,
        icon: '/static/images/logo.jpeg',
        badge: '/static/images/logo.jpeg',
        actions: [
            { action: 'open', title: '👁️ زيارة' },
            { action: 'close', title: '⏰ لاحقاً' }
        ],
        data: { url }
    });
});

// لما المستخدم يضغط على الإشعار أو على زيارة
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'close') return;

    const url = event.notification.data?.url || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // لو الموقع مفتوح خليه يفتح الـ url في نفس التاب
            for (const client of clientList) {
                if (client.url.includes('alagme.com') && 'focus' in client) {
                    client.navigate(url);
                    return client.focus();
                }
            }
            // لو مفيش تاب مفتوح افتح تاب جديد
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});