from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PublicQuestion
from accounts.notifications import send_public_notification

@receiver(post_save, sender=PublicQuestion)
def notify_new_question(sender, instance, created, **kwargs):
    if instance.status == 'approved':
        if created:
            send_public_notification(
                title="❓ سؤال جديد!",
                message=instance.title,
                url=f"https://alagme.com/questions/{instance.slug}/"
            )