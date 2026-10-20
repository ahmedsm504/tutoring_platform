"""إشعارات الأسئلة كلها في مكان واحد (كانت متكررة في الأدمن والإشارات فكانت بتتبعت مرتين).

- سؤال جديد من زائر (pending)  → إشعار + إيميل للأدمن عشان يراجعه.
- السؤال اتعمد (أول مرة)        → إشعار للكل: «سؤال جديد مُجاب» أو «سؤال جديد».
- إجابة رسمية اتضافت بعد الاعتماد → إشعار «تمت الإجابة» + إيميل للمشتركين في السؤال.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from accounts.notifications import send_admin_notification, send_in_background, send_public_notification
from core.indexnow import send_indexnow

from .models import PublicQuestion, QuestionAnswer

logger = logging.getLogger(__name__)
BASE = 'https://alagme.com'


def _question_url(q):
    return f'/questions/question/{q.slug}/'


def notify_question(question, answered=None):
    """إشعار عام للسؤال المعتمد، مرة واحدة بس."""
    now = timezone.now()
    updated = PublicQuestion.objects.filter(pk=question.pk, push_sent_at__isnull=True).update(push_sent_at=now)
    question.push_sent_at = question.push_sent_at or now  # عشان أي save تاني لنفس الـ object ميرجّعهاش فاضية
    if not updated:
        return False
    if answered is None:
        answered = QuestionAnswer.objects.filter(question_id=question.pk).exists()
    send_in_background(
        send_public_notification,
        title='❓ سؤال جديد مُجاب' if answered else '❓ سؤال جديد',
        message=question.title,
        url=_question_url(question),
    )
    return True


def _email_admins_new_question(question):
    admins = [email for _, email in getattr(settings, 'ADMINS', []) if email]
    if not admins:
        return
    send_mail(
        f'سؤال جديد يحتاج مراجعة: {question.title[:60]}',
        (f'العنوان: {question.title}\nمن: {question.visitor_name}\n'
         f'البريد: {question.visitor_email or "غير متوفر"}\n\n{question.question_text[:500]}\n\n'
         f'للمراجعة: {BASE}/admin/qna/publicquestion/{question.pk}/change/'),
        settings.DEFAULT_FROM_EMAIL, admins, fail_silently=True,
    )


def _email_subscribers(question, answer):
    from .models import QuestionSubscription
    url = BASE + _question_url(question)
    for sub in QuestionSubscription.objects.filter(question=question, is_active=True).select_related('user'):
        email = sub.user.email if sub.user_id else sub.email
        if email:
            send_mail(
                f'تمت الإجابة على سؤال تتابعه: {question.title[:60]}',
                f'{question.title}\n\n{answer.answer_text[:400]}...\n\nاقرأ الإجابة كاملة: {url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True,
            )


@receiver(pre_save, sender=PublicQuestion)
def cache_old_status(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        instance._old_status = PublicQuestion.objects.filter(pk=instance.pk).values_list('status', flat=True).first()


@receiver(post_save, sender=PublicQuestion)
def on_question_saved(sender, instance, created, **kwargs):
    try:
        if created and instance.status == 'pending':
            send_in_background(
                send_admin_notification,
                title='📝 سؤال جديد يحتاج مراجعة',
                message=instance.title,
                url=f'/admin/qna/publicquestion/{instance.pk}/change/',
            )
            send_in_background(_email_admins_new_question, instance)
            return

        # الإشعار العام للسؤال المعتمد اللي ليه إجابة بس؛ من غير إجابة بيستنى on_answer_saved
        if (instance.status == 'approved' and instance.push_sent_at is None
                and QuestionAnswer.objects.filter(question_id=instance.pk).exists()):
            notify_question(instance, answered=True)

        if instance.status == 'approved' and getattr(instance, '_old_status', None) != 'approved':
            send_indexnow(BASE + _question_url(instance))
    except Exception:
        logger.exception('فشل تجهيز إشعار السؤال %s', instance.pk)


@receiver(post_save, sender=QuestionAnswer)
def on_answer_saved(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        question = PublicQuestion.objects.get(pk=instance.question_id)
        send_in_background(_email_subscribers, question, instance)
        if question.status != 'approved':
            return  # الإشعار العام هيتبعت لما السؤال يتعمد
        if question.push_sent_at is None:
            notify_question(question, answered=True)
        elif timezone.now() - question.push_sent_at > timedelta(minutes=10):
            # السؤال اتنشر من فترة من غير إجابة، ودلوقتي اتجاوب
            send_in_background(
                send_public_notification,
                title='✅ تمت الإجابة',
                message=question.title,
                url=_question_url(question),
            )
    except Exception:
        logger.exception('فشل تجهيز إشعار الإجابة %s', instance.pk)
