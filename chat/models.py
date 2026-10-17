"""الشات الداخلي بين المعلمة والطالب (تحت إشراف الإدارة).

- محادثة واحدة لكل طالب، بين الطالب (أو ولي أمره من نفس الحساب) ومعلمته الحالية.
- مفيش أي رقم تليفون بيظهر لأي طرف، وأي محاولة لتبادل وسيلة تواصل خاصة بتتمنع.
- الإدارة شايفة كل حاجة (حتى الرسايل اللي اتمنعت)، والمشرفة بتتابع معلماتها.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

ONLINE_SECONDS = 25
TYPING_SECONDS = 6


class Conversation(models.Model):
    student = models.OneToOneField(
        'core.Student', on_delete=models.CASCADE, related_name='chat', verbose_name="الطالب",
    )
    is_locked = models.BooleanField(default=False, verbose_name="المحادثة مقفولة من الإدارة")
    is_flagged = models.BooleanField(default=False, db_index=True, verbose_name="فيها رسائل محتاجة مراجعة")
    admin_note = models.TextField(blank=True, default='', verbose_name="ملاحظة الإدارة (مش بتظهر لحد)")

    teacher_unread = models.PositiveIntegerField(default=0, verbose_name="غير مقروء للمعلمة")
    student_unread = models.PositiveIntegerField(default=0, verbose_name="غير مقروء للطالب")
    admin_unread = models.PositiveIntegerField(default=0, verbose_name="جديد للإدارة")

    teacher_seen_at = models.DateTimeField(null=True, blank=True, editable=False)
    student_seen_at = models.DateTimeField(null=True, blank=True, editable=False)
    teacher_typing_at = models.DateTimeField(null=True, blank=True, editable=False)
    student_typing_at = models.DateTimeField(null=True, blank=True, editable=False)

    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="آخر رسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ البداية")

    class Meta:
        verbose_name = "محادثة"
        verbose_name_plural = "المحادثات"
        ordering = ['-last_message_at', '-id']

    def __str__(self):
        return f"محادثة {self.student.name}"

    @property
    def teacher(self):
        return self.student.teacher

    @staticmethod
    def _recent(dt, seconds):
        return bool(dt and timezone.now() - dt < timezone.timedelta(seconds=seconds))

    def teacher_online(self):
        return self._recent(self.teacher_seen_at, ONLINE_SECONDS)

    def student_online(self):
        return self._recent(self.student_seen_at, ONLINE_SECONDS)

    def teacher_typing(self):
        return self._recent(self.teacher_typing_at, TYPING_SECONDS)

    def student_typing(self):
        return self._recent(self.student_typing_at, TYPING_SECONDS)


def attachment_path(instance, filename):
    now = timezone.now()
    return f"chat/{now:%Y/%m}/{instance.conversation_id}-{filename}"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('student', 'الطالب / ولي الأمر'),
        ('teacher', 'المعلمة'),
        ('admin', 'الإدارة'),
    ]
    KIND_CHOICES = [('image', 'صورة'), ('audio', 'رسالة صوتية'), ('video', 'فيديو'), ('file', 'ملف')]
    STATUS_CHOICES = [('sent', 'اتبعتت'), ('blocked', 'اتمنعت (فيها وسيلة تواصل خاصة)')]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="المحادثة")
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES, verbose_name="المرسل")
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chat_messages_sent', verbose_name="حساب المرسل",
    )
    teacher = models.ForeignKey(
        'core.Teacher', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chat_messages', verbose_name="المعلمة وقت الرسالة",
    )
    body = models.TextField(blank=True, default='', verbose_name="النص")

    attachment = models.FileField(upload_to=attachment_path, blank=True, null=True, verbose_name="مرفق")
    attachment_kind = models.CharField(max_length=10, choices=KIND_CHOICES, blank=True, default='')
    attachment_name = models.CharField(max_length=255, blank=True, default='')
    attachment_mime = models.CharField(max_length=100, blank=True, default='')
    attachment_hidden = models.BooleanField(default=False, verbose_name="المرفق مخفي بقرار الإدارة")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent', db_index=True, verbose_name="الحالة")
    flagged = models.BooleanField(default=False, db_index=True, verbose_name="محتاجة مراجعة")
    flag_reasons = models.CharField(max_length=255, blank=True, default='', verbose_name="سبب التنبيه")
    flag_resolved = models.BooleanField(default=False, verbose_name="الإدارة راجعتها")

    read_at = models.DateTimeField(null=True, blank=True, verbose_name="اتقرت")
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="الوقت")

    class Meta:
        verbose_name = "رسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"{self.get_sender_type_display()} - {self.conversation} - {self.body[:40]}"

    @property
    def is_blocked(self):
        return self.status == 'blocked'

    def preview(self):
        if self.body:
            return self.body
        return {'image': '📷 صورة', 'audio': '🎙️ رسالة صوتية', 'video': '🎬 فيديو', 'file': '📄 ملف'}.get(self.attachment_kind, '')
