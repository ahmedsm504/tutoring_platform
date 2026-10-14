import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from accounts.notifications import send_public_notification
from core.indexnow import send_indexnow

logger = logging.getLogger(__name__)

# لو الحفظ جزئي (update_fields) ومفيش فيه أي حقل من دول، المحتوى ما اتغيرش ومفيش داعي نبلّغ جوجل
CONTENT_FIELDS = {
    'title', 'slug', 'content', 'excerpt', 'status', 'category', 'image', 'cloud_url',
    'image_alt', 'published_at', 'meta_description', 'keywords',
}


@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    if instance.status != 'published':
        return

    update_fields = kwargs.get('update_fields')
    if update_fields is not None and not (set(update_fields) & CONTENT_FIELDS):
        return

    url = f"https://alagme.com/blog/{instance.slug}/"

    # إشعار (للمقال الجديد بس)
    if created:
        try:
            send_public_notification(title="📖 مقال جديد!", message=instance.title, url=url)
        except Exception:
            logger.exception("فشل إرسال إشعار المقال الجديد: %s", url)

    # IndexNow (دالة send_indexnow نفسها مابترميش أخطاء)
    send_indexnow(url)
