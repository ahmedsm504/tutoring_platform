

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

// 📩 استقبال الإشعار في الخلفية
messaging.onBackgroundMessage((payload) => {
    console.log("📩 Background Message:", payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/images/logo.jpeg',
        data: {
            url: payload.fcmOptions?.link || "https://alagme.com"
        }
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});


// 👇🔥 لما المستخدم يضغط على الإشعار
self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    const urlToOpen = event.notification.data.url || "https://alagme.com";

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then((clientList) => {
            // لو التاب مفتوحة بالفعل
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if (client.url.includes("alagme.com") && 'focus' in client) {
                    client.navigate(urlToOpen);
                    return client.focus();
                }
            }
            // لو مش مفتوحة
            return clients.openWindow(urlToOpen);
        })
    );
});