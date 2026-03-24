from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from accounts.notifications import send_public_notification

@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    # لما المقال يتنشر للأول مرة أو يتغير status لـ published
    if instance.status == 'published':
        if created:
            send_public_notification(
                title="📖 مقال جديد!",
                message=instance.title,
                url=f"https://alagme.com/blog/{instance.slug}/"
            )