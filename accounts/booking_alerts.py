"""إشعارات الحجز للأدمن (Firebase، على المتصفحات اللي فاعلة إشعارات الأدمن):
- حجز جديد مكتمل: فورًا.
- حد كتب اسمه ورقمه في الخطوة الأولى ومكملش: بعد ABANDON_AFTER، مرة واحدة بس.
الفحص بيتعمل من core/indexnow_scheduler (كل ~10 دقايق مع الزيارات)، من غير cron."""
import logging
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)
ABANDON_AFTER = timedelta(minutes=10)


def _admin_url(b):
    return reverse('admin:accounts_trialbooking_change', args=[b.pk])


def notify_new(booking):
    from .notifications import send_admin_notification, send_in_background
    where = f' · {booking.country}' if booking.country else ''
    send_in_background(send_admin_notification, 'حجز حلقة تجريبية جديد ✅',
                       f'{booking.name} · {booking.phone}{where}', _admin_url(booking))


def notify_abandoned():
    """يبعت تنبيه لكل حجز وقف عند الخطوة الأولى بقاله أكتر من 10 دقايق (وأقل من يومين)"""
    from .models import TrialBooking
    from .notifications import send_admin_notification
    now = timezone.now()
    sent = 0
    qs = TrialBooking.objects.filter(is_complete=False, alert_sent=False,
                                     created_at__lte=now - ABANDON_AFTER, created_at__gte=now - timedelta(days=2))
    for b in qs[:20]:
        # قفل ذرّي: worker واحد بس يبعت التنبيه
        if TrialBooking.objects.filter(pk=b.pk, alert_sent=False).update(alert_sent=True) != 1:
            continue
        send_admin_notification('⚠ حد بدأ الحجز ومكملش، كلمه',
                                f'{b.name} · {b.phone}', _admin_url(b))
        sent += 1
    return sent
