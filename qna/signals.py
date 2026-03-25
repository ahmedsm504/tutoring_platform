from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PublicQuestion
from accounts.notifications import send_public_notification


@receiver(post_save, sender=PublicQuestion)
def notify_question_approved(sender, instance, created, **kwargs):
    # ❌ لو لسه جديد
    if created:
        return

    # ✅ يبعت مرة واحدة بس
    if instance.status == 'approved' and not instance.notification_sent:
        send_public_notification(
            title=f'❓ سؤال جديد: {instance.title[:50]}',
            message=instance.question_text[:100],
            url=f'https://alagme.com/questions/question/{instance.slug}/'
        )

        # 🔥 نعلم إنه اتبعت
        instance.notification_sent = True
        instance.save(update_fields=['notification_sent'])