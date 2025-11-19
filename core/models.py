from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import date

# ===============================
#           Teacher Model
# ===============================
class Teacher(models.Model):
    JOB_TITLES = [
        ('junior', 'معلم مبتدئ'),
        ('intermediate', 'معلم متوسط'),
        ('senior', 'معلم خبير'),
        ('master', 'معلم متميز'),
    ]

    name = models.CharField(max_length=255, verbose_name="اسم المعلم")
    job_title = models.CharField(max_length=20, choices=JOB_TITLES, default='junior', verbose_name="الوظيفة")
    
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الراتب الشهري")
    working_hours = models.PositiveIntegerField(default=0, verbose_name="عدد ساعات العمل")
    
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="مكافآت")
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="خصومات")

    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    start_date = models.DateField(default=timezone.now, verbose_name="تاريخ التعيين")

    def total_students(self):
        """ يحسب عدد الطلاب المرتبطين بالمعلم """
        return self.students.count()

    def __str__(self):
        return f"{self.name} - {self.get_job_title_display()}"


# ===============================
#           Student Model
# ===============================
class Student(models.Model):
    SESSION_DURATION_CHOICES = [
        (30, "30 دقيقة"),
        (40, "40 دقيقة"),
        (60, "60 دقيقة"),
    ]

    LESSONS_COUNT_CHOICES = [
        (4, "4 حلقات"),
        (6, "6 حلقات"),
        (8, "8 حلقات"),
        (12, "12 حلقة"),
        (16, "16 حلقة"),
    ]

    PAYMENT_TYPES = [
        ('monthly', 'شهري'),
        ('per_lesson', 'حسب الحلقة'),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="المعلم"
    )

    name = models.CharField(max_length=255, verbose_name="اسم الطالب")

    session_duration = models.PositiveIntegerField(
        choices=SESSION_DURATION_CHOICES,
        default=30,
        verbose_name="مدة الحلقة"
    )

    lessons_count = models.PositiveIntegerField(
        choices=LESSONS_COUNT_CHOICES,
        default=4,
        verbose_name="عدد الحلقات"
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        default='monthly',
        verbose_name="نظام الدفع"
    )

    # السعر لكل حلقة أو المبلغ الشهري
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="المبلغ المدفوع"
    )

    join_date = models.DateField(default=timezone.now, verbose_name="تاريخ الانضمام")

    def total_paid(self):
        """ يحسب المبلغ الفعلي حسب نوع الدفع """
        if self.payment_type == 'per_lesson':
            return self.paid_amount * self.lessons_count
        return self.paid_amount

    def __str__(self):
        return f"{self.name} - {self.teacher.name if self.teacher else 'بدون معلم'}"


# ===============================
#           Expense Model
# ===============================
class Expense(models.Model):
    title = models.CharField(max_length=255, verbose_name="العنوان")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return self.title


# ===============================
#           Dashboard Helper Methods
# ===============================
class FinanceHelper:

    @staticmethod
    def total_income():
        return sum(student.total_paid() for student in Student.objects.all())

    @staticmethod
    def total_salaries():
        return sum(t.salary for t in Teacher.objects.all())

    @staticmethod
    def total_expenses():
        return sum(e.amount for e in Expense.objects.all())

    @staticmethod
    def net_profit():
        return FinanceHelper.total_income() - (FinanceHelper.total_salaries() + FinanceHelper.total_expenses())

    @staticmethod
    def monthly_revenue(year=None, month=None):
        """إجمالي الإيرادات لشهر معين"""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        students = Student.objects.filter(join_date__year=year, join_date__month=month)
        return sum(s.total_paid() for s in students)

    @staticmethod
    def monthly_expenses(year=None, month=None):
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        expenses = Expense.objects.filter(date__year=year, date__month=month)
        return sum(e.amount for e in expenses)
