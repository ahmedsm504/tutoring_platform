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
    self.registration.showNotification(title, {
        body: body,
        icon: '/static/images/logo.jpeg'
    });
});