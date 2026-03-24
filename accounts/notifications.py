import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import json

if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    cred = credentials.Certificate(json.loads(firebase_json))
    firebase_admin.initialize_app(cred)


def send_public_notification(title, message, url="https://alagme.com"):
    """للكل — مقالات وأسئلة"""
    try:
        from accounts.models import FCMToken
        tokens = list(FCMToken.objects.values_list('token', flat=True))

        if not tokens:
            print("لا يوجد مشتركين")
            return None

        msg = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=url,
                ),
                notification=messaging.WebpushNotification(
                    icon='/static/images/logo.jpeg',
                ),
            ),
            tokens=tokens,
        )

        response = messaging.send_each_for_multicast(msg)  # ✅ الدالة الجديدة
        print(f"✅ أُرسل لـ {response.success_count} | فشل {response.failure_count}")
        return response

    except Exception as e:
        print(f"Firebase Error: {e}")
        return None


def send_admin_notification(title, message, url="https://alagme.com"):
    """للأدمن بس"""
    try:
        from accounts.models import FCMToken
        tokens = list(FCMToken.objects.filter(is_admin=True).values_list('token', flat=True))

        if not tokens:
            print("لا يوجد token للأدمن")
            return None

        msg = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=url,
                ),
                notification=messaging.WebpushNotification(
                    icon='/static/images/logo.jpeg',
                ),
            ),
            tokens=tokens,
        )

        response = messaging.send_each_for_multicast(msg)
        print(f"✅ أُرسل للأدمن")
        return response

    except Exception as e:
        print(f"Firebase Admin Error: {e}")
        return None