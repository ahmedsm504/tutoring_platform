from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import PublicQuestion
from accounts.notifications import send_public_notification
from django.db import transaction

@receiver(pre_save, sender=PublicQuestion)
def notify_question_approved(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = PublicQuestion.objects.get(pk=instance.pk)

        if old.status != 'approved' and instance.status == 'approved':
            # 🔥 نخلي الإرسال بعد الحفظ
            transaction.on_commit(lambda: send_public_notification(
                title=f'❓ سؤال جديد: {instance.title[:50]}',
                message=instance.question_text[:100],
                url=f'https://alagme.com/questions/question/{instance.slug}/'
            ))

    except PublicQuestion.DoesNotExist:
        pass