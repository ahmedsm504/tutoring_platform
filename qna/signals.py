from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import PublicQuestion
from accounts.notifications import send_public_notification
from django.db import transaction


@receiver(pre_save, sender=PublicQuestion)
def cache_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = PublicQuestion.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except PublicQuestion.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=PublicQuestion)
def notify_question_approved(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, '_old_status', None)

    if old_status and old_status != 'approved' and instance.status == 'approved':
        transaction.on_commit(lambda: send_public_notification(
            title=f'❓ سؤال جديد: {instance.title[:50]}',
            message=instance.question_text[:100],
            url=f'https://alagme.com/questions/question/{instance.slug}/'
        ))