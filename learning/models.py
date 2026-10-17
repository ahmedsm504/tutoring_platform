"""الواجبات (بتسجيل صوتي) + نقاط الطالب من الواجبات والألعاب."""
from datetime import timedelta

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from . import quran


def hw_path(instance, filename):
    return f"homework/{timezone.now():%Y/%m}/{filename}"


class Homework(models.Model):
    KIND_CHOICES = [
        ('memorize', 'حفظ جديد'),
        ('review', 'مراجعة'),
        ('recite', 'تلاوة وتصحيح'),
        ('other', 'نشاط آخر'),
    ]
    teacher = models.ForeignKey('core.Teacher', on_delete=models.CASCADE, related_name='homeworks', verbose_name="المعلمة")
    student = models.ForeignKey('core.Student', on_delete=models.CASCADE, related_name='homeworks', verbose_name="الطالب")
    title = models.CharField(max_length=160, verbose_name="عنوان الواجب")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='memorize', verbose_name="النوع")
    surah = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="السورة")
    ayah_from = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="من آية")
    ayah_to = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="إلى آية")
    instructions = models.TextField(blank=True, default='', verbose_name="التعليمات")
    teacher_audio = models.FileField(upload_to=hw_path, blank=True, null=True, verbose_name="شرح صوتي من المعلمة")
    due_date = models.DateField(null=True, blank=True, verbose_name="آخر موعد")
    seen_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "واجب"
        verbose_name_plural = "الواجبات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.student.name}"

    @property
    def range_label(self):
        return quran.range_label(self.surah, self.ayah_from, self.ayah_to)

    def verses(self):
        if not self.surah:
            return []
        return quran.verses(self.surah, self.ayah_from or 1, self.ayah_to)

    def latest(self):
        subs = getattr(self, '_prefetched_objects_cache', {}).get('submissions')
        if subs is not None:
            return max(subs, key=lambda s: s.id) if subs else None
        return self.submissions.order_by('-id').first()

    def status(self):
        s = self.latest()
        if not s:
            return 'new'
        return s.status

    def status_label(self):
        return {'new': 'جديد', 'submitted': 'مستني تصحيح المعلمة', 'approved': 'ممتاز ✓', 'redo': 'محتاج تسجيل تاني'}[self.status()]

    def is_overdue(self):
        return bool(self.due_date and self.status() in ('new', 'redo') and self.due_date < timezone.localdate())


class Submission(models.Model):
    STATUS_CHOICES = [('submitted', 'اتسلّم'), ('approved', 'مقبول'), ('redo', 'إعادة')]
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions', verbose_name="الواجب")
    audio = models.FileField(upload_to=hw_path, blank=True, null=True, verbose_name="تسجيل الطالب")
    audio_mime = models.CharField(max_length=60, blank=True, default='')
    note = models.TextField(blank=True, default='', verbose_name="ملاحظة الطالب")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='submitted', verbose_name="الحالة")
    stars = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="التقييم (من 5)")
    feedback = models.TextField(blank=True, default='', verbose_name="تعليق المعلمة")
    feedback_audio = models.FileField(upload_to=hw_path, blank=True, null=True, verbose_name="تعليق صوتي")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت التسليم")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت التصحيح")
    feedback_seen = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "تسليم واجب"
        verbose_name_plural = "تسليمات الواجبات"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"تسليم {self.homework}"


class StudentActivity(models.Model):
    """كل نجمة الطالب كسبها (واجب / لعبة / استماع) - منها بنحسب النجوم والسلسلة والأوسمة"""
    KIND_CHOICES = [('homework', 'واجب'), ('game', 'لعبة'), ('listen', 'استماع')]
    student = models.ForeignKey('core.Student', on_delete=models.CASCADE, related_name='activities', verbose_name="الطالب")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    detail = models.CharField(max_length=60, blank=True, default='')
    points = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "نشاط طالب"
        verbose_name_plural = "أنشطة الطلاب"
        ordering = ['-created_at']

    @classmethod
    def total_points(cls, student):
        return cls.objects.filter(student=student).aggregate(t=Sum('points'))['t'] or 0

    @classmethod
    def streak(cls, student):
        """كام يوم ورا بعض الطالب عمل فيهم أي نشاط (لحد النهارده أو امبارح)"""
        days = set(timezone.localtime(d).date() for d in
                   cls.objects.filter(student=student, created_at__gte=timezone.now() - timedelta(days=120))
                   .values_list('created_at', flat=True))
        today = timezone.localdate()
        d = today if today in days else today - timedelta(days=1)
        n = 0
        while d in days:
            n += 1
            d -= timedelta(days=1)
        return n
