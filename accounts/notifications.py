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
_key_project = ''  # project_id بتاع المفتاح المستخدم
WEB_PROJECT = 'alagme-notifications'  # المشروع اللي الموقع بيسجل فيه المتصفحات (base.html)
_last_error = ''   # آخر سبب فشل (بيظهر في صفحة حالة الإشعارات في الأدمن)


def last_error():
    return _last_error


def key_project():
    return _key_project


# أسماء متغيرات مقبولة للمفتاح (الأول هو المعتمد، والباقي عشان لو اتكتب باسم تاني)
ENV_NAMES = ('FIREBASE_CREDENTIALS_JSON', 'FIREBASE_CREDENTIALS', 'FIREBASE_SERVICE_ACCOUNT',
             'FIREBASE_KEY', 'GOOGLE_CREDENTIALS_JSON')


def _parse_key(raw):
    """يقرا مفتاح الـ service account مهما كانت طريقة لصقه: JSON عادي، أو بين علامات تنصيص،
    أو Base64، ويصلح \\n في private_key."""
    import base64

    def attempt(text):
        data = json.loads(text)
        if isinstance(data, str):  # JSON متغلف مرتين
            data = json.loads(data)
        return data

    s = raw.strip()
    candidates = [s]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        candidates.append(s[1:-1].strip())
    try:
        candidates.append(base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8').strip())
    except Exception:
        pass
    data, err = None, None
    for c in candidates:
        try:
            data = attempt(c)
            if isinstance(data, dict):
                break
        except Exception as e:  # نجرب الشكل اللي بعده
            err = e
    if not isinstance(data, dict):
        raise ValueError(f'مش قادر أقرا المفتاح كـ JSON: {err}')
    key = data.get('private_key', '')
    if '\\n' in key and '\n' not in key:
        data['private_key'] = key.replace('\\n', '\n')
    if data.get('type') != 'service_account':
        raise ValueError('ده مش ملف service account (لازم يكون فيه "type": "service_account").')
    return data


def _ensure_app():
    global _app_ready, _last_error, _key_project
    if _app_ready is not None:
        return _app_ready
    try:
        try:
            import firebase_admin
            from firebase_admin import credentials
        except ImportError:
            _last_error = 'مكتبة firebase-admin مش متثبتة على السيرفر (لازم تكون في requirements.txt).'
            _app_ready = False
            return False

        if firebase_admin._apps:
            _app_ready = True
            return True

        firebase_json = next((os.environ.get(k) for k in ENV_NAMES if os.environ.get(k)), None)
        firebase_file = os.environ.get('FIREBASE_CREDENTIALS_FILE')
        if firebase_json:
            data = _parse_key(firebase_json)
            _key_project = data.get('project_id', '')
            cred = credentials.Certificate(data)
        elif firebase_file and os.path.exists(firebase_file):
            cred = credentials.Certificate(firebase_file)
        else:
            logger.warning('Firebase مش متظبط (FIREBASE_CREDENTIALS_JSON فاضي) - الإشعارات متوقفة.')
            _last_error = 'متغير FIREBASE_CREDENTIALS_JSON مش موجود في Railway (أو اسمه مكتوب غلط).'
            _app_ready = False
            return False

        firebase_admin.initialize_app(cred)
        _app_ready = True
    except Exception as e:
        logger.exception('فشل تهيئة Firebase')
        _last_error = f'المفتاح موجود بس فيه مشكلة: {type(e).__name__}: {str(e)[:200]}'
        _app_ready = False
    return _app_ready


def is_configured():
    """True لو مفتاح Firebase موجود والتهيئة نجحت."""
    return bool(_ensure_app())


def _absolute(url):
    if url.startswith('http'):
        return url
    from django.conf import settings
    return getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/') + url


def _send(tokens, title, message, url):
    if not tokens or not _ensure_app():
        return None
    from firebase_admin import messaging

    url = _absolute(url)
    title, message = (title or '')[:120], (message or '')[:240]
    responses = []
    # FCM بيقبل 500 توكن كحد أقصى في الرسالة الواحدة
    for i in range(0, len(tokens), 500):
        chunk = tokens[i:i + 500]
        msg = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=message),
            data={'url': url},
            webpush=messaging.WebpushConfig(
                headers={'TTL': '172800'},
                fcm_options=messaging.WebpushFCMOptions(link=url),
                notification=messaging.WebpushNotification(
                    icon=_absolute('/static/images/icon-192.png'),
                    badge=_absolute('/static/images/favicon.png'),
                    dir='rtl', lang='ar',
                ),
            ),
            tokens=chunk,
        )
        resp = messaging.send_each_for_multicast(msg)
        responses.append((chunk, resp))
        if resp.failure_count and not resp.success_count:
            global _last_error
            first = next((r.exception for r in resp.responses if r.exception is not None), None)
            _last_error = f'الإرسال فشل: {type(first).__name__}: {str(first)[:200]}' if first else 'الإرسال فشل'
    _cleanup(responses)
    return responses


def _cleanup(responses):

    # تنظيف التوكنات اللي بقت مش صالحة (المستخدم لغى الإذن أو مسح المتصفح)
    try:
        from accounts.models import FCMToken
        dead = []
        for tokens, response in responses:
            dead += [
                tokens[i] for i, r in enumerate(response.responses)
                if not r.success and r.exception is not None
                and type(r.exception).__name__ in ('UnregisteredError', 'SenderIdMismatchError', 'InvalidArgumentError')
            ]
        if dead:
            FCMToken.objects.filter(token__in=dead).delete()
    except Exception:
        logger.exception('فشل تنظيف توكنات FCM')


def send_in_background(func, *args, **kwargs):
    """يبعت الإشعار في thread منفصل بعد ما الحفظ يخلص، عشان صفحة الأدمن متستناش Firebase."""
    import threading

    from django.db import close_old_connections, transaction

    def run():
        try:
            func(*args, **kwargs)
        except Exception:
            logger.exception('فشل إرسال إشعار في الخلفية')
        finally:
            close_old_connections()

    def start():
        threading.Thread(target=run, daemon=True).start()

    transaction.on_commit(start)


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
