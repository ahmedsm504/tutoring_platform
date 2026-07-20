from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum
import json
import calendar

from .models import Teacher, Student, Country, StudentNote, Expense, Payment, TeacherSalaryRecord, MonthlyEvaluation


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
    context = {
        'student': student,
        'notes': notes,
        'payments': payments,
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

    context = {
        'teacher': teacher,
        'students': students,
        'current_students': students.filter(status='active').count(),
        'previous_students': students.filter(status='inactive').count(),
        'salary_records': teacher.salary_records.all()[:12],
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
    teachers = Teacher.objects.all()
    stats = []

    grand_total_fees = 0
    grand_platform_share = 0
    grand_teacher_share = 0

    for teacher in teachers:
        total_fees = teacher.total_subscriptions()
        teacher_share = teacher.calculated_salary()
        platform_share = teacher.platform_share()

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
    teachers = Teacher.objects.all()

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
        'teachers': teachers,
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
    teachers = Teacher.objects.all()
    preselected_teacher = request.GET.get('teacher', '')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        if not teacher_id:
            messages.error(request, 'من فضلك اختاري المعلمة.')
        else:
            teacher = get_object_or_404(Teacher, pk=teacher_id)
            TeacherSalaryRecord.objects.create(
                teacher=teacher,
                payout_date=_or_none(request.POST.get('payout_date')) or timezone.now().date(),
                base_amount=Decimal(str(teacher.calculated_salary())),
                bonus=_to_decimal_or_zero(request.POST.get('bonus')),
                deduction=_to_decimal_or_zero(request.POST.get('deduction')),
                leave_days=_to_int_or_none(request.POST.get('leave_days')) or 0,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, f'تم تسجيل صرف راتب "{teacher.name}".')
            return redirect('salaries_list')

    context = {
        'teachers': teachers,
        'preselected_teacher': preselected_teacher,
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