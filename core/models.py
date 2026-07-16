from django.db import models
from django.utils import timezone


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الدولة")
    flag_icon = models.CharField(max_length=50, default='🏳️', verbose_name="أيقونة العلم")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "دولة"
        verbose_name_plural = "الدول"
        ordering = ['name']

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم المعلمة")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="السن")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    whatsapp = models.CharField(max_length=20, blank=True, null=True, verbose_name="واتساب")
    governorate = models.CharField(max_length=100, blank=True, null=True, verbose_name="المحافظة")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الراتب الأساسي")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المكافآت")
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصومات")
    hire_date = models.DateField(default=timezone.now, verbose_name="تاريخ القبض")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "معلمة"
        verbose_name_plural = "المعلمات"
        ordering = ['name']

    def __str__(self):
        return self.name

    def current_students_count(self):
        return self.students.filter(status='active').count()

    def previous_students_count(self):
        return self.students.filter(status='inactive').count()

    def net_salary(self):
        return self.salary + self.bonus - self.deduction


class Student(models.Model):
    STATUS_CHOICES = [('active', 'مقيد'), ('inactive', 'غير مقيد')]
    PAYMENT_STATUS_CHOICES = [('paid', 'مدفوع'), ('pending', 'مستحق'), ('overdue', 'متأخر')]
    ENROLLMENT_TYPE_CHOICES = [('new', 'طالب جديد'), ('existing', 'طالب مسجل من قبل')]
    SOURCE_CHOICES = [
        ('ad', 'إعلان'),
        ('referral', 'توصية'),
        ('website', 'الموقع'),
        ('social_media', 'سوشيال ميديا'),
        ('other', 'أخرى'),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='students', verbose_name="الدولة")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="المعلمة")

    name = models.CharField(max_length=255, verbose_name="اسم الطالب")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="السن")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    governorate = models.CharField(max_length=100, blank=True, null=True, verbose_name="المحافظة")

    package_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="اسم الباقة")
    lessons_count = models.PositiveIntegerField(default=4, verbose_name="عدد الحلقات")
    subscription_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="قيمة الاشتراك")
    month = models.CharField(max_length=20, verbose_name="الشهر")

    start_date = models.DateField(default=timezone.now, verbose_name="تاريخ بداية الاشتراك")
    end_date = models.DateField(null=True, blank=True, verbose_name="تاريخ نهاية الاشتراك")
    last_payment_date = models.DateField(null=True, blank=True, verbose_name="آخر دفعة")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="حالة الدفع")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="الحالة")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات عامة")
    join_date = models.DateField(default=timezone.now, verbose_name="تاريخ التسجيل")

    enrollment_type = models.CharField(
        max_length=20, choices=ENROLLMENT_TYPE_CHOICES, default='new',
        verbose_name="نوع التسجيل"
    )
    acquisition_source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, blank=True, null=True,
        verbose_name="مصدر الطالب (لو جديد)"
    )

    class Meta:
        verbose_name = "طالب"
        verbose_name_plural = "الطلاب"
        ordering = ['name']

    def __str__(self):
        teacher_name = self.teacher.name if self.teacher else "بدون معلم"
        return f"{self.name} - {teacher_name}"

    def total_paid(self):
        return self.subscription_fee


class Payment(models.Model):
    """سجل فعلي لكل دفعة اتحصلت، بيتقسم على سنة/شهر عشان صفحة السنوات والتقارير المالية"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments', verbose_name="الطالب")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الدفع")
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="ملاحظة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإدخال")

    class Meta:
        verbose_name = "دفعة"
        verbose_name_plural = "الدفعات"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.student.name} - {self.amount} جنيه - {self.date}"


class StudentNote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notes_timeline', verbose_name="الطالب")
    note_text = models.TextField(verbose_name="نص الملاحظة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="أضيف بواسطة")

    class Meta:
        verbose_name = "ملاحظة طالب"
        verbose_name_plural = "سجل الملاحظات"
        ordering = ['-created_at']

    def __str__(self):
        return f"ملاحظة لـ {self.student.name}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('rent', 'إيجار'),
        ('marketing', 'تسويق وإعلانات'),
        ('tools', 'أدوات وتراخيص'),
        ('teachers_related', 'مصروفات متعلقة بالمعلمات'),
        ('other', 'أخرى'),
    ]

    title = models.CharField(max_length=255, verbose_name="العنوان")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other', verbose_name="التصنيف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "مصروف"
        verbose_name_plural = "المصروفات"
        ordering = ['-date']

    def __str__(self):
        return self.title
