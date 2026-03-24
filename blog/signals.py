from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from accounts.notifications import send_push_notification

@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    if created and instance.status == 'published':
        send_push_notification(
            title=f'📝 مقالة جديدة: {instance.title[:50]}',
            message=instance.excerpt[:100] if instance.excerpt else instance.content[:100],
            url=f'https://alagme.com/blog/{instance.slug}/'
        )