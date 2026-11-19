from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Video


@receiver(post_save, sender=Video)
def ping_indexnow(sender, instance, **kwargs):
    if instance.is_published and instance.slug:
        from django.conf import settings
        from core.indexnow import send_indexnow
        base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
        send_indexnow(base + instance.get_absolute_url())
        send_indexnow(base + '/videos/')
