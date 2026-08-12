import uuid
from django.db import models
from django.conf import settings
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

    def calculated_salary(self, year=None, month=None):
        """الراتب المستحق عن شهر واحد بس (افتراضيًا الشهر الحالي):
        مثبت لو موجود، وإلا نسبة من اشتراكات الشهر ده تحديدًا"""
        if self.fixed_salary is not None:
            return round(float(self.fixed_salary), 2)
        return round(self.total_subscriptions(year=year, month=month) * (float(self.commission_percent) / 100), 2)

    def platform_share(self, year=None, month=None):
        """نصيب المنصة من نفس الشهر"""
        if self.fixed_salary is not None:
            return round(self.total_subscriptions(year=year, month=month) - float(self.fixed_salary), 2)
        return round(self.total_subscriptions(year=year, month=month) * (1 - float(self.commission_percent) / 100), 2)

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
        completed = student_absent = teacher_absent = cancelled = late = 0
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
            if lesson.was_late:
                late += 1

        countable = total - cancelled  # الملغاة مش بتتحاسب في نسبة الالتزام
        commitment_rate = round((completed / countable * 100), 1) if countable else 100.0
        attendance_rate = round(((countable - teacher_absent) / countable * 100), 1) if countable else 100.0
        recording_rate = round(((total - unrecorded) / total * 100), 1) if total else 100.0
        overall_rating = round((commitment_rate + attendance_rate + recording_rate) / 3, 1)

        return {
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
        ('teacher_absent', 'المعلمة لم تتمكن من الحضور'),
        ('cancelled', 'أُلغيت'),
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

    def mark_started(self):
        """المعلمة بتضغط "بدء الحلقة" الساعة اللي بتبدأ فيها فعليًا"""
        self.started_at = timezone.now()
        self.save(update_fields=['started_at'])

    def mark(self, new_status, was_late=False):
        self.status = new_status
        self.status_recorded_at = timezone.now()
        self.auto_flagged = False
        self.was_late = was_late
        self.save(update_fields=['status', 'status_recorded_at', 'auto_flagged', 'was_late'])


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
            self.related_lesson.save(update_fields=['scheduled_at', 'status', 'status_recorded_at'])
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
