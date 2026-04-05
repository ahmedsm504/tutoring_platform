from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from accounts.notifications import send_public_notification
from core.indexnow import send_indexnow  # 👈 ضيف ده

@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    
    if instance.status == 'published':
        url = f"https://alagme.com/blog/{instance.slug}/"

        # إشعار
        if created:
            send_public_notification(
                title="📖 مقال جديد!",
                message=instance.title,
                url=url
            )

        # 🔥 IndexNow (مهم جدًا)
        send_indexnow(url)