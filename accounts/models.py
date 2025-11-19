# accounts/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# ==========================================
# نموذج المستخدم المخصص
# ==========================================
class User(AbstractUser):
    """
    نموذج المستخدم الأساسي مع دعم أنواع مختلفة
    """
    USER_TYPES = (
        ('student', 'طالب'),
        ('supervisor', 'مشرف'),
        ('admin', 'مدير'),
    )
    
    user_type = models.CharField(
        max_length=15,
        choices=USER_TYPES,
        default='student',
        verbose_name="نوع المستخدم"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الهاتف"
    )
    country = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="الدولة"
    )

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


# ==========================================
# اختيارات الجلسات والحلقات
# ==========================================
SESSION_DURATION_CHOICES = [
    (30, "30 دقيقة"),
    (40, "40 دقيقة"),
    (60, "60 دقيقة"),
]

LESSONS_COUNT_CHOICES = [
    (4, "4 حلقات"),
    (8, "8 حلقات"),
    (12, "12 حلقة"),
    (16, "16 حلقة"),
]


# ==========================================
# نموذج ملف الطالب
# ==========================================
class StudentProfile(models.Model):
    """
    ملف شخصي للطالب يحتوي على كل المعلومات الإضافية
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="المستخدم",
        related_name="student_profile"
    )
    full_name = models.CharField(
        max_length=100,
        verbose_name="الاسم الكامل"
    )
    country = models.CharField(
        max_length=50,
        verbose_name="الدولة"
    )
    phone = models.CharField(
        max_length=15,
        verbose_name="رقم الهاتف"
    )
    parent_phone = models.CharField(
        max_length=15,
        verbose_name="رقم هاتف ولي الأمر"
    )
    age = models.PositiveIntegerField(
        default=10,
        verbose_name="العمر"
    )
    lessons_count = models.PositiveIntegerField(
        choices=LESSONS_COUNT_CHOICES,
        default=4,
        verbose_name="عدد الحلقات"
    )
    session_duration = models.PositiveIntegerField(
        choices=SESSION_DURATION_CHOICES,
        default=30,
        verbose_name="مدة الجلسة"
    )
    package_name = models.CharField(
        max_length=100,
        verbose_name="اسم الباقة"
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'supervisor'},
        related_name='students',
        verbose_name="المشرف"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ التسجيل"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    class Meta:
        verbose_name = "ملف طالب"
        verbose_name_plural = "ملفات الطلاب"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_lessons_count_display()})"

    def get_total_sessions(self):
        """عدد الجلسات الكلي"""
        return self.sessions.count()

    def get_attended_sessions(self):
        """عدد الجلسات التي حضرها"""
        return self.sessions.filter(status='present').count()

    def get_attendance_rate(self):
        """نسبة الحضور"""
        total = self.get_total_sessions()
        if total == 0:
            return 0
        return (self.get_attended_sessions() / total) * 100


# ==========================================
# نموذج الجلسات
# ==========================================
class Session(models.Model):
    """
    جلسة دراسية لطالب معين
    """
    STATUS_CHOICES = (
        ('present', 'حاضر'),
        ('absent', 'غائب'),
        ('', 'غير محدد'),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="الطالب"
    )
    date = models.DateTimeField(
        verbose_name="تاريخ ووقت الجلسة"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='',
        blank=True,
        verbose_name="الحالة"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "جلسة"
        verbose_name_plural = "الجلسات"
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date.strftime('%Y-%m-%d %H:%M')}"

    def get_status_display_ar(self):
        """عرض الحالة بالعربية"""
        status_map = {
            'present': '✓ حاضر',
            'absent': '✗ غائب',
            '': '- غير محدد'
        }
        return status_map.get(self.status, 'غير محدد')


# ==========================================
# نموذج الرسائل
# ==========================================
class Message(models.Model):
    """
    رسالة بين المستخدمين (طالب ومشرف)
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="المرسل"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name="المستقبل"
    )
    content = models.TextField(
        verbose_name="المحتوى"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="مقروءة"
    )

    class Meta:
        verbose_name = "رسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['sender', 'recipient']),
        ]

    def __str__(self):
        status = "✓" if self.is_read else "✗"
        return f"{status} {self.sender.username} → {self.recipient.username}: {self.content[:30]}"

    def mark_as_read(self):
        """تحديد الرسالة كمقروءة"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


# ==========================================
# نموذج حجز التجربة
# ==========================================
class TrialBooking(models.Model):
    """
    حجز حصة تجريبية
    """
    GENDER_CHOICES = (
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name="الاسم"
    )
    country = models.CharField(
        max_length=100,
        verbose_name="الدولة"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        verbose_name="الجنس"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="رقم الهاتف"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="البريد الإلكتروني"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الحجز"
    )
    is_contacted = models.BooleanField(
        default=False,
        verbose_name="تم التواصل"
    )

    class Meta:
        verbose_name = "حجز تجربة"
        verbose_name_plural = "حجوزات التجربة"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.get_gender_display()})"