"""منطق الشات: الإرسال، الحجب، العدادات، القراءة، والإشعارات."""
import logging
import mimetypes
import os
import threading

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from .filters import scan
from .models import ChatMessage, Conversation

logger = logging.getLogger(__name__)

# الأنواع المسموح برفعها (نوع -> (تصنيف، أقصى حجم بالميجا))
ALLOWED = {
    'image/jpeg': ('image', 8), 'image/png': ('image', 8), 'image/webp': ('image', 8), 'image/gif': ('image', 8),
    'audio/webm': ('audio', 15), 'audio/ogg': ('audio', 15), 'audio/mpeg': ('audio', 15), 'audio/mp4': ('audio', 15),
    'audio/aac': ('audio', 15), 'audio/wav': ('audio', 15), 'audio/x-wav': ('audio', 15), 'audio/amr': ('audio', 15),
    'video/mp4': ('video', 30), 'video/webm': ('video', 30), 'video/quicktime': ('video', 30),
    'application/pdf': ('file', 15),
}
ALIASES = {'audio/x-m4a': 'audio/mp4', 'audio/m4a': 'audio/mp4', 'audio/mp3': 'audio/mpeg',
           'image/jpg': 'image/jpeg', 'audio/opus': 'audio/ogg', 'audio/x-aac': 'audio/aac'}
SAFE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.webm', '.ogg', '.oga', '.opus', '.mp3', '.m4a', '.mp4',
            '.aac', '.wav', '.amr', '.mov', '.pdf'}


class SendRefused(Exception):
    pass


def conversation_for(student):
    conv, _ = Conversation.objects.get_or_create(student=student)
    return conv


def visible_messages(conv, role):
    qs = conv.messages.select_related('teacher', 'sender_user')
    if role == 'teacher':
        qs = qs.exclude(status='blocked', sender_type='student')
    elif role == 'student':
        qs = qs.exclude(status='blocked', sender_type__in=['teacher', 'admin'])
    return qs


def _clean_upload(upload):
    mime = (getattr(upload, 'content_type', '') or '').split(';')[0].strip().lower()
    mime = ALIASES.get(mime, mime)
    ext = os.path.splitext(upload.name or '')[1].lower()
    if mime not in ALLOWED:
        guessed = ALIASES.get(mimetypes.guess_type(upload.name or '')[0] or '', mimetypes.guess_type(upload.name or '')[0] or '')
        mime = guessed
    if mime not in ALLOWED or (ext and ext not in SAFE_EXT):
        raise SendRefused('نوع الملف ده مش مسموح. المسموح: صور، رسائل صوتية، فيديو قصير، أو PDF.')
    kind, max_mb = ALLOWED[mime]
    if upload.size > max_mb * 1024 * 1024:
        raise SendRefused(f'حجم الملف أكبر من {max_mb} ميجا.')
    if not ext:
        upload.name = f"{kind}{mimetypes.guess_extension(mime) or ''}"
    return mime, kind


def send_message(conv, *, role, user, text='', upload=None):
    """role = student / teacher / admin. بيرجع ChatMessage (ممكن تكون اتمنعت)."""
    text = (text or '').strip()
    if not text and not upload:
        raise SendRefused('اكتب رسالة أو اختار ملف.')
    if len(text) > 4000:
        raise SendRefused('الرسالة طويلة جدًا.')
    if conv.is_locked and role != 'admin':
        raise SendRefused('المحادثة دي مقفولة مؤقتًا من الإدارة.')
    if role in ('student', 'teacher') and not conv.student.teacher_id:
        raise SendRefused('الطالب لسه ملوش معلمة.')

    mime = kind = None
    if upload:
        mime, kind = _clean_upload(upload)

    res = scan(text) if (text and role != 'admin') else None
    blocked = bool(res and res.is_strong)
    soft = bool(res and res.is_soft and not blocked)

    msg = ChatMessage(
        conversation=conv, sender_type=role, sender_user=user, teacher=conv.student.teacher,
        body=text, status='blocked' if blocked else 'sent',
        flagged=blocked or soft, flag_reasons=(res.reasons()[:255] if res and (blocked or soft) else ''),
        attachment_kind=kind or '', attachment_mime=mime or '',
        attachment_name=(os.path.basename(upload.name)[:255] if upload else ''),
    )
    if upload and not blocked:
        msg.attachment = upload
    msg.save()

    upd = {'last_message_at': timezone.now(), 'admin_unread': F('admin_unread') + 1}
    if blocked or soft:
        upd['is_flagged'] = True
    if not blocked:
        if role == 'student':
            upd['teacher_unread'] = F('teacher_unread') + 1
            upd['student_typing_at'] = None
        elif role == 'teacher':
            upd['student_unread'] = F('student_unread') + 1
            upd['teacher_typing_at'] = None
        else:
            upd['teacher_unread'] = F('teacher_unread') + 1
            upd['student_unread'] = F('student_unread') + 1
    Conversation.objects.filter(pk=conv.pk).update(**upd)

    if blocked or soft:
        _alert_admin(conv, role, 'blocked' if blocked else 'flagged')
    if not blocked:
        transaction.on_commit(lambda: _push(conv, msg))
    return msg


def mark_seen(conv, role):
    """الطرف ده فاتح المحادثة: علّم رسايل الطرف التاني كمقروءة وحدّث "متصل الآن"."""
    now = timezone.now()
    if role == 'teacher':
        conv.messages.filter(sender_type='student', read_at__isnull=True, status='sent').update(read_at=now)
        Conversation.objects.filter(pk=conv.pk).update(teacher_unread=0, teacher_seen_at=now)
    elif role == 'student':
        conv.messages.filter(sender_type__in=['teacher', 'admin'], read_at__isnull=True, status='sent').update(read_at=now)
        Conversation.objects.filter(pk=conv.pk).update(student_unread=0, student_seen_at=now)
    elif role == 'admin':
        Conversation.objects.filter(pk=conv.pk).update(admin_unread=0)


def set_typing(conv, role):
    field = {'teacher': 'teacher_typing_at', 'student': 'student_typing_at'}.get(role)
    if field:
        Conversation.objects.filter(pk=conv.pk).update(**{field: timezone.now()})


def _alert_admin(conv, role, kind):
    who = 'الطالب/ولي الأمر' if role == 'student' else f'المعلمة {conv.student.teacher.name if conv.student.teacher else ""}'
    text = (f'{who} حاول يبعت وسيلة تواصل خاصة في محادثة {conv.student.name} (اتمنعت)'
            if kind == 'blocked' else f'رسالة محتاجة مراجعة من {who} في محادثة {conv.student.name}')
    if conv.student.teacher_id:
        try:
            from core.models import TeacherActivity
            TeacherActivity.log_chat_flag(conv.student.teacher, conv.student.name,
                                          kind if role == 'teacher' else ('student' if kind == 'blocked' else 'flagged'))
        except Exception:
            logger.exception('فشل تسجيل تنبيه الشات')
    url = settings.CANONICAL_URL.rstrip('/') + reverse('chat_admin_thread', args=[conv.student_id])
    _background(lambda: _admin_push(text, url))


def _admin_push(text, url):
    from accounts.notifications import send_admin_notification
    send_admin_notification('⚠️ تنبيه في الشات', text, url=url)


def _push(conv, msg):
    """إشعار للطرف التاني حتى لو المتصفح مقفول (Firebase) - في الخلفية عشان الإرسال يفضل لحظي"""
    student, teacher = conv.student, conv.student.teacher
    base = settings.CANONICAL_URL.rstrip('/')
    preview = msg.preview()[:120]
    targets = []
    if msg.sender_type in ('student',) and teacher and teacher.user_id:
        targets.append((teacher.user, f'💬 {student.name}', base + reverse('chat_teacher_thread', args=[student.pk])))
    if msg.sender_type in ('teacher', 'admin') and student.user_id:
        title = f"💬 {'المعلمة ' + teacher.name if msg.sender_type == 'teacher' and teacher else 'إدارة المنصة'}"
        targets.append((student.user, title, base + reverse('student_chat')))
    if msg.sender_type == 'admin' and teacher and teacher.user_id:
        targets.append((teacher.user, f'🏢 الإدارة - {student.name}', base + reverse('chat_teacher_thread', args=[student.pk])))
    if not targets:
        return

    def job():
        from accounts.notifications import send_user_notification
        for user, title, url in targets:
            send_user_notification([user], title, preview, url=url, tag=f'chat-{conv.pk}')
    _background(job)


def _background(fn):
    if getattr(settings, 'CHAT_PUSH_SYNC', False):  # في الاختبارات
        fn()
        return
    threading.Thread(target=_safe(fn), daemon=True).start()


def _safe(fn):
    def run():
        try:
            fn()
        except Exception:
            logger.exception('فشل إشعار في الخلفية')
    return run


def unread_summary(user):
    """للـ badge والإشعار اللحظي في كل صفحات البورتال"""
    q = None
    if hasattr(user, 'core_student'):
        conv = Conversation.objects.filter(student=user.core_student).first()
        count = conv.student_unread if conv else 0
        last = (ChatMessage.objects.filter(conversation=conv, sender_type__in=['teacher', 'admin'], status='sent',
                                           read_at__isnull=True).order_by('-id').first() if conv else None)
        url = reverse('student_chat')
        if last:
            who = 'الإدارة' if last.sender_type == 'admin' else (f'المعلمة {last.teacher.name}' if last.teacher else 'المعلمة')
            q = {'id': last.id, 'title': who, 'text': last.preview()[:120], 'url': url}
        return {'count': count, 'latest': q}
    if hasattr(user, 'teacher_profile'):
        t = user.teacher_profile
        convs = Conversation.objects.filter(student__teacher=t)
        count = sum(convs.values_list('teacher_unread', flat=True))
        last = (ChatMessage.objects.filter(conversation__student__teacher=t, status='sent', read_at__isnull=True)
                .filter(Q(sender_type='student')).select_related('conversation__student').order_by('-id').first())
        if last:
            q = {'id': last.id, 'title': last.conversation.student.name, 'text': last.preview()[:120],
                 'url': reverse('chat_teacher_thread', args=[last.conversation.student_id])}
        return {'count': count, 'latest': q}
    if user.is_staff:
        flagged = Conversation.objects.filter(is_flagged=True).count()
        return {'count': flagged, 'latest': None}
    return {'count': 0, 'latest': None}
