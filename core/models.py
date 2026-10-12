import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

# سعر الحصة الافتراضي (جنيه) - بيتحدد لكل معلمة في حقل Teacher.lesson_rate
DEFAULT_LESSON_RATE = 20

# المعلمة تقدر تغيّر تسجيلها (تمت/غياب...) بنفسها لمدة كام دقيقة بعد ما تسجل - بعدها بيتقفل ويفضل للمشرفة/الإدارة
TEACHER_REMARK_WINDOW_MINUTES = 60


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
    hire_date = models.DateField(null=True, blank=True, verbose_name="تاريخ بداية العمل")

    # حساب دخول المعلمة نفسها (مش أدمن، صلاحياته محدودة على بياناتها هي بس)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='teacher_profile',
        verbose_name="حساب الدخول"
    )

    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=60,
        verbose_name="نسبة المعلمة من الاشتراكات (%)"
    )
    fixed_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="راتب مثبت (بدل النسبة)"
    )
    # الراتب بقى بالحلقة: عدد الحلقات اللي *تمت* × سعر الحصة
    # (commission_percent و fixed_salary فاضلين في الجدول للتوثيق بس ومبقوش بيتحسبوا)
    lesson_rate = models.DecimalField(
        max_digits=8, decimal_places=2, default=DEFAULT_LESSON_RATE,
        verbose_name="سعر الحصة"
    )

    supervisor = models.ForeignKey(
        'Supervisor', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='teachers', verbose_name="المشرفة المسؤولة"
    )

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

    def total_subscriptions(self, year=None, month=None):
        """إجمالي اللي اتحصل فعليًا (دفعات حقيقية) من طلابها *المقيدين* فقط
        (اللي status = active).

        مهم جدًا: الدالة دي بتحسب عن *شهر واحد بس* (افتراضيًا الشهر الحالي لو
        مبعتيش year/month) وده عشان لو الطالب دفع في شهور مختلفة، كل دفعة تدخل
        في حساب راتب شهرها هي بس، مش تتجمع مع بعض وتتحسب تاني في كل مرة
        (وده كان سبب إن الراتب كان بيتضاعف). لو عايزة إجمالي كل العمر مرة واحدة
        استخدمي total_subscriptions_all_time().
        """
        now = timezone.now()
        year = year or now.year
        month = month or now.month
        active_students = self.students.filter(status='active')
        return sum(float(s.total_paid(year=year, month=month)) for s in active_students)

    def total_subscriptions_all_time(self):
        """إجمالي كل الدفعات الفعلية من طلابها المقيدين من غير أي تحديد بشهر
        (للعرض الإعلامي بس، متستخدمهاش لحساب الراتب عشان مش هتفرق بين الشهور)"""
        active_students = self.students.filter(status='active')
        return sum(float(s.total_paid()) for s in active_students)

    def completed_lessons_count(self, year=None, month=None):
        """عدد الحلقات اللي *تمت فعلًا* في الشهر (دي الوحيدة اللي بتتحسب في الراتب)"""
        return self.lessons_for_period(year, month).filter(status='completed').count()

    def calculated_salary(self, year=None, month=None):
        """الراتب المستحق عن شهر واحد (افتراضيًا الشهر الحالي) =
        عدد الحلقات اللي تمت × سعر الحصة.

        غياب الطالب / عذر / مؤجلة / ملغاة / غياب المعلمة / لسه مجدولة = مفيش أجر.
        (نسبة المعلمة والراتب المثبت القدام مبقوش بيدخلوا في الحساب)"""
        return round(self.completed_lessons_count(year, month) * float(self.lesson_rate), 2)

    def platform_share(self, year=None, month=None):
        """نصيب المنصة من اشتراكات الشهر بعد مستحق المعلمة"""
        return round(self.total_subscriptions(year=year, month=month) - self.calculated_salary(year, month), 2)

    def salary_records_for(self, year=None, month=None):
        """سجلات الصرف الفعلية اللي تاريخ صرفها في الشهر ده"""
        now = timezone.now()
        year = year or now.year
        month = month or now.month
        return self.salary_records.filter(payout_date__year=year, payout_date__month=month)

    def paid_salary(self, year=None, month=None):
        """اللي اتدفع لها *فعليًا* في الشهر ده (الصافي = أساسي + مكافآت - خصومات)"""
        return round(sum(r.net_amount() for r in self.salary_records_for(year, month)), 2)

    def paid_base_salary(self, year=None, month=None):
        """الجزء الأساسي (من الحلقات) اللي اتصرف في الشهر ده من غير المكافآت والخصومات"""
        return round(sum(float(r.base_amount) for r in self.salary_records_for(year, month)), 2)

    def remaining_salary(self, year=None, month=None):
        """المتبقي للصرف عن الشهر = المستحق من الحلقات - الأساسي اللي اتصرف قبل كده"""
        return round(max(self.calculated_salary(year, month) - self.paid_base_salary(year, month), 0), 2)

    def deductions_summary(self, year=None, month=None):
        """عدد الخصومات المسجلة في الشهر (سجلات صرف فيها خصم > 0) وإجماليها"""
        recs = [r for r in self.salary_records_for(year, month) if r.deduction and float(r.deduction) > 0]
        return {'count': len(recs), 'total': round(sum(float(r.deduction) for r in recs), 2)}

    def has_salary_record_for(self, year, month):
        """هل اتصرفلها راتب عن الشهر ده قبل كده؟ (عشان نمنع صرف راتب نفس الشهر مرتين)"""
        return self.salary_records.filter(payout_date__year=year, payout_date__month=month).exists()

    def lessons_for_period(self, year=None, month=None):
        now = timezone.now()
        year = year or now.year
        month = month or now.month
        return self.lessons.filter(scheduled_at__year=year, scheduled_at__month=month)

    def monthly_lesson_stats(self, year=None, month=None):
        """إحصائيات الحضور والانضباط عن شهر واحد (افتراضيًا الشهر الحالي):
        عدد الحلقات، المكتملة، غياب الطالب (وضمنها اللي محدش سجلها فعتُبرت
        غياب تلقائي)، غياب المعلمة، الملغاة، التأخيرات، ونسب الالتزام/الحضور/التسجيل"""
        qs = self.lessons_for_period(year, month)
        total = qs.count()
        completed = student_absent = teacher_absent = cancelled = late = excused = 0
        unrecorded = 0  # عدد الحلقات اللي محدش سجلها يدويًا (اتحسبت غياب تلقائي) - رقم فرعي داخل student_absent

        for lesson in qs:
            eff = lesson.effective_status()
            if eff == 'completed':
                completed += 1
            elif eff == 'student_absent':
                student_absent += 1
                if lesson.was_auto_defaulted():
                    unrecorded += 1
            elif eff == 'teacher_absent':
                teacher_absent += 1
            elif eff == 'cancelled':
                cancelled += 1
            elif eff == 'excused':
                excused += 1
            if lesson.was_late:
                late += 1

        countable = total - cancelled  # الملغاة مش بتتحاسب في نسبة الالتزام
        commitment_rate = round((completed / countable * 100), 1) if countable else 100.0
        attendance_rate = round(((countable - teacher_absent) / countable * 100), 1) if countable else 100.0
        recording_rate = round(((total - unrecorded) / total * 100), 1) if total else 100.0
        overall_rating = round((commitment_rate + attendance_rate + recording_rate) / 3, 1)

        ded = self.deductions_summary(year, month)

        return {
            'excused': excused, 'postponed': cancelled,
            'absent_total': student_absent + excused + teacher_absent,
            'lesson_rate': float(self.lesson_rate),
            'salary_due': round(completed * float(self.lesson_rate), 2),
            'salary_paid': self.paid_salary(year, month),
            'deductions_count': ded['count'], 'deductions_total': ded['total'],
            'total': total, 'completed': completed, 'student_absent': student_absent,
            'teacher_absent': teacher_absent, 'cancelled': cancelled, 'unregistered': unrecorded,
            'late': late, 'complaints': self.complaints_count(year, month),
            'commitment_rate': commitment_rate, 'attendance_rate': attendance_rate,
            'recording_rate': recording_rate, 'overall_rating': overall_rating,
        }

    def complaints_count(self, year=None, month=None):
        qs = self.complaints.all()
        if year:
            qs = qs.filter(date__year=year)
        if month:
            qs = qs.filter(date__month=month)
        return qs.count()


class Supervisor(models.Model):
    """مشرفة مسؤولة عن مجموعة معلمات (بحد أقصى مقترح 5) - بتتابع حلقاتهم وطلابهم يوميًا"""
    name = models.CharField(max_length=255, verbose_name="اسم المشرفة")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='supervisor_profile',
        verbose_name="حساب الدخول"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشطة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "مشرفة"
        verbose_name_plural = "المشرفات"
        ordering = ['name']

    def __str__(self):
        return self.name

    def teachers_count(self):
        return self.teachers.count()

    def today_lessons(self):
        today = timezone.localdate()
        return Lesson.objects.filter(teacher__supervisor=self, scheduled_at__date=today).order_by('scheduled_at')


class CurriculumDocument(models.Model):
    """ملفات المنهج (بي دي إف) اللي بتشوفها المعلمة جوه بورتالها بس - زي منهج الحفظ أو المصحف"""
    title = models.CharField(max_length=255, verbose_name="عنوان الملف")
    file = models.FileField(upload_to='curriculum/%Y/%m/', verbose_name="ملف PDF")
    is_quran = models.BooleanField(default=False, verbose_name="هل هو المصحف؟")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط (ظاهر للمعلمات)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "ملف منهج"
        verbose_name_plural = "ملفات المنهج"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class TeacherSalaryRecord(models.Model):
    """سجل كل مرة اتصرف فيها راتب لمعلمة - تاريخ الصرف + خصومات/مكافآت/إجازات خاصة بالمرة دي بالذات"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salary_records', verbose_name="المعلمة")
    payout_date = models.DateField(default=timezone.now, verbose_name="تاريخ الصرف")
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الراتب الأساسي (محسوب وقت الصرف)")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المكافآت")
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصومات")
    leave_days = models.PositiveIntegerField(default=0, verbose_name="عدد أيام الإجازة")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")

    class Meta:
        verbose_name = "سجل راتب"
        verbose_name_plural = "سجل الرواتب"
        ordering = ['-payout_date', '-created_at']

    def net_amount(self):
        return round(float(self.base_amount) + float(self.bonus) - float(self.deduction), 2)

    def __str__(self):
        return f"{self.teacher.name} - {self.payout_date}"


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

    def total_paid(self, year=None, month=None):
        """إجمالي اللي دفعه الطالب فعليًا (من سجل الدفعات الحقيقي Payment)،
        مش القيمة الاسمية للاشتراك اللي ممكن يكون لسه ماتدفعتش.
        لو حددتي year/month، بيرجع بس دفعات الشهر ده (مهم عشان حساب راتب
        المعلمة الشهري ميتكررش)"""
        qs = self.payments.all()
        if year:
            qs = qs.filter(date__year=year)
        if month:
            qs = qs.filter(date__month=month)
        total = qs.aggregate(total=models.Sum('amount'))['total']
        return total or 0

    def is_paid_for(self, year=None, month=None):
        """هل دفع فعليًا (فيه دفعة مسجلة) في الشهر ده؟ - الأدق من حقل payment_status
        اللي بيفضل 'مدفوع' بعد أول دفعة ومبيرجعش لـ 'مستحق' لما شهر جديد يبدأ"""
        now = timezone.now()
        return float(self.total_paid(year=year or now.year, month=month or now.month)) > 0

    def lessons_completed_count(self):
        """كام حلقة اتعملت فعلًا للطالب ده من كل حلقاته المسجلة في السيستم"""
        return self.lessons.filter(status='completed').count()

    def lessons_progress_label(self):
        """عدد الحلقات المطلوبة (من الباقة) مقابل اللي تمت فعلًا - '3 من 8' مثلًا"""
        return f"{self.lessons_completed_count()} من {self.lessons_count}"


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


class MonthlyEvaluation(models.Model):
    """نموذج تقييم ومتابعة أداء شهري لطالب - قابل للتحميل PDF أو المشاركة برابط عام لولي الأمر"""
    TEMPLATE_CHOICES = [
        ('teal_pink', 'تركواز ووردي'),
        ('violet', 'بنفسجي (هوية المنصة)'),
        ('sunny', 'أصفر وبرتقالي دافئ'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='evaluations', verbose_name="الطالب")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="رمز المشاركة العام")

    # بيانات مأخوذة وقت إنشاء التقييم (بتفضل ثابتة حتى لو بيانات الطالب اتغيرت بعدين)
    student_name = models.CharField(max_length=255, verbose_name="اسم الطالب")
    teacher_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="اسم المعلمة")
    package_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="الباقة")
    lessons_count = models.PositiveIntegerField(default=4, verbose_name="عدد الحلقات")
    month_label = models.CharField(max_length=30, verbose_name="الشهر")

    # ملخص الإنجاز
    memorization_progress = models.CharField(max_length=255, blank=True, null=True, verbose_name="مقدار حفظ الجديد")
    review_progress = models.CharField(max_length=255, blank=True, null=True, verbose_name="مقدار المراجعة")
    absences = models.CharField(max_length=255, blank=True, null=True, verbose_name="عدد مرات الغياب")

    # تقييم المهارات
    pronunciation_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="النطق ومخارج الحروف")
    tajweed_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="تطبيق أحكام التجويد")
    interaction_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="التفاعل مع المعلمة")
    response_speed_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="سرعة الاستجابة والحفظ")
    commitment_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="الالتزام بالمواعيد والآداب")

    recommendations = models.TextField(blank=True, null=True, verbose_name="التوصيات / المستوى العام")
    teacher_comment = models.TextField(blank=True, null=True, verbose_name="كلمة المعلمة")
    month_rating = models.CharField(max_length=100, blank=True, null=True, verbose_name="مستوى الشهر")

    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='teal_pink', verbose_name="شكل النموذج")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "تقييم شهري"
        verbose_name_plural = "التقييمات الشهرية"
        ordering = ['-created_at']

    def __str__(self):
        return f"تقييم {self.student_name} - {self.month_label}"


class Lesson(models.Model):
    """حلقة واحدة (موعد) بين معلمة وطالب - العمود الفقري لمتابعة الحضور والانضباط"""
    STATUS_CHOICES = [
        ('scheduled', 'مجدولة'),
        ('completed', 'تمت'),
        ('student_absent', 'الطالب غائب'),
        ('excused', 'عذر'),
        ('teacher_absent', 'المعلمة لم تتمكن من الحضور'),
        ('cancelled', 'مؤجلة'),
        ('unregistered', 'غير مسجلة'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lessons', verbose_name="الطالب")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons', verbose_name="المعلمة")

    scheduled_at = models.DateTimeField(verbose_name="موعد الحلقة")
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="مدة الحلقة (دقيقة)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="الحالة")
    status_recorded_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت تسجيل الحالة")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت بدء الحلقة فعليًا")
    auto_flagged = models.BooleanField(default=False, verbose_name="اتحسبت غياب تلقائيًا من غير ما تتسجل")
    was_late = models.BooleanField(default=False, verbose_name="اتأخرت المعلمة في الحضور")

    # مين أضاف الحلقة ومين سجل حالتها (للمتابعة والتدقيق)
    CREATOR_CHOICES = [('admin', 'الإدارة / المشرفة'), ('teacher', 'المعلمة')]
    RECORDER_CHOICES = [('teacher', 'المعلمة'), ('supervisor', 'المشرفة'), ('admin', 'الإدارة')]
    created_by = models.CharField(max_length=10, choices=CREATOR_CHOICES, default='admin', verbose_name="أضافها")
    recorded_by = models.CharField(max_length=12, choices=RECORDER_CHOICES, blank=True, default='', verbose_name="سجّل الحالة")

    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات على الحلقة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "حلقة"
        verbose_name_plural = "الحلقات"
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.student.name} - {self.scheduled_at:%Y-%m-%d %H:%M}"

    def end_time(self):
        return self.scheduled_at + timezone.timedelta(minutes=self.duration_minutes)

    def is_due_soon(self, minutes=15):
        """هتبدأ خلال كام دقيقة (للتنبيه قبل الحلقة)"""
        now = timezone.now()
        return self.status == 'scheduled' and self.scheduled_at <= now + timezone.timedelta(minutes=minutes) and now < self.scheduled_at

    def is_ongoing_or_due(self):
        """حان موعدها دلوقتي (بين بداية الحلقة ونهايتها) وبتستنى تسجيل حالة"""
        now = timezone.now()
        return self.status == 'scheduled' and self.scheduled_at <= now <= self.end_time()

    def is_overdue_unrecorded(self):
        """انتهى وقتها ومفيش حد سجل حالتها"""
        return self.status == 'scheduled' and timezone.now() > self.end_time()

    def effective_status(self):
        """الحالة الفعلية للعرض والحساب: لو الوقت فات ومفيش حد سجل حالتها،
        بتتحسب غياب تلقائيًا (مش حالة منفصلة اسمها "غير مسجلة") - زي ما
        اتفقنا: أي حلقة محدش سجلها = غياب"""
        if self.is_overdue_unrecorded():
            return 'student_absent'
        return self.status

    def was_auto_defaulted(self):
        """هل الحالة دي طالعة تلقائي كغياب لأن محدش سجلها (مش تسجيل يدوي فعلي)؟
        مفيد للإدارة عشان تفرق بين غياب متسجل فعلًا وغياب افتراضي محتاج متابعة"""
        return self.is_overdue_unrecorded()

    def earned_amount(self):
        """أجر الحلقة دي للمعلمة: سعر الحصة لو *تمت* فعلًا، وصفر لأي حالة تانية"""
        return float(self.teacher.lesson_rate) if self.status == 'completed' else 0.0

    def table_group(self):
        """تصنيف الحلقة في جدول المعلمة: completed / absent / postponed / upcoming"""
        eff = self.effective_status()
        if eff == 'completed':
            return 'completed'
        if eff in ('student_absent', 'excused', 'teacher_absent', 'unregistered'):
            return 'absent'
        if eff == 'cancelled':
            return 'postponed'
        return 'upcoming'

    def status_label(self):
        """اسم الحالة بالتفصيل للعرض في الجدول"""
        if self.was_auto_defaulted():
            return 'غياب (لم تُسجَّل)'
        return self.get_status_display()

    def mark_started(self):
        """المعلمة بتضغط "بدء الحلقة" الساعة اللي بتبدأ فيها فعليًا"""
        self.started_at = timezone.now()
        self.save(update_fields=['started_at'])

    def mark(self, new_status, was_late=False, by=''):
        """تسجيل حالة الحلقة + وقت التسجيل + مين سجلها (teacher / supervisor / admin)"""
        self.status = new_status
        self.status_recorded_at = timezone.now()
        self.auto_flagged = False
        self.was_late = was_late
        self.recorded_by = by
        self.save(update_fields=['status', 'status_recorded_at', 'auto_flagged', 'was_late', 'recorded_by'])

    # ---------- صلاحيات المعلمة على حلقاتها ----------
    TEACHER_MARK_LABELS = {
        'completed': '✅ تمت',
        'student_absent': '🔴 الطالب غاب',
        'excused': '📝 عذر',
        'cancelled': '⏸ مؤجلة',
    }

    def teacher_mark_options(self, now=None):
        """الحالات اللي تقدر المعلمة تسجلها دلوقتي للحلقة دي (فاضية = مقفولة عليها).
        - لسه ما اتسجلتش (حتى لو فات وقتها) أو هي اللي سجلتها من أقل من ساعة -> تقدر تسجل/تعدل.
        - 'تمت' و'الطالب غاب' مينفعوش قبل موعد بداية الحلقة (عشان متسجلش حلقة لسه ما حصلتش).
        - 'عذر' و'مؤجلة' مسموحين في أي وقت.
        - لو المشرفة أو الإدارة سجلت الحالة بتتقفل على المعلمة."""
        now = now or timezone.now()
        recent_own = (
            self.recorded_by == 'teacher' and self.status_recorded_at
            and now - self.status_recorded_at <= timezone.timedelta(minutes=TEACHER_REMARK_WINDOW_MINUTES)
        )
        if not (self.status == 'scheduled' or recent_own):
            return []
        options = ['excused', 'cancelled']
        if now >= self.scheduled_at:
            options = ['completed', 'student_absent'] + options
        return [o for o in options if o != self.status]

    def teacher_mark_choices(self):
        """(القيمة, الاسم) لعرض أزرار التسجيل في القوالب"""
        return [(s, self.TEACHER_MARK_LABELS[s]) for s in self.teacher_mark_options()]

    def teacher_can_delete(self, now=None):
        """المعلمة تقدر تمسح بس حلقة هي اللي أضافتها ولسه مجدولة وموعدها لسه ما جاش"""
        now = now or timezone.now()
        return self.created_by == 'teacher' and self.status == 'scheduled' and self.scheduled_at > now

    def record_delay_minutes(self):
        """عدد الدقايق بين موعد الحلقة ووقت تسجيل حالتها (None لو لسه ما اتسجلتش)"""
        if not self.status_recorded_at:
            return None
        return int((self.status_recorded_at - self.scheduled_at).total_seconds() // 60)

    def record_delay_label(self):
        """نص التأخير في التسجيل لو عدّى ساعة، وإلا فاضي"""
        return _delay_label(self.record_delay_minutes())

    def added_after_time(self):
        """المعلمة أضافت الحلقة دي بعد ما موعدها فات (أكتر من 5 دقايق) - علامة للمتابعة"""
        return self.created_by == 'teacher' and self.created_at and self.created_at > self.scheduled_at + timezone.timedelta(minutes=5)

    def recorded_by_label(self):
        return dict(self.RECORDER_CHOICES).get(self.recorded_by, '')


class ScheduleRequest(models.Model):
    """طلب إضافة موعد جديد أو تعديل موعد قائم - المعلمة تقترح والإدارة توافق"""
    REQUEST_TYPE_CHOICES = [
        ('new', 'موعد جديد'),
        ('change', 'تعديل موعد قائم'),
    ]
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='schedule_requests', verbose_name="الطالب")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedule_requests', verbose_name="المعلمة")
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES, default='new', verbose_name="نوع الطلب")

    related_lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='change_requests', verbose_name="الحلقة المطلوب تعديلها (لو تعديل)"
    )

    proposed_days = models.CharField(max_length=150, blank=True, null=True, verbose_name="الأيام المقترحة")
    proposed_time = models.TimeField(null=True, blank=True, verbose_name="الوقت المقترح")
    proposed_datetime = models.DateTimeField(null=True, blank=True, verbose_name="الموعد المقترح (لتعديل حلقة بعينها)")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    teacher_note = models.CharField(max_length=255, blank=True, null=True, verbose_name="ملاحظة المعلمة")
    admin_note = models.CharField(max_length=255, blank=True, null=True, verbose_name="ملاحظة الإدارة")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")

    class Meta:
        verbose_name = "طلب موعد"
        verbose_name_plural = "طلبات المواعيد"
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب {self.get_request_type_display()} - {self.student.name}"

    def approve(self, admin_note=''):
        self.status = 'approved'
        self.admin_note = admin_note
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'admin_note', 'reviewed_at'])

        if self.request_type == 'change' and self.related_lesson and self.proposed_datetime:
            self.related_lesson.scheduled_at = self.proposed_datetime
            self.related_lesson.status = 'scheduled'
            self.related_lesson.status_recorded_at = None
            self.related_lesson.recorded_by = ''
            self.related_lesson.save(update_fields=['scheduled_at', 'status', 'status_recorded_at', 'recorded_by'])
        elif self.request_type == 'new' and self.proposed_datetime:
            Lesson.objects.create(
                student=self.student,
                teacher=self.teacher,
                scheduled_at=self.proposed_datetime,
            )

    def reject(self, admin_note=''):
        self.status = 'rejected'
        self.admin_note = admin_note
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'admin_note', 'reviewed_at'])


class TeacherComplaint(models.Model):
    """شكوى مسجلة على معلمة (بتدخل في تقييمها الشهري)"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='complaints', verbose_name="المعلمة")
    description = models.TextField(verbose_name="تفاصيل الشكوى")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")

    class Meta:
        verbose_name = "شكوى على معلمة"
        verbose_name_plural = "شكاوى المعلمات"
        ordering = ['-date']

    def __str__(self):
        return f"شكوى - {self.teacher.name} - {self.date}"


def _delay_label(minutes):
    """'بعد 3 ساعات' / 'بعد يومين' للتأخير الأكبر من ساعة، وإلا نص فاضي"""
    if not minutes or minutes <= 60:
        return ''
    if minutes < 24 * 60:
        return f'بعد {minutes // 60} ساعة من موعدها'
    return f'بعد {minutes // (24 * 60)} يوم من موعدها'


class TeacherActivity(models.Model):
    """سجل نشاط المعلمات (إضافة حلقات / تسجيل حالة / حذف) - بيظهر للأدمن لحظيًا مع تنبيه صوتي"""
    KIND_CHOICES = [
        ('added', 'أضافت حلقات'),
        ('marked', 'سجّلت حالة حلقة'),
        ('removed', 'حذفت حلقة'),
    ]
    STATUS_WORDS = {
        'completed': '✅ تمت',
        'student_absent': '🔴 الطالب غاب',
        'excused': '📝 عذر',
        'cancelled': '⏸ مؤجلة',
    }

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='activities', verbose_name="المعلمة")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities', verbose_name="الحلقة")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, verbose_name="النوع")
    status = models.CharField(max_length=20, blank=True, default='', verbose_name="الحالة المسجلة")
    student_name = models.CharField(max_length=255, blank=True, verbose_name="الطالب")
    lesson_at = models.DateTimeField(null=True, blank=True, verbose_name="موعد الحلقة")
    count = models.PositiveIntegerField(default=1, verbose_name="العدد")
    delay_minutes = models.IntegerField(null=True, blank=True, verbose_name="التسجيل بعد موعد الحلقة (دقيقة)")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="وقت النشاط")

    class Meta:
        verbose_name = "نشاط معلمة"
        verbose_name_plural = "نشاط المعلمات"
        ordering = ['-id']

    def __str__(self):
        return f"{self.teacher.name} - {self.text()}"

    @classmethod
    def log(cls, teacher, kind, lesson, status='', count=1):
        delay = None
        if kind == 'marked' and lesson.scheduled_at:
            delay = int((timezone.now() - lesson.scheduled_at).total_seconds() // 60)
        return cls.objects.create(
            teacher=teacher, kind=kind, status=status, count=count, delay_minutes=delay,
            lesson=None if kind == 'removed' else lesson,
            student_name=lesson.student.name, lesson_at=lesson.scheduled_at,
        )

    def lesson_when(self):
        if not self.lesson_at:
            return ''
        lt = timezone.localtime(self.lesson_at)
        return f"{lt:%Y/%m/%d} الساعة {lt:%H:%M}"

    def delay_label(self):
        return _delay_label(self.delay_minutes)

    def text(self):
        when = self.lesson_when()
        if self.kind == 'added':
            if self.count > 1:
                return f"أضافت {self.count} حلقات مع {self.student_name} ابتداءً من {when}"
            return f"أضافت حلقة مع {self.student_name} يوم {when}"
        if self.kind == 'removed':
            return f"حذفت حلقة {self.student_name} ({when})"
        s = f"سجّلت حلقة {self.student_name} ({when}): {self.STATUS_WORDS.get(self.status, self.status)}"
        late = self.delay_label()
        return f"{s} · {late}" if late else s

    def tone(self):
        if self.kind == 'marked':
            return {'completed': 'ok', 'student_absent': 'bad'}.get(self.status, 'warn')
        return 'info'

    def short_time(self):
        return f"{timezone.localtime(self.created_at):%H:%M}"
