"""تشغيل IndexNow تلقائي كل كام ساعة من جوه السيرفر نفسه (من غير cron).

أول طلب بعد ما تعدّي INTERVAL بيشغّل thread في الخلفية (مابيأخرش الزائر). القفل في قاعدة البيانات
(صف IndexNowPing خاص) فحتى لو فيه أكتر من worker بيشتغل مرة واحدة بس في المدة دي.
كل مرة: الروابط الجديدة/المتعدّلة + دفعة صغيرة من الروابط اللي بقالها أكتر من REFRESH_DAYS ما اتبلّغتش."""
import logging
import threading
import time
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

INTERVAL = timedelta(hours=3)
LOCK_URL = '__scheduler__/indexnow'
GSC_INTERVAL = timedelta(hours=20)
GSC_LOCK_URL = '__scheduler__/gsc-v2'
GSC_RETRY = timedelta(hours=1)
_next_check = 0.0
_guard = threading.Lock()


def _claim(lock_url=LOCK_URL, interval=INTERVAL):
    """True لو العملية دي هي اللي هتشغّل الدورة الجاية (قفل ذرّي في قاعدة البيانات)"""
    from core.models import IndexNowPing
    now = timezone.now()
    IndexNowPing.objects.get_or_create(url=lock_url, defaults={'pinged_at': now - interval * 2})
    return IndexNowPing.objects.filter(url=lock_url, pinged_at__lt=now - interval).update(pinged_at=now) == 1


def _run():
    from django.core.management import call_command
    from django.db import close_old_connections
    try:
        close_old_connections()
        if _claim():
            # مفيش استيراد تلقائي من يوتيوب (بطلب صاحب الموقع)؛ الفيديوهات بتتضاف من الأدمن أو يدويًا:
            # manage.py sync_youtube_channel
            call_command('indexnow_ping', '--refresh')
    except Exception:
        logger.exception('IndexNow scheduler فشل')
    try:
        if _claim(GSC_LOCK_URL, GSC_INTERVAL):
            from core import gsc
            try:
                gsc.run()  # جوجل: إعادة إرسال السايت ماب + فحص الفهرسة + تقرير المشاكل
            except Exception:
                # لو فشل (صلاحيات/شبكة) نحاول تاني بعد ساعة بدل ما نستنى يوم كامل
                from core.models import IndexNowPing
                IndexNowPing.objects.filter(url=GSC_LOCK_URL).update(
                    pinged_at=timezone.now() - GSC_INTERVAL + GSC_RETRY)
                raise
    except Exception:
        logger.exception('GSC sync فشل')
    finally:
        close_old_connections()


def maybe_run():
    global _next_check
    if settings.DEBUG or getattr(settings, 'TESTING', False):
        return
    t = time.monotonic()
    if t < _next_check:
        return
    with _guard:
        if t < _next_check:
            return
        _next_check = t + 600  # كل worker بيبص على القفل مرة كل 10 دقايق بالكتير
    threading.Thread(target=_run, name='indexnow-scheduler', daemon=True).start()


class IndexNowSchedulerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            maybe_run()
        except Exception:
            logger.exception('IndexNow scheduler')
        return response
