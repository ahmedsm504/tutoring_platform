"""إشعارات Firebase (Web Push).

التهيئة بقت *كسولة* (lazy): مبتحصلش وقت استيراد الملف، فلو مفتاح Firebase مش
موجود على السيرفر الموقع مش هيقع - الإشعار بس مش هيتبعت وهيتسجل تحذير في اللوج.
المفتاح بيتقري من متغير البيئة FIREBASE_CREDENTIALS_JSON (محتوى ملف JSON كامل)
أو من مسار ملف في FIREBASE_CREDENTIALS_FILE.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_app_ready = None  # None = لسه ماجربناش، True/False = نتيجة آخر محاولة


def _ensure_app():
    global _app_ready
    if _app_ready is not None:
        return _app_ready
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _app_ready = True
            return True

        firebase_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        firebase_file = os.environ.get('FIREBASE_CREDENTIALS_FILE')
        if firebase_json:
            cred = credentials.Certificate(json.loads(firebase_json))
        elif firebase_file and os.path.exists(firebase_file):
            cred = credentials.Certificate(firebase_file)
        else:
            logger.warning('Firebase مش متظبط (FIREBASE_CREDENTIALS_JSON فاضي) - الإشعارات متوقفة.')
            _app_ready = False
            return False

        firebase_admin.initialize_app(cred)
        _app_ready = True
    except Exception:
        logger.exception('فشل تهيئة Firebase')
        _app_ready = False
    return _app_ready


def _send(tokens, title, message, url):
    if not tokens or not _ensure_app():
        return None
    from firebase_admin import messaging

    msg = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=message),
        webpush=messaging.WebpushConfig(
            fcm_options=messaging.WebpushFCMOptions(link=url),
            notification=messaging.WebpushNotification(icon='/static/images/logo.jpeg'),
        ),
        tokens=tokens,
    )
    response = messaging.send_each_for_multicast(msg)

    # تنظيف التوكنات اللي بقت مش صالحة (المستخدم لغى الإذن أو مسح المتصفح)
    try:
        from accounts.models import FCMToken
        dead = [
            tokens[i] for i, r in enumerate(response.responses)
            if not r.success and r.exception is not None
            and type(r.exception).__name__ in ('UnregisteredError', 'SenderIdMismatchError', 'InvalidArgumentError')
        ]
        if dead:
            FCMToken.objects.filter(token__in=dead).delete()
    except Exception:
        logger.exception('فشل تنظيف توكنات FCM')
    return response


def send_public_notification(title, message, url="https://alagme.com"):
    """للكل — مقالات وأسئلة"""
    try:
        from accounts.models import FCMToken
        tokens = list(FCMToken.objects.values_list('token', flat=True))
        return _send(tokens, title, message, url)
    except Exception:
        logger.exception('Firebase Error')
        return None


def send_admin_notification(title, message, url="https://alagme.com"):
    """للأدمن بس"""
    try:
        from accounts.models import FCMToken
        tokens = list(FCMToken.objects.filter(is_admin=True).values_list('token', flat=True))
        return _send(tokens, title, message, url)
    except Exception:
        logger.exception('Firebase Admin Error')
        return None


def send_user_notification(users, title, message, url="/", tag="chat"):
    """إشعار لمستخدمين محددين (رسايل الشات). data-only عشان الـ service worker هو اللي
    يعرضه ويجمع رسايل نفس المحادثة في إشعار واحد (tag)."""
    try:
        from accounts.models import FCMToken
        ids = [u.pk for u in users if u is not None]
        tokens = list(FCMToken.objects.filter(user_id__in=ids).values_list('token', flat=True))
        if not tokens or not _ensure_app():
            return None
        from firebase_admin import messaging
        msg = messaging.MulticastMessage(
            data={'title': title[:100], 'body': message[:240], 'url': url, 'tag': tag},
            webpush=messaging.WebpushConfig(headers={'Urgency': 'high', 'TTL': '86400'}),
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(msg)
        dead = [tokens[i] for i, r in enumerate(response.responses)
                if not r.success and r.exception is not None
                and type(r.exception).__name__ in ('UnregisteredError', 'SenderIdMismatchError', 'InvalidArgumentError')]
        if dead:
            FCMToken.objects.filter(token__in=dead).delete()
        return response
    except Exception:
        logger.exception('Firebase user notification error')
        return None
