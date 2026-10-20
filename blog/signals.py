import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from accounts.notifications import send_in_background, send_public_notification
from core.indexnow import send_indexnow

from .models import Post

logger = logging.getLogger(__name__)

# لو الحفظ جزئي (update_fields) ومفيش فيه أي حقل من دول، المحتوى ما اتغيرش ومفيش داعي نبلّغ جوجل
CONTENT_FIELDS = {
    'title', 'slug', 'content', 'excerpt', 'status', 'category', 'image', 'cloud_url',
    'image_alt', 'published_at', 'meta_description', 'keywords',
}


def notify_post(post):
    """يبعت إشعار المقال (في الخلفية) ويعلّم إنه اتبعت. بيرجع False لو كان اتبعت قبل كده."""
    # update بشرط إن الحقل لسه فاضي: لو حصل حفظين في نفس اللحظة، واحد بس اللي هيبعت
    now = timezone.now()
    updated = Post.objects.filter(pk=post.pk, push_sent_at__isnull=True).update(push_sent_at=now)
    post.push_sent_at = post.push_sent_at or now  # عشان أي save تاني لنفس الـ object ميرجّعهاش فاضية
    if not updated:
        return False
    send_in_background(
        send_public_notification,
        title='📖 مقال جديد في مدونة العجمي',
        message=post.title,
        url=f'/blog/{post.slug}/',
    )
    return True


@receiver(post_save, sender=Post)
def on_post_saved(sender, instance, created, **kwargs):
    if instance.status != 'published':
        return

    update_fields = kwargs.get('update_fields')
    if update_fields is not None and not (set(update_fields) & CONTENT_FIELDS):
        return

    # إشعار: أول مرة المقال يبقى منشور (سواء اتعمل منشور على طول أو اتنشر بعد ما كان مسودة)
    if instance.push_sent_at is None:
        try:
            notify_post(instance)
        except Exception:
            logger.exception('فشل تجهيز إشعار المقال: %s', instance.slug)

    # IndexNow (دالة send_indexnow نفسها مابترميش أخطاء)
    send_indexnow(f'https://alagme.com/blog/{instance.slug}/')
