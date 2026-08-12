from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model

User = get_user_model()
from django.contrib.auth.hashers import make_password
from django.db.models import Q, Sum
from functools import wraps
import json
import calendar
import secrets

from .models import (
    Teacher, Student, Country, StudentNote, Expense, Payment, TeacherSalaryRecord, MonthlyEvaluation,
    Lesson, ScheduleRequest, TeacherComplaint,
)


def teacher_login_required(view_func):
    """صلاحية مختلفة تمامًا عن staff_member_required: بتسمح بس للمعلمة اللي
    عندها حساب دخول (User) مربوط بيها عن طريق Teacher.user، وبتمنعها
    نهائيًا من أي صفحة إدارية تانية (لوحة الأدمن كلها staff_member_required
    ومحدش من المعلمات is_staff، فهي أصلاً برة اللوحة دي بالكامل)"""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'teacher_profile'):
            messages.error(request, 'من فضلك سجلي الدخول بحساب المعلمة الخاص بيكِ.')
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


ARABIC_MONTHS = {
    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
    7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر',
}


# =======================
# صفحات الموقع العامة
# =======================
def home(request):
    reviews = [
        'review1.jpeg', 'review2.jpeg', 'review3.jpeg', 'review4.jpeg',
        'review5.jpeg', 'review6.jpeg', 'review7.jpeg', 'review8.jpeg',
        'review9.jpeg', 'review10.jpeg', 'review11.jpeg', 'review12.jpeg',
        'review13.jpeg', 'review14.jpeg'
    ]
    return render(request, 'core/home.html', {'reviews': reviews})


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')


def pricing(request):
    return render(request, 'core/pricing.html')


def quality_standards(request):
    return render(request, 'core/quality_standards.html')


# =======================
# أدوات مساعدة صغيرة
# =======================
def _or_none(value):
    """يحول أي حقل فاضي في الفورم لـ None بدل ما يبقى string فاضي"""
    if value is None:
        return None
    value = value.strip()
    return value if value != '' else None


def _to_int_or_none(value):
    value = _or_none(value)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_decimal_or_zero(value):
    value = _or_none(value)
    if value is None:
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


# =======================
# أدوات الحسابات المالية (إيرادات / مصروفات / رواتب)
# =======================
def _student_payment_date(student):
    """التاريخ اللي بنحسب عليه إيراد الطالب: آخر دفعة لو موجودة، وإلا تاريخ بداية الاشتراك"""
    return student.last_payment_date or student.start_date


def _monthly_income(year, month):
    total = Payment.objects.filter(date__year=year, date__month=month).aggregate(
        total=Sum('amount')
    )['total']
    return total or Decimal('0')


def _monthly_expenses(year, month):
    total = Expense.objects.filter(date__year=year, date__month=month).aggregate(
        total=Sum('amount')
    )['total']
    return total or Decimal('0')


def _total_salaries():
    """إجمالي الرواتب الشهرية المحسوبة (نسبة من الاشتراكات أو راتب مثبت) لكل المعلمات"""
    total = Decimal('0')
    for t in Teacher.objects.all():
        total += Decimal(str(t.calculated_salary()))
    return total


# =======================
# الصفحة الرئيسية للنظام (كروت الدول)
# =======================
@staff_member_required
def dashboard_home(request):
    countries = Country.objects.filter(is_active=True)

    today = timezone.now().date()
    current_month_income = _monthly_income(today.year, today.month)
    current_month_expenses = _monthly_expenses(today.year, today.month)
    current_month_salaries = _total_salaries()
    current_month_profit = current_month_income - current_month_expenses - current_month_salaries

    context = {
        'countries': countries,
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='active').count(),
        'inactive_students': Student.objects.filter(status='inactive').count(),
        'total_teachers': Teacher.objects.count(),
        'current_month_name': ARABIC_MONTHS[today.month],
        'current_month_income': current_month_income,
        'current_month_expenses': current_month_expenses,
        'current_month_salaries': current_month_salaries,
        'current_month_profit': current_month_profit,
    }
    return render(request, 'core/dashboard_home.html', context)


# =======================
# طلاب دولة معينة (بحث + فلاتر)
# =======================
@staff_member_required
def country_students(request, country_id):
    country = get_object_or_404(Country, pk=country_id)
    students = country.students.all()

    status = request.GET.get('status', '')
    teacher_id = request.GET.get('teacher', '')
    month = request.GET.get('month', '').strip()
    governorate = request.GET.get('governorate', '').strip()
    q = request.GET.get('q', '').strip()

    if status:
        students = students.filter(status=status)
    if teacher_id:
        students = students.filter(teacher_id=teacher_id)
    if month:
        students = students.filter(month__icontains=month)
    if governorate:
        students = students.filter(governorate__icontains=governorate)
    if q:
        students = students.filter(name__icontains=q)

    teachers = Teacher.objects.all()

    context = {
        'country': country,
        'students': students,
        'teachers': teachers,
    }
    return render(request, 'core/country_students.html', context)


# =======================
# إضافة طالب جديد
# =======================
@staff_member_required
def add_student(request):
    countries = Country.objects.filter(is_active=True)
    teachers = Teacher.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        country_id = request.POST.get('country')

        if not name or not country_id:
            messages.error(request, 'من فضلك أدخلي اسم الطالب واختاري الدولة.')
        else:
            enrollment_type = request.POST.get('enrollment_type', 'new')
            acquisition_source = request.POST.get('acquisition_source') or None
            if enrollment_type != 'new':
                acquisition_source = None

            subscription_fee = _to_decimal_or_zero(request.POST.get('subscription_fee'))
            start_date = _or_none(request.POST.get('start_date')) or timezone.now().date()

            student = Student.objects.create(
                country_id=country_id,
                teacher_id=request.POST.get('teacher') or None,
                name=name,
                age=_to_int_or_none(request.POST.get('age')),
                phone=_or_none(request.POST.get('phone')),
                governorate=_or_none(request.POST.get('governorate')),
                package_name=_or_none(request.POST.get('package_name')),
                lessons_count=_to_int_or_none(request.POST.get('lessons_count')) or 4,
                subscription_fee=subscription_fee,
                month=request.POST.get('month', '').strip(),
                start_date=start_date,
                end_date=_or_none(request.POST.get('end_date')),
                payment_status=request.POST.get('payment_status', 'pending'),
                status=request.POST.get('status', 'active'),
                enrollment_type=enrollment_type,
                acquisition_source=acquisition_source,
            )

            note_text = request.POST.get('note_text', '').strip()
            if note_text:
                StudentNote.objects.create(
                    student=student,
                    note_text=note_text,
                    created_by=request.user.get_username() if request.user.is_authenticated else '',
                )

            # لو الطالب دفع فعلاً من الأول (حالة الدفع "مدفوع")، نسجلها كأول دفعة في سجل المدفوعات
            # عشان تظهر في صفحة "السنوات" وفي التقارير المالية مباشرة
            if request.POST.get('payment_status') == 'paid' and subscription_fee > 0:
                source_label = dict(Student.SOURCE_CHOICES).get(acquisition_source, '')
                payment_note = 'أول اشتراك (طالب جديد)' if enrollment_type == 'new' else 'أول اشتراك مسجل في النظام'
                if source_label:
                    payment_note += f' - المصدر: {source_label}'
                Payment.objects.create(
                    student=student,
                    amount=subscription_fee,
                    date=start_date,
                    note=payment_note,
                )
                student.last_payment_date = start_date
                student.save(update_fields=['last_payment_date'])

            messages.success(request, f'تم إضافة الطالب "{student.name}" بنجاح.')
            return redirect('country_students', country_id=student.country.id)

    context = {
        'countries': countries,
        'teachers': teachers,
    }
    return render(request, 'core/add_student.html', context)


# =======================
# تعديل بيانات طالب
# =======================
@staff_member_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    countries = Country.objects.filter(is_active=True)
    teachers = Teacher.objects.all()

    if request.method == 'POST':
        student.country_id = request.POST.get('country')
        student.teacher_id = request.POST.get('teacher') or None
        student.name = request.POST.get('name', '').strip()
        student.age = _to_int_or_none(request.POST.get('age'))
        student.phone = _or_none(request.POST.get('phone'))
        student.governorate = _or_none(request.POST.get('governorate'))
        student.package_name = _or_none(request.POST.get('package_name'))
        student.lessons_count = _to_int_or_none(request.POST.get('lessons_count')) or 4
        student.subscription_fee = _to_decimal_or_zero(request.POST.get('subscription_fee'))
        student.month = request.POST.get('month', '').strip()
        student.start_date = _or_none(request.POST.get('start_date')) or student.start_date
        student.end_date = _or_none(request.POST.get('end_date'))
        student.payment_status = request.POST.get('payment_status', student.payment_status)
        student.status = request.POST.get('status', student.status)
        student.notes = request.POST.get('notes', '').strip()
        enrollment_type = request.POST.get('enrollment_type', student.enrollment_type)
        student.enrollment_type = enrollment_type
        acquisition_source = request.POST.get('acquisition_source') or None
        student.acquisition_source = acquisition_source if enrollment_type == 'new' else None
        student.save()

        messages.success(request, 'تم تحديث بيانات الطالب.')
        return redirect('student_detail', student_id=student.id)

    context = {
        'student': student,
        'countries': countries,
        'teachers': teachers,
    }
    return render(request, 'core/edit_student.html', context)


# =======================
# ملف طالب فردي + سجل الملاحظات
# =======================
@staff_member_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    if request.method == 'POST':
        note_text = request.POST.get('note_text', '').strip()
        if note_text:
            StudentNote.objects.create(
                student=student,
                note_text=note_text,
                created_by=request.user.get_username() if request.user.is_authenticated else '',
            )
            messages.success(request, 'تم إضافة الملاحظة.')
        return redirect('student_detail', student_id=student.id)

    notes = student.notes_timeline.all()
    payments = student.payments.all()
    lessons = student.lessons.all()[:30]
    context = {
        'student': student,
        'notes': notes,
        'payments': payments,
        'lessons': lessons,
    }
    return render(request, 'core/student_detail.html', context)


# =======================
# تسجيل دفعة جديدة لطالب (من صفحة ملفه الشخصي مباشرة)
# =======================
@staff_member_required
def add_student_payment(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    if request.method == 'POST':
        amount = _to_decimal_or_zero(request.POST.get('amount'))
        date = _or_none(request.POST.get('date')) or timezone.now().date()
        note = request.POST.get('note', '').strip()

        if amount <= 0:
            messages.error(request, 'من فضلك أدخلي مبلغ صحيح.')
        else:
            Payment.objects.create(student=student, amount=amount, date=date, note=note)
            student.last_payment_date = date
            student.payment_status = 'paid'
            student.save(update_fields=['last_payment_date', 'payment_status'])
            messages.success(request, f'تم تسجيل دفعة بقيمة {amount} جنيه لـ {student.name}.')

    return redirect('student_detail', student_id=student.id)


# =======================
# تبديل حالة الطالب (مقيد / غير مقيد)
# =======================
@staff_member_required
def toggle_student_status(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    student.status = 'inactive' if student.status == 'active' else 'active'
    student.save()

    if student.status == 'inactive':
        messages.warning(request, f'تم تحويل "{student.name}" إلى غير مقيد.')
    else:
        messages.success(request, f'تم تحويل "{student.name}" إلى مقيد.')

    return redirect('student_detail', student_id=student.id)


# =======================
# ملف المعلمات
# =======================
@staff_member_required
def teachers_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'core/teachers_list.html', {'teachers': teachers})


@staff_member_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    students = teacher.students.all()

    now = timezone.now()
    stat_year = _to_int_or_none(request.GET.get('year')) or now.year
    stat_month = _to_int_or_none(request.GET.get('month')) or now.month

    context = {
        'teacher': teacher,
        'teacher_login_display': getattr(teacher.user, User.USERNAME_FIELD, None) if teacher.user_id else None,
        'students': students,
        'current_students': students.filter(status='active').count(),
        'previous_students': students.filter(status='inactive').count(),
        'salary_records': teacher.salary_records.all()[:12],
        'salary_this_month': teacher.calculated_salary(year=stat_year, month=stat_month),
        'subscriptions_this_month': teacher.total_subscriptions(year=stat_year, month=stat_month),
        'monthly_stats': teacher.monthly_lesson_stats(year=stat_year, month=stat_month),
        'stat_year': stat_year,
        'stat_month': stat_month,
        'stat_month_name': ARABIC_MONTHS.get(stat_month, stat_month),
        'arabic_months': ARABIC_MONTHS,
        'stat_years_range': sorted({now.year - 1, now.year, now.year + 1}, reverse=True),
        'upcoming_lessons': teacher.lessons.filter(status='scheduled', scheduled_at__gte=now).order_by('scheduled_at')[:15],
        'recent_complaints': teacher.complaints.all()[:5],
    }
    return render(request, 'core/teacher_detail.html', context)


@staff_member_required
def add_teacher(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'من فضلك أدخلي اسم المعلمة.')
        else:
            Teacher.objects.create(
                name=name,
                age=_to_int_or_none(request.POST.get('age')),
                phone=_or_none(request.POST.get('phone')),
                whatsapp=_or_none(request.POST.get('whatsapp')),
                governorate=_or_none(request.POST.get('governorate')),
                hire_date=_or_none(request.POST.get('hire_date')),
            )
            messages.success(request, 'تم إضافة المعلمة بنجاح. تقدري تظبطي نسبتها أو راتبها المثبت من صفحة "قائمة الرواتب".')
            return redirect('teachers_list')

    return render(request, 'core/add_teacher.html')


@staff_member_required
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    if request.method == 'POST':
        teacher.name = request.POST.get('name', '').strip()
        teacher.age = _to_int_or_none(request.POST.get('age'))
        teacher.phone = _or_none(request.POST.get('phone'))
        teacher.whatsapp = _or_none(request.POST.get('whatsapp'))
        teacher.governorate = _or_none(request.POST.get('governorate'))
        teacher.hire_date = _or_none(request.POST.get('hire_date'))
        teacher.save()

        messages.success(request, 'تم تحديث بيانات المعلمة.')
        return redirect('teachers_list')

    return render(request, 'core/edit_teacher.html', {'teacher': teacher})


@staff_member_required
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    if request.method == 'POST':
        name = teacher.name
        teacher.delete()
        messages.success(request, f'تم حذف المعلمة "{name}".')
        return redirect('teachers_list')

    return render(request, 'core/delete_teacher.html', {'teacher': teacher})


# =======================
# جميع الطلاب (كل الدول - ترتيب أبجدي)
# =======================
@staff_member_required
def all_students(request):
    students = Student.objects.select_related('country', 'teacher').all().order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        students = students.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    return render(request, 'core/all_students.html', {'students': students})


# =======================
# النسب (نسبة المنصة / نسبة المعلمة) - نسبة كل معلمة قابلة للتعديل من صفحة الرواتب
# =======================
@staff_member_required
def statistics(request):
    now = timezone.now()
    stat_year = _to_int_or_none(request.GET.get('year')) or now.year
    stat_month = _to_int_or_none(request.GET.get('month')) or now.month

    teachers = Teacher.objects.all()
    stats = []

    grand_total_fees = 0
    grand_platform_share = 0
    grand_teacher_share = 0

    for teacher in teachers:
        total_fees = teacher.total_subscriptions(year=stat_year, month=stat_month)
        teacher_share = teacher.calculated_salary(year=stat_year, month=stat_month)
        platform_share = teacher.platform_share(year=stat_year, month=stat_month)

        grand_total_fees += total_fees
        grand_platform_share += platform_share
        grand_teacher_share += teacher_share

        stats.append({
            'teacher': teacher,
            'student_count': teacher.students.count(),
            'total_fees': total_fees,
            'is_fixed': teacher.fixed_salary is not None,
            'commission_percent': teacher.commission_percent,
            'platform_share': platform_share,
            'teacher_share': teacher_share,
        })

    context = {
        'stats': stats,
        'grand_total_fees': grand_total_fees,
        'grand_platform_share': grand_platform_share,
        'grand_teacher_share': grand_teacher_share,
        'stat_year': stat_year,
        'stat_month': stat_month,
        'arabic_months': ARABIC_MONTHS,
        'stat_years_range': sorted({now.year - 1, now.year, now.year + 1}, reverse=True),
    }
    return render(request, 'core/statistics.html', context)


# =======================
# إدارة الدول
# =======================
@staff_member_required
def countries_list(request):
    countries = Country.objects.all()
    return render(request, 'core/countries_list.html', {'countries': countries})


@staff_member_required
def add_country(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'من فضلك أدخلي اسم الدولة.')
        else:
            Country.objects.create(
                name=name,
                flag_icon=request.POST.get('flag_icon', '🏳️').strip() or '🏳️',
            )
            messages.success(request, 'تم إضافة الدولة بنجاح.')
            return redirect('countries_list')

    return render(request, 'core/add_country.html')


@staff_member_required
def edit_country(request, country_id):
    country = get_object_or_404(Country, pk=country_id)

    if request.method == 'POST':
        country.name = request.POST.get('name', '').strip()
        country.flag_icon = request.POST.get('flag_icon', '🏳️').strip() or '🏳️'
        country.save()

        messages.success(request, 'تم تحديث بيانات الدولة.')
        return redirect('countries_list')

    return render(request, 'core/edit_country.html', {'country': country})


@staff_member_required
def delete_country(request, country_id):
    country = get_object_or_404(Country, pk=country_id)

    if request.method == 'POST':
        name = country.name
        country.delete()
        messages.success(request, f'تم حذف الدولة "{name}".')
        return redirect('countries_list')

    return render(request, 'core/delete_country.html', {'country': country})


# =======================
# المصروفات
# =======================
@staff_member_required
def expenses_list(request):
    expenses = Expense.objects.all()

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    year = request.GET.get('year', '').strip()
    month = request.GET.get('month', '').strip()

    if q:
        expenses = expenses.filter(title__icontains=q)
    if category:
        expenses = expenses.filter(category=category)
    if year:
        expenses = expenses.filter(date__year=year)
    if month:
        expenses = expenses.filter(date__month=month)

    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    years_range = set(Expense.objects.values_list('date__year', flat=True))
    years_range.add(timezone.now().year)
    years_range = sorted(years_range, reverse=True)

    context = {
        'expenses': expenses,
        'total_amount': total_amount,
        'categories': Expense.CATEGORY_CHOICES,
        'years_range': years_range,
        'selected_category': category,
        'selected_year': year,
        'selected_month': month,
        'search': q,
    }
    return render(request, 'core/expenses_list.html', context)


@staff_member_required
def add_expense(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'من فضلك أدخلي عنوان المصروف.')
        else:
            Expense.objects.create(
                title=title,
                category=request.POST.get('category', 'other'),
                amount=_to_decimal_or_zero(request.POST.get('amount')),
                date=_or_none(request.POST.get('date')) or timezone.now().date(),
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'تم إضافة المصروف بنجاح.')
            return redirect('expenses_list')

    return render(request, 'core/add_expense.html', {'categories': Expense.CATEGORY_CHOICES})


@staff_member_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)

    if request.method == 'POST':
        expense.title = request.POST.get('title', '').strip()
        expense.category = request.POST.get('category', expense.category)
        expense.amount = _to_decimal_or_zero(request.POST.get('amount'))
        expense.date = _or_none(request.POST.get('date')) or expense.date
        expense.notes = request.POST.get('notes', '').strip()
        expense.save()

        messages.success(request, 'تم تحديث بيانات المصروف.')
        return redirect('expenses_list')

    return render(request, 'core/edit_expense.html', {'expense': expense, 'categories': Expense.CATEGORY_CHOICES})


@staff_member_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)

    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f'تم حذف المصروف "{title}".')
        return redirect('expenses_list')

    return render(request, 'core/delete_expense.html', {'expense': expense})


# =======================
# التقارير المالية (شهري / سنوي)
# =======================
@staff_member_required
def financial_reports(request):
    try:
        selected_year = int(request.GET.get('year', timezone.now().year))
    except (TypeError, ValueError):
        selected_year = timezone.now().year

    total_salaries = _total_salaries()

    monthly_data = []
    year_income = Decimal('0')
    year_expenses = Decimal('0')
    year_profit = Decimal('0')

    for month in range(1, 13):
        income = _monthly_income(selected_year, month)
        expenses = _monthly_expenses(selected_year, month)
        profit = income - expenses - total_salaries

        year_income += income
        year_expenses += expenses
        year_profit += profit

        monthly_data.append({
            'month': month,
            'month_name': ARABIC_MONTHS[month],
            'income': income,
            'expenses': expenses,
            'salaries': total_salaries,
            'profit': profit,
        })

    # السنين المتاحة للاختيار من بينها (فيها بيانات فعلية + السنة الحالية)
    years_with_data = set()
    for s in Student.objects.all():
        pdate = _student_payment_date(s)
        if pdate:
            years_with_data.add(pdate.year)
    for e in Expense.objects.all():
        years_with_data.add(e.date.year)
    years_with_data.add(timezone.now().year)
    years_with_data = sorted(years_with_data, reverse=True)

    context = {
        'selected_year': selected_year,
        'years_with_data': years_with_data,
        'monthly_data': monthly_data,
        'total_salaries': total_salaries,
        'year_income': year_income,
        'year_expenses': year_expenses,
        'year_total_salaries': total_salaries * 12,
        'year_profit': year_profit,
        'chart_labels': json.dumps([m['month_name'] for m in monthly_data], ensure_ascii=False),
        'chart_income': json.dumps([float(m['income']) for m in monthly_data]),
        'chart_expenses': json.dumps([float(m['expenses'] + m['salaries']) for m in monthly_data]),
        'chart_profit': json.dumps([float(m['profit']) for m in monthly_data]),
    }
    return render(request, 'core/financial_reports.html', context)


# =======================
# السنوات -> الشهور -> الطلاب اللي دفعوا (سجل المدفوعات)
# =======================
@staff_member_required
def years_list(request):
    payment_years = set(Payment.objects.values_list('date__year', flat=True))
    payment_years.add(timezone.now().year)
    years = sorted(payment_years, reverse=True)

    year_cards = []
    for y in years:
        total = Payment.objects.filter(date__year=y).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        count = Payment.objects.filter(date__year=y).count()
        year_cards.append({'year': y, 'total': total, 'count': count})

    return render(request, 'core/years_list.html', {'year_cards': year_cards})


@staff_member_required
def year_months(request, year):
    months_data = []
    year_total = Decimal('0')

    for m in range(1, 13):
        total = Payment.objects.filter(date__year=year, date__month=m).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        count = Payment.objects.filter(date__year=year, date__month=m).count()
        year_total += total
        months_data.append({
            'month': m,
            'month_name': ARABIC_MONTHS[m],
            'total': total,
            'count': count,
        })

    context = {
        'year': year,
        'months_data': months_data,
        'year_total': year_total,
    }
    return render(request, 'core/year_months.html', context)


@staff_member_required
def month_payments(request, year, month):
    payments = Payment.objects.filter(date__year=year, date__month=month).select_related('student', 'student__country')
    total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = _to_decimal_or_zero(request.POST.get('amount'))
        day = request.POST.get('day', '1').strip() or '1'
        note = request.POST.get('note', '').strip()

        if not student_id or amount <= 0:
            messages.error(request, 'من فضلك اختاري الطالب وأدخلي مبلغ صحيح.')
        else:
            last_day = calendar.monthrange(year, month)[1]
            try:
                day_num = min(max(int(day), 1), last_day)
            except ValueError:
                day_num = 1
            payment_date = datetime(year, month, day_num).date()

            student = get_object_or_404(Student, pk=student_id)
            Payment.objects.create(student=student, amount=amount, date=payment_date, note=note)
            student.last_payment_date = payment_date
            student.payment_status = 'paid'
            student.save(update_fields=['last_payment_date', 'payment_status'])

            messages.success(request, f'تم تسجيل دفعة {student.name} في {ARABIC_MONTHS[month]} {year}.')
            return redirect('month_payments', year=year, month=month)

    context = {
        'year': year,
        'month': month,
        'month_name': ARABIC_MONTHS[month],
        'payments': payments,
        'total': total,
        'all_students': Student.objects.all().order_by('name'),
    }
    return render(request, 'core/month_payments.html', context)


@staff_member_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    year, month = payment.date.year, payment.date.month

    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'تم حذف الدفعة من السجل.')

    return redirect('month_payments', year=year, month=month)


# =======================
# قائمة الرواتب (تحديد نسبة/راتب مثبت لكل معلمة + تسجيل كل صرف راتب)
# =======================
@staff_member_required
def salaries_list(request):
    now = timezone.now()

    # الشهر/السنة اللي بنعرض "الراتب المستحق" عنها فوق (افتراضيًا الشهر الحالي).
    # ده بديل الحساب التراكمي القديم اللي كان بيجمع كل دفعات المعلمة من الأول
    # وبيسبب مضاعفة الراتب لما تتصرف رواتب عن شهور مختلفة.
    salary_year = _to_int_or_none(request.GET.get('salary_year')) or now.year
    salary_month = _to_int_or_none(request.GET.get('salary_month')) or now.month

    teachers_data = []
    for t in Teacher.objects.all():
        teachers_data.append({
            'teacher': t,
            'total_subscriptions': t.total_subscriptions(year=salary_year, month=salary_month),
            'calculated_salary': t.calculated_salary(year=salary_year, month=salary_month),
            'already_paid_this_month': t.has_salary_record_for(salary_year, salary_month),
        })

    q = request.GET.get('q', '').strip()
    year = request.GET.get('year', '').strip()
    month = request.GET.get('month', '').strip()

    records = TeacherSalaryRecord.objects.select_related('teacher').all()
    if q:
        records = records.filter(teacher__name__icontains=q)
    if year:
        records = records.filter(payout_date__year=year)
    if month:
        records = records.filter(payout_date__month=month)

    total_net = sum(r.net_amount() for r in records)

    years_range = set(TeacherSalaryRecord.objects.values_list('payout_date__year', flat=True))
    years_range.add(timezone.now().year)
    years_range = sorted(years_range, reverse=True)

    context = {
        'teachers_data': teachers_data,
        'salary_year': salary_year,
        'salary_month': salary_month,
        'salary_years_range': sorted({now.year - 1, now.year, now.year + 1}, reverse=True),
        'arabic_months': ARABIC_MONTHS,
        'records': records,
        'total_net': total_net,
        'years_range': years_range,
        'selected_year': year,
        'selected_month': month,
        'search': q,
    }
    return render(request, 'core/salaries_list.html', context)


@staff_member_required
def update_teacher_commission(request, teacher_id):
    """تعديل سريع لنسبة معلمة أو تثبيت راتب لها بدل النسبة"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    if request.method == 'POST':
        use_fixed = request.POST.get('use_fixed') == 'on'
        if use_fixed:
            teacher.fixed_salary = _to_decimal_or_zero(request.POST.get('fixed_salary'))
        else:
            teacher.fixed_salary = None
            percent = _to_decimal_or_zero(request.POST.get('commission_percent'))
            if 0 <= percent <= 100:
                teacher.commission_percent = percent
            else:
                messages.error(request, 'النسبة لازم تكون رقم بين 0 و100.')
                return redirect('salaries_list')
        teacher.save()
        messages.success(request, f'تم تحديث إعدادات راتب "{teacher.name}".')

    return redirect('salaries_list')


@staff_member_required
def add_salary_record(request):
    now = timezone.now()
    preselected_teacher = request.GET.get('teacher', '')

    # الشهر اللي بنصرف الراتب عنه - افتراضيًا الشهر الحالي، وقابل للتغيير
    salary_year = _to_int_or_none(request.GET.get('salary_year')) or now.year
    salary_month = _to_int_or_none(request.GET.get('salary_month')) or now.month

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        salary_year = _to_int_or_none(request.POST.get('salary_year')) or now.year
        salary_month = _to_int_or_none(request.POST.get('salary_month')) or now.month
        force = request.POST.get('force') == 'on'

        if not teacher_id:
            messages.error(request, 'من فضلك اختاري المعلمة.')
        else:
            teacher = get_object_or_404(Teacher, pk=teacher_id)

            # منع صرف راتب نفس الشهر مرتين بالغلط (إلا لو اختارت "تأكيد الصرف تاني")
            if teacher.has_salary_record_for(salary_year, salary_month) and not force:
                messages.error(
                    request,
                    f'"{teacher.name}" اتصرفلها راتب شهر {ARABIC_MONTHS.get(salary_month, salary_month)}/{salary_year} قبل كده. '
                    'لو متأكدة إنك عايزة تسجلي صرف تاني عن نفس الشهر (مثلاً دفعة إضافية)، فعّلي خيار "تأكيد الصرف مرة تانية".'
                )
                return redirect(f"{reverse('add_salary_record')}?teacher={teacher_id}&salary_year={salary_year}&salary_month={salary_month}")

            # الراتب بيتحسب من دفعات الشهر ده بس (مش تراكمي) عشان ميتضاعفش
            base_amount = teacher.calculated_salary(year=salary_year, month=salary_month)

            payout_date = _or_none(request.POST.get('payout_date'))
            if not payout_date:
                payout_date = timezone.now().date().replace(year=salary_year, month=salary_month, day=min(timezone.now().day, 28))

            TeacherSalaryRecord.objects.create(
                teacher=teacher,
                payout_date=payout_date,
                base_amount=Decimal(str(base_amount)),
                bonus=_to_decimal_or_zero(request.POST.get('bonus')),
                deduction=_to_decimal_or_zero(request.POST.get('deduction')),
                leave_days=_to_int_or_none(request.POST.get('leave_days')) or 0,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(
                request,
                f'تم تسجيل صرف راتب "{teacher.name}" عن شهر {ARABIC_MONTHS.get(salary_month, salary_month)}/{salary_year} '
                f'بقيمة {base_amount} جنيه.'
            )
            return redirect('salaries_list')

    teachers_data = [
        {
            'teacher': t,
            'calculated_salary': t.calculated_salary(year=salary_year, month=salary_month),
            'already_paid_this_month': t.has_salary_record_for(salary_year, salary_month),
        }
        for t in Teacher.objects.all()
    ]

    context = {
        'teachers_data': teachers_data,
        'preselected_teacher': preselected_teacher,
        'salary_year': salary_year,
        'salary_month': salary_month,
        'salary_years_range': sorted({now.year - 1, now.year, now.year + 1}, reverse=True),
        'arabic_months': ARABIC_MONTHS,
    }
    return render(request, 'core/add_salary_record.html', context)


@staff_member_required
def delete_salary_record(request, record_id):
    record = get_object_or_404(TeacherSalaryRecord, pk=record_id)

    if request.method == 'POST':
        record.delete()
        messages.success(request, 'تم حذف سجل الراتب.')

    return redirect('salaries_list')


# =======================
# الحلقات ومتابعة الحضور والانضباط
# =======================
@staff_member_required
def lessons_dashboard(request):
    """لوحة اليوم: كام حلقة مجدولة/تمت/لسه/غير مسجلة + دخول سريع على المعلمات"""
    now = timezone.now()
    today = now.date()

    todays_lessons = Lesson.objects.select_related('student', 'teacher').filter(scheduled_at__date=today)

    completed = 0
    student_absent = 0
    teacher_absent = 0
    cancelled = 0
    unrecorded = 0  # عدد الحلقات اللي اتحسبت غياب تلقائي لأن محدش سجلها (رقم فرعي داخل غياب الطالب)
    not_due_yet = 0
    due_now = []

    for lesson in todays_lessons:
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
        elif eff == 'scheduled':
            if lesson.scheduled_at > now:
                not_due_yet += 1
            else:
                due_now.append(lesson)

    teacher_rows = []
    for t in Teacher.objects.all():
        s = t.monthly_lesson_stats(year=now.year, month=now.month)
        teacher_rows.append({'teacher': t, 'stats': s})

    context = {
        'today': today,
        'todays_lessons': todays_lessons,
        'total_today': todays_lessons.count(),
        'completed': completed,
        'student_absent': student_absent,
        'teacher_absent': teacher_absent,
        'cancelled': cancelled,
        'unregistered': unrecorded,
        'not_due_yet': not_due_yet,
        'due_now': due_now,
        'teacher_rows': teacher_rows,
        'pending_requests_count': ScheduleRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'core/lessons_dashboard.html', context)


@staff_member_required
def add_lesson(request):
    """جدولة حلقة جديدة يدويًا (بديل عن اللي بيتحط عن طريق الموافقة على طلب موعد)"""
    students = Student.objects.filter(status='active').select_related('teacher')
    preselected_student = request.GET.get('student', '')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        scheduled_at = _or_none(request.POST.get('scheduled_at'))
        if not student_id or not scheduled_at:
            messages.error(request, 'من فضلك اختاري الطالب وحددي الموعد.')
        else:
            student = get_object_or_404(Student, pk=student_id)
            if not student.teacher:
                messages.error(request, 'الطالب ده لسه ملوش معلمة محددة.')
            else:
                Lesson.objects.create(
                    student=student,
                    teacher=student.teacher,
                    scheduled_at=scheduled_at,
                    duration_minutes=_to_int_or_none(request.POST.get('duration_minutes')) or 30,
                )
                messages.success(request, f'تم جدولة حلقة لـ {student.name}.')
                return redirect('lessons_dashboard')

    return render(request, 'core/add_lesson.html', {
        'students': students,
        'preselected_student': preselected_student,
    })


@staff_member_required
def mark_lesson(request, lesson_id):
    """تسجيل حالة الحلقة: تمت / غياب طالب / غياب معلمة / أُلغيت"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        was_late = request.POST.get('was_late') == 'on'
        valid_statuses = dict(Lesson.STATUS_CHOICES)
        if new_status not in valid_statuses or new_status == 'unregistered':
            messages.error(request, 'حالة غير صحيحة.')
        else:
            lesson.mark(new_status, was_late=was_late)
            messages.success(request, f'تم تسجيل حالة الحلقة: {valid_statuses[new_status]}.')

    next_url = request.POST.get('next') or request.GET.get('next') or 'lessons_dashboard'
    return redirect(next_url)


@staff_member_required
def mark_lesson_started(request, lesson_id):
    """تسجيل إن الحلقة بدأت فعليًا (زرار "بدء الحلقة")"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if request.method == 'POST':
        lesson.mark_started()
        messages.success(request, f'تم تسجيل بدء حلقة {lesson.student.name}.')
    next_url = request.POST.get('next') or request.GET.get('next') or 'lessons_dashboard'
    return redirect(next_url)


@staff_member_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'تم حذف الحلقة.')
    return redirect('lessons_dashboard')


# =======================
# طلبات المواعيد (المعلمة تقترح - الإدارة توافق)
# =======================
@staff_member_required
def schedule_requests_list(request):
    requests_qs = ScheduleRequest.objects.select_related('student', 'teacher').all()
    status = request.GET.get('status', 'pending')
    if status in ('pending', 'approved', 'rejected'):
        requests_qs = requests_qs.filter(status=status)
    # status == 'all' -> بدون فلترة

    context = {
        'requests': requests_qs,
        'selected_status': status,
    }
    return render(request, 'core/schedule_requests_list.html', context)


@staff_member_required
def review_schedule_request(request, request_id):
    """موافقة أو رفض طلب موعد جديد/تعديل موعد"""
    req = get_object_or_404(ScheduleRequest, pk=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_note = request.POST.get('admin_note', '').strip()
        if action == 'approve':
            req.approve(admin_note=admin_note)
            messages.success(request, f'تمت الموافقة على طلب "{req.student.name}".')
        elif action == 'reject':
            req.reject(admin_note=admin_note)
            messages.warning(request, f'تم رفض طلب "{req.student.name}".')

    return redirect('schedule_requests_list')


# =======================
# شكاوى المعلمات
# =======================
@staff_member_required
def add_complaint(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        if description:
            TeacherComplaint.objects.create(
                teacher=teacher,
                description=description,
                date=_or_none(request.POST.get('date')) or timezone.now().date(),
            )
            messages.success(request, 'تم تسجيل الشكوى.')
        else:
            messages.error(request, 'من فضلك اكتبي تفاصيل الشكوى.')
    return redirect('teacher_detail', teacher_id=teacher.id)


# =======================
# حساب دخول المعلمة (صلاحيات محدودة - مش أدمن) - بتتعمل من لوحة الإدارة
# =======================
@staff_member_required
def create_teacher_login(request, teacher_id):
    """الإدارة (أدمن) بس اللي تقدر تنشئ حساب دخول لمعلمة. الحساب ده User عادي
    is_staff=False و is_superuser=False يعني معندوش أي دخول للوحة الإدارة
    خالص، بس بيدخل بورتال المعلمة المحدود (بياناته هو بس)"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    # بنستخدم USERNAME_FIELD الحقيقي لموديل اليوزر عندكم (ممكن يكون username
    # أو email أو أي حاجة تانية لو عندكم موديل يوزر مخصص) بدل ما نفترض 'username'
    username_field = User.USERNAME_FIELD
    user_field_names = {f.name for f in User._meta.get_fields()}

    if teacher.user_id:
        messages.error(request, f'"{teacher.name}" عندها حساب دخول بالفعل ({getattr(teacher.user, username_field)}).')
        return redirect('teacher_detail', teacher_id=teacher.id)

    if request.method == 'POST':
        base_username = request.POST.get('username', '').strip()
        if not base_username:
            # قيمة مقترحة لو الأدمن ما كتبش حاجة
            base_username = 'teacher_' + str(teacher.id)
            if username_field == 'email' and '@' not in base_username:
                base_username = f'teacher{teacher.id}@example.com'

        if User.objects.filter(**{username_field: base_username}).exists():
            messages.error(request, f'"{base_username}" مستخدم قبل كده، اختاري قيمة تانية.')
            return redirect('create_teacher_login', teacher_id=teacher.id)

        temp_password = secrets.token_urlsafe(6)  # كلمة سر عشوائية آمنة تتعرض مرة واحدة بس
        try:
            create_kwargs = {
                username_field: base_username,
                'is_staff': False,      # <-- الأهم: مفيش دخول للوحة الإدارة نهائيًا
                'is_superuser': False,
            }
            if 'first_name' in user_field_names:
                create_kwargs['first_name'] = teacher.name
            user = User(**create_kwargs)
            user.set_password(temp_password)
            user.save()
        except TypeError as e:
            messages.error(
                request,
                'موديل اليوزر عندكم (accounts.User) فيه حقول مطلوبة تانية مش موجودة في الكود ده '
                f'({e}). ابعتيلي شكل الموديل وهظبطها.'
            )
            return redirect('teacher_detail', teacher_id=teacher.id)

        teacher.user = user
        teacher.save(update_fields=['user'])

        messages.success(
            request,
            f'تم إنشاء حساب دخول لـ "{teacher.name}". {username_field}: {base_username} - كلمة السر: {temp_password} '
            '(احفظيها وابعتيها للمعلمة دلوقتي، مش هتتعرض تاني).'
        )
        return redirect('teacher_detail', teacher_id=teacher.id)

    return render(request, 'core/create_teacher_login.html', {'teacher': teacher})


@staff_member_required
def reset_teacher_login_password(request, teacher_id):
    """تصفير كلمة سر المعلمة لو نسيتها (بدون ما تشوف الأدمن كلمة السر القديمة أصلًا، مش متخزنة)"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    if not teacher.user_id:
        messages.error(request, 'المعلمة دي معندهاش حساب دخول أصلًا.')
        return redirect('teacher_detail', teacher_id=teacher.id)

    if request.method == 'POST':
        temp_password = secrets.token_urlsafe(6)
        teacher.user.password = make_password(temp_password)
        teacher.user.save(update_fields=['password'])
        messages.success(request, f'كلمة السر الجديدة لـ "{teacher.name}": {temp_password}')
    return redirect('teacher_detail', teacher_id=teacher.id)


@staff_member_required
def revoke_teacher_login(request, teacher_id):
    """إلغاء حساب الدخول (مثلاً المعلمة سابت الشغل)"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    if request.method == 'POST' and teacher.user_id:
        old_user = teacher.user
        teacher.user = None
        teacher.save(update_fields=['user'])
        old_user.is_active = False
        old_user.save(update_fields=['is_active'])
        messages.success(request, f'تم إلغاء حساب دخول "{teacher.name}".')
    return redirect('teacher_detail', teacher_id=teacher.id)


# =======================
# بورتال المعلمة (تسجيل دخول محدود الصلاحيات - مش أدمن)
# =======================
def teacher_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_portal_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'اسم المستخدم أو كلمة السر غلط.')
        elif not hasattr(user, 'teacher_profile'):
            # حتى لو الحساب صح، لو مش مربوط بمعلمة (زي حساب الأدمن) بيتمنع من هنا
            messages.error(request, 'الحساب ده مش حساب معلمة.')
        elif not user.is_active:
            messages.error(request, 'الحساب ده متوقف، كلمي الإدارة.')
        else:
            auth_login(request, user)
            return redirect('teacher_portal_home')

    return render(request, 'core/teacher_login.html')


def teacher_logout(request):
    auth_logout(request)
    return redirect('teacher_login')


@teacher_login_required
def teacher_portal_home(request):
    """الصفحة الرئيسية لبورتال المعلمة: بياناتها هي بس + إحصائياتها + طلابها"""
    teacher = request.user.teacher_profile
    now = timezone.now()
    stat_year = _to_int_or_none(request.GET.get('year')) or now.year
    stat_month = _to_int_or_none(request.GET.get('month')) or now.month

    due_lessons = [l for l in teacher.lessons.filter(status='scheduled') if l.is_ongoing_or_due()]
    upcoming = teacher.lessons.filter(status='scheduled', scheduled_at__gte=now).order_by('scheduled_at')[:10]
    overdue_unrecorded = [l for l in teacher.lessons.filter(status='scheduled') if l.is_overdue_unrecorded()]

    students_progress = [
        {'student': s, 'progress': s.lessons_progress_label()}
        for s in teacher.students.filter(status='active')
    ]

    context = {
        'teacher': teacher,
        'students': teacher.students.filter(status='active'),
        'students_progress': students_progress,
        'monthly_stats': teacher.monthly_lesson_stats(year=stat_year, month=stat_month),
        'stat_year': stat_year,
        'stat_month': stat_month,
        'arabic_months': ARABIC_MONTHS,
        'stat_years_range': sorted({now.year - 1, now.year, now.year + 1}, reverse=True),
        'due_lessons': due_lessons,
        'upcoming_lessons': upcoming,
        'overdue_unrecorded': overdue_unrecorded,
    }
    return render(request, 'core/teacher_portal_home.html', context)


@teacher_login_required
def teacher_mark_lesson_started(request, lesson_id):
    """المعلمة تضغط "بدء الحلقة" الساعة اللي بتبدأ فيها فعليًا"""
    teacher = request.user.teacher_profile
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher=teacher)
    if request.method == 'POST':
        lesson.mark_started()
        messages.success(request, f'تم تسجيل بدء حلقة {lesson.student.name}.')
    return redirect('teacher_portal_home')


@teacher_login_required
def teacher_mark_lesson(request, lesson_id):
    """المعلمة تسجل حالة حلقتها هي بس - مينفعش تلمس حلقة معلمة تانية"""
    teacher = request.user.teacher_profile
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher=teacher)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        was_late = request.POST.get('was_late') == 'on'
        valid_statuses = dict(Lesson.STATUS_CHOICES)
        if new_status not in valid_statuses or new_status == 'unregistered':
            messages.error(request, 'حالة غير صحيحة.')
        else:
            lesson.mark(new_status, was_late=was_late)
            messages.success(request, f'تم تسجيل حالة الحلقة: {valid_statuses[new_status]}.')

    return redirect('teacher_portal_home')


@teacher_login_required
def teacher_schedule_requests(request):
    """المعلمة تشوف طلبات تعديل المواعيد بتاعتها وتقدر تبعت طلب تعديل جديد
    لحلقة قائمة - مش بيتفعّل على طول، لازم موافقة الإدارة. (تسجيل مواعيد
    جديدة بقى من صفحة "تسجيل مواعيد الطلاب" بدل ما يكون طلب هنا)"""
    teacher = request.user.teacher_profile

    if request.method == 'POST':
        related_lesson_id = request.POST.get('related_lesson')
        proposed_datetime = _or_none(request.POST.get('proposed_datetime'))

        if not related_lesson_id or not proposed_datetime:
            messages.error(request, 'من فضلك اختاري الحلقة والموعد الجديد المقترح.')
            return redirect('teacher_schedule_requests')

        related_lesson = get_object_or_404(Lesson, pk=related_lesson_id, teacher=teacher)
        ScheduleRequest.objects.create(
            student=related_lesson.student,
            teacher=teacher,
            request_type='change',
            related_lesson=related_lesson,
            proposed_datetime=proposed_datetime,
            teacher_note=request.POST.get('teacher_note', '').strip(),
        )
        messages.success(request, 'تم إرسال طلب تعديل الموعد للإدارة، هيتفعّل بعد الموافقة عليه.')
        return redirect('teacher_schedule_requests')

    context = {
        'teacher': teacher,
        'requests': teacher.schedule_requests.all(),
        'upcoming_lessons': teacher.lessons.filter(status='scheduled').order_by('scheduled_at')[:20],
    }
    return render(request, 'core/teacher_schedule_requests.html', context)


@teacher_login_required
def teacher_register_schedule(request):
    """تسجيل مواعيد الطلاب: المعلمة تحط اسم الطالب ومواعيد حلقاته المتكررة
    (يوم/أيام الأسبوع + الوقت)، والسيستم بيولّد الحلقات تلقائيًا لعدد
    الأسابيع المطلوبة. ده تسجيل مباشر (مش طلب محتاج موافقة) لأنه أساسًا
    بيان بجدولها هي المعروف مسبقًا، مش تعديل على جدول متفق عليه بالفعل"""
    teacher = request.user.teacher_profile
    students = teacher.students.filter(status='active')

    WEEKDAYS = [
        (0, 'الإثنين'), (1, 'الثلاثاء'), (2, 'الأربعاء'), (3, 'الخميس'),
        (4, 'الجمعة'), (5, 'السبت'), (6, 'الأحد'),
    ]

    if request.method == 'POST':
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, pk=student_id, teacher=teacher)

        weekdays = request.POST.getlist('weekday')
        lesson_time = _or_none(request.POST.get('lesson_time'))
        weeks_count = _to_int_or_none(request.POST.get('weeks_count')) or 4
        duration_minutes = _to_int_or_none(request.POST.get('duration_minutes')) or 30

        if not weekdays or not lesson_time:
            messages.error(request, 'من فضلك حددي يوم/أيام الحلقة والوقت.')
            return redirect('teacher_register_schedule')

        weekdays = {int(w) for w in weekdays}
        hour, minute = [int(x) for x in lesson_time.split(':')[:2]]

        created_count = 0
        today = timezone.localdate()
        end_date = today + timedelta(days=weeks_count * 7)
        current_date = today
        while current_date <= end_date:
            if current_date.weekday() in weekdays:
                naive_dt = datetime.combine(current_date, datetime.min.time()).replace(hour=hour, minute=minute)
                scheduled_at = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
                if scheduled_at >= timezone.now() and not Lesson.objects.filter(student=student, teacher=teacher, scheduled_at=scheduled_at).exists():
                    Lesson.objects.create(
                        student=student, teacher=teacher,
                        scheduled_at=scheduled_at, duration_minutes=duration_minutes,
                    )
                    created_count += 1
            current_date += timedelta(days=1)

        if created_count:
            messages.success(request, f'تم تسجيل {created_count} حلقة لـ "{student.name}" في جدولك.')
        else:
            messages.warning(request, 'مفيش حلقات جديدة اتضافت (ممكن تكون كل المواعيد دي متسجلة قبل كده).')
        return redirect('teacher_register_schedule')

    students_progress = [
        {'student': s, 'progress': s.lessons_progress_label(), 'upcoming': s.lessons.filter(status='scheduled', scheduled_at__gte=timezone.now()).order_by('scheduled_at')}
        for s in students
    ]

    context = {
        'teacher': teacher,
        'students': students,
        'students_progress': students_progress,
        'weekdays': WEEKDAYS,
    }
    return render(request, 'core/teacher_register_schedule.html', context)


# =======================
# نموذج تقييم ومتابعة الأداء الشهري
# =======================
@staff_member_required
def evaluations_list(request):
    evaluations = MonthlyEvaluation.objects.select_related('student').all()

    q = request.GET.get('q', '').strip()
    if q:
        evaluations = evaluations.filter(student_name__icontains=q)

    return render(request, 'core/evaluations_list.html', {'evaluations': evaluations, 'search': q})


@staff_member_required
def add_evaluation(request):
    students = Student.objects.all().order_by('name')
    preselected_student = request.GET.get('student', '')
    today = timezone.now().date()
    default_month = f"{ARABIC_MONTHS[today.month]} {today.year}"

    students_data = {
        s.id: {
            'teacher': s.teacher.name if s.teacher else '',
            'package': s.package_name or '',
            'lessons': s.lessons_count,
        }
        for s in students
    }

    if request.method == 'POST':
        student_id = request.POST.get('student')
        if not student_id:
            messages.error(request, 'من فضلك اختاري الطالب.')
        else:
            student = get_object_or_404(Student, pk=student_id)
            evaluation = MonthlyEvaluation.objects.create(
                student=student,
                student_name=request.POST.get('student_name', '').strip() or student.name,
                teacher_name=request.POST.get('teacher_name', '').strip(),
                package_name=request.POST.get('package_name', '').strip(),
                lessons_count=_to_int_or_none(request.POST.get('lessons_count')) or student.lessons_count,
                month_label=request.POST.get('month_label', '').strip() or default_month,
                memorization_progress=request.POST.get('memorization_progress', '').strip(),
                review_progress=request.POST.get('review_progress', '').strip(),
                absences=request.POST.get('absences', '').strip(),
                pronunciation_rating=request.POST.get('pronunciation_rating', '').strip(),
                tajweed_rating=request.POST.get('tajweed_rating', '').strip(),
                interaction_rating=request.POST.get('interaction_rating', '').strip(),
                response_speed_rating=request.POST.get('response_speed_rating', '').strip(),
                commitment_rating=request.POST.get('commitment_rating', '').strip(),
                recommendations=request.POST.get('recommendations', '').strip(),
                teacher_comment=request.POST.get('teacher_comment', '').strip(),
                month_rating=request.POST.get('month_rating', '').strip(),
                template=request.POST.get('template', 'teal_pink'),
            )
            messages.success(request, f'تم إنشاء تقييم "{evaluation.student_name}" بنجاح.')
            return redirect('evaluation_detail', evaluation_id=evaluation.id)

    preview_defaults = {
        'student_name': 'اسم الطالب',
        'teacher_name': 'اسم المعلمة',
        'package_name': 'اسم الباقة',
        'lessons_count': 4,
        'month_label': default_month,
        'memorization_progress': '-',
        'review_progress': '-',
        'absences': '-',
        'pronunciation_rating': '-',
        'tajweed_rating': '-',
        'interaction_rating': '-',
        'response_speed_rating': '-',
        'commitment_rating': '-',
        'recommendations': '-',
        'teacher_comment': '-',
        'month_rating': '-',
        'template': 'teal_pink',
    }

    context = {
        'students': students,
        'preselected_student': preselected_student,
        'default_month': default_month,
        'students_json': json.dumps(students_data, ensure_ascii=False),
        'preview_defaults': preview_defaults,
    }
    return render(request, 'core/add_evaluation.html', context)


@staff_member_required
def evaluation_detail(request, evaluation_id):
    evaluation = get_object_or_404(MonthlyEvaluation, pk=evaluation_id)
    public_url = request.build_absolute_uri(reverse('public_evaluation', args=[evaluation.public_token]))
    return render(request, 'core/evaluation_detail.html', {'evaluation': evaluation, 'public_url': public_url})


@staff_member_required
def delete_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(MonthlyEvaluation, pk=evaluation_id)

    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, 'تم حذف التقييم.')

    return redirect('evaluations_list')


def public_evaluation(request, token):
    """صفحة عامة بدون تسجيل دخول - عشان تُبعت كلينك لولي الأمر مباشرة"""
    evaluation = get_object_or_404(MonthlyEvaluation, public_token=token)
    return render(request, 'core/evaluation_public.html', {'evaluation': evaluation})