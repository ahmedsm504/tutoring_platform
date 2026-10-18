from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Q, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from functools import wraps
import json
import calendar

from .models import (
    Teacher, Student, Country, StudentNote, Expense, Payment, TeacherSalaryRecord, MonthlyEvaluation,
    Lesson, ScheduleRequest, TeacherComplaint, Supervisor, CurriculumDocument, TeacherActivity,
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


def supervisor_login_required(view_func):
    """نفس فكرة teacher_login_required بالظبط، بس لحساب المشرفة: بتشوف بس
    المعلمات المربوطين بيها (Teacher.supervisor) وبياناتهم، ومش بتدخل لوحة
    الأدمن ولا بورتال المعلمة خالص"""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'supervisor_profile'):
            messages.error(request, 'من فضلك سجلي الدخول بحساب المشرفة الخاص بيكِ.')
            return redirect('supervisor_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


# المعلمة تقدر تضيف حلقات في الماضي؟ (False = من النهاردة وطالع بس؛ الحلقات الفايتة بتتسجل من المشرفة)
TEACHER_CAN_ADD_PAST_LESSONS = False
MAX_REPEAT_WEEKS = 12

# كلمة سر حسابات المعلمات والمشرفات بتتكتب بإيد الأدمن (مش بتتولد تلقائي)
MIN_PASSWORD_LENGTH = 6


def _check_chosen_password(password, password2, username=''):
    """بنتأكد بس من الكلمة اللي الأدمن كتبتها: مش فاضية، متطابقة مع التأكيد، طولها كفاية،
    ومش نفس اسم الدخول. بترجع نص الخطأ أو None لو تمام."""
    if not password or not password.strip():
        return 'لازم تكتبي كلمة السر.'
    if password != password2:
        return 'كلمتي السر مش متطابقتين.'
    if len(password) < MIN_PASSWORD_LENGTH:
        return f'كلمة السر لازم تكون {MIN_PASSWORD_LENGTH} حروف/أرقام على الأقل.'
    if username and password.strip().lower() == str(username).strip().lower():
        return 'كلمة السر مينفعش تكون نفس اسم الدخول.'
    return None


def _safe_next(request, default):
    """رابط الرجوع بعد الإجراء - بنقبل بس روابط من نفس الموقع (حماية من open redirect)"""
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return default


ARABIC_MONTHS = {
    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
    7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر',
}


# =======================
# صفحات الموقع العامة
# =======================
def _public_ctx(**extra):
    from . import site_content as sc
    ctx = {'programs': sc.PROGRAMS, 'steps': sc.STEPS, 'features': sc.FEATURES, 'faq': sc.FAQ, 'reviews': sc.REVIEWS}
    ctx.update(extra)
    return ctx


def home(request):
    from . import site_content as sc
    return render(request, 'core/home.html', _public_ctx(
        faq_ldjson=json.dumps(sc.faq_schema(), ensure_ascii=False).replace('<', '\\u003c'),
    ))


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    # القالب core/contact.html مكانش موجود أصلًا (الصفحة كانت بتقع 500) -
    # صفحة التواصل الحقيقية بفورم حجز الحلقة التجريبية موجودة في accounts
    from accounts.views import contact_view
    return contact_view(request)


def pricing(request):
    from . import site_content as sc
    site = settings.CANONICAL_URL.rstrip('/')
    return render(request, 'core/pricing.html', _public_ctx(
        courses_ldjson=json.dumps(sc.courses_schema(site), ensure_ascii=False).replace('<', '\\u003c'),
    ))


def quality_standards(request):
    return render(request, 'core/quality_standards.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def terms(request):
    return render(request, 'core/terms.html')


def editorial_policy(request):
    return render(request, 'core/editorial_policy.html')


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


def _paid_salaries(year, month):
    """إجمالي الرواتب *المصروفة فعليًا* في شهر معيّن (حسب تاريخ الصرف):
    الصافي = الأساسي + المكافآت - الخصومات من سجل الصرف. مفيش علاقة بالمستحق:
    لو لسه ما اتصرفش حاجة بيرجع صفر."""
    total = Decimal('0')
    for r in TeacherSalaryRecord.objects.filter(payout_date__year=year, payout_date__month=month):
        total += r.base_amount + r.bonus - r.deduction
    return total


def _pay_period(request):
    """الشهر اللي بنفحص الدفع فيه للطلاب (افتراضيًا الشهر الحالي)"""
    now = timezone.now()
    year = _to_int_or_none(request.GET.get('pay_year')) or now.year
    month = _to_int_or_none(request.GET.get('pay_month')) or now.month
    if not 1 <= month <= 12:
        month = now.month
    return year, month


def _annotate_paid(qs, year, month):
    """يضيف لكل طالب paid_this_month = إجمالي اللي دفعه فعليًا في الشهر ده (0 لو ما دفعش)"""
    return qs.annotate(paid_this_month=Coalesce(
        Sum('payments__amount', filter=Q(payments__date__year=year, payments__date__month=month)),
        Value(0), output_field=DecimalField(max_digits=12, decimal_places=2),
    ))


def _pay_context(pay_year, pay_month, pay_filter=''):
    now = timezone.now()
    return {
        'pay_year': pay_year,
        'pay_month': pay_month,
        'pay_month_name': ARABIC_MONTHS.get(pay_month, pay_month),
        'pay_filter': pay_filter,
        'pay_years_range': sorted({now.year - 1, now.year, now.year + 1, pay_year}, reverse=True),
        'arabic_months': ARABIC_MONTHS,
    }


# =======================
# الصفحة الرئيسية للنظام (كروت الدول)
# =======================
@staff_member_required
def dashboard_home(request):
    countries = Country.objects.filter(is_active=True)

    today = timezone.now().date()
    current_month_income = _monthly_income(today.year, today.month)
    current_month_expenses = _monthly_expenses(today.year, today.month)
    current_month_salaries = _paid_salaries(today.year, today.month)  # المصروف فعليًا بس
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
    todays_activity = TeacherActivity.objects.filter(created_at__date=timezone.localdate())
    context.update({
        'recent_activity': TeacherActivity.objects.select_related('teacher')[:12],
        'last_activity_id': TeacherActivity.objects.order_by('-id').values_list('id', flat=True).first() or 0,
        'act_today_total': todays_activity.count(),
        'act_today_completed': todays_activity.filter(kind='marked', status='completed').count(),
    })
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

    # تمييز الطلاب اللي دفعوا (فعليًا من سجل الدفعات) في الشهر المختار
    pay_year, pay_month = _pay_period(request)
    pay_filter = request.GET.get('pay', '')
    students = _annotate_paid(students, pay_year, pay_month)
    paid_count = students.filter(paid_this_month__gt=0).count()
    unpaid_count = students.filter(paid_this_month=0).count()
    if pay_filter == 'paid':
        students = students.filter(paid_this_month__gt=0)
    elif pay_filter == 'unpaid':
        students = students.filter(paid_this_month=0)

    teachers = Teacher.objects.all()

    context = {
        'country': country,
        'students': students,
        'teachers': teachers,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
    }
    context.update(_pay_context(pay_year, pay_month, pay_filter))
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
                guardian_phone=_or_none(request.POST.get('guardian_phone')),
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
        student.guardian_phone = _or_none(request.POST.get('guardian_phone'))
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
    now = timezone.now()
    context = {
        'student': student,
        'notes': notes,
        'payments': payments,
        'lessons': lessons,
        'paid_this_month': student.total_paid(year=now.year, month=now.month),
        'pay_month_name': ARABIC_MONTHS[now.month],
        'pay_year': now.year,
        'student_conv': getattr(student, 'chat', None) if hasattr(student, 'chat') else None,
        'student_login_display': student.user.get_username() if student.user_id else None,
        'student_portal_url': settings.CANONICAL_URL.rstrip('/') + reverse('student_login'),
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
    if request.method != 'POST':
        # تغيير الحالة لازم يبقى POST (رابط GET ممكن يتفتح بالغلط من المتصفح أو من أي موقع تاني)
        return redirect('student_detail', student_id=student.id)
    student.status = 'inactive' if student.status == 'active' else 'active'
    student.save(update_fields=['status'])

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
    now = timezone.now()
    stat_year = _to_int_or_none(request.GET.get('year')) or now.year
    stat_month = _to_int_or_none(request.GET.get('month')) or now.month
    students = _annotate_paid(teacher.students.all(), stat_year, stat_month)

    context = {
        'teacher': teacher,
        'teacher_login_display': getattr(teacher.user, User.USERNAME_FIELD, None) if teacher.user_id else None,
        'students': students,
        'current_students': students.filter(status='active').count(),
        'previous_students': students.filter(status='inactive').count(),
        'salary_records': teacher.salary_records.all()[:12],
        'salary_this_month': teacher.calculated_salary(year=stat_year, month=stat_month),
        'salary_paid_this_month': teacher.paid_salary(year=stat_year, month=stat_month),
        'salary_remaining': teacher.remaining_salary(year=stat_year, month=stat_month),
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

    pay_year, pay_month = _pay_period(request)
    pay_filter = request.GET.get('pay', '')
    students = _annotate_paid(students, pay_year, pay_month)
    paid_count = students.filter(paid_this_month__gt=0).count()
    unpaid_count = students.filter(paid_this_month=0).count()
    if pay_filter == 'paid':
        students = students.filter(paid_this_month__gt=0)
    elif pay_filter == 'unpaid':
        students = students.filter(paid_this_month=0)

    context = {'students': students, 'paid_count': paid_count, 'unpaid_count': unpaid_count}
    context.update(_pay_context(pay_year, pay_month, pay_filter))
    return render(request, 'core/all_students.html', context)


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
            'completed_lessons': teacher.completed_lessons_count(year=stat_year, month=stat_month),
            'lesson_rate': teacher.lesson_rate,
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

    monthly_data = []
    year_salaries = Decimal('0')
    year_income = Decimal('0')
    year_expenses = Decimal('0')
    year_profit = Decimal('0')

    for month in range(1, 13):
        income = _monthly_income(selected_year, month)
        expenses = _monthly_expenses(selected_year, month)
        salaries = _paid_salaries(selected_year, month)  # المصروف فعليًا في الشهر ده
        profit = income - expenses - salaries
        year_salaries += salaries

        year_income += income
        year_expenses += expenses
        year_profit += profit

        monthly_data.append({
            'month': month,
            'month_name': ARABIC_MONTHS[month],
            'income': income,
            'expenses': expenses,
            'salaries': salaries,
            'profit': profit,
        })

    # السنين المتاحة للاختيار من بينها (فيها بيانات فعلية + السنة الحالية)
    years_with_data = set(Payment.objects.values_list('date__year', flat=True))
    years_with_data |= set(Expense.objects.values_list('date__year', flat=True))
    years_with_data |= set(TeacherSalaryRecord.objects.values_list('payout_date__year', flat=True))
    years_with_data.add(timezone.now().year)
    years_with_data = sorted(years_with_data, reverse=True)

    context = {
        'selected_year': selected_year,
        'years_with_data': years_with_data,
        'monthly_data': monthly_data,
        'total_salaries': year_salaries,
        'year_income': year_income,
        'year_expenses': year_expenses,
        'year_total_salaries': year_salaries,
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
    total_due = total_paid_period = total_remaining = 0
    for t in Teacher.objects.all():
        due = t.calculated_salary(year=salary_year, month=salary_month)
        paid = t.paid_salary(year=salary_year, month=salary_month)
        remaining = t.remaining_salary(year=salary_year, month=salary_month)
        has_record = t.has_salary_record_for(salary_year, salary_month)
        total_due += due
        total_paid_period += paid
        total_remaining += remaining
        teachers_data.append({
            'teacher': t,
            'completed': t.completed_lessons_count(year=salary_year, month=salary_month),
            'calculated_salary': due,
            'paid': paid,
            'remaining': remaining,
            'already_paid_this_month': has_record,
            'fully_paid': has_record and remaining <= 0,
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
        'total_due': round(total_due, 2),
        'total_paid_period': round(total_paid_period, 2),
        'total_remaining': round(total_remaining, 2),
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
def update_teacher_rate(request, teacher_id):
    """تعديل سعر الحصة لمعلمة (الراتب = حلقات تمت × سعر الحصة).
    ملحوظة: التعديل بيسري على الحساب كله (المستحق غير المصروف) - اللي اتصرف قبل كده بيفضل زي ما اتسجل."""
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    if request.method == 'POST':
        rate = _to_decimal_or_zero(request.POST.get('lesson_rate'))
        if rate < 0:
            messages.error(request, 'سعر الحصة لازم يكون رقم موجب.')
        else:
            teacher.lesson_rate = rate
            teacher.save(update_fields=['lesson_rate'])
            messages.success(request, f'تم تحديث سعر حصة "{teacher.name}" إلى {rate} جنيه.')

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

            # الأساسي = حلقات تمت × سعر الحصة - اللي اتصرف قبل كده عن نفس الشهر (عشان ميتدفعش مرتين)
            base_amount = teacher.remaining_salary(year=salary_year, month=salary_month)

            # لو اتصرف المستحق كله قبل كده منسجلش تاني إلا بتأكيد صريح (مثلاً مكافأة إضافية)
            if teacher.has_salary_record_for(salary_year, salary_month) and base_amount <= 0 and not force:
                messages.error(
                    request,
                    f'"{teacher.name}" اتصرفلها مستحق شهر {ARABIC_MONTHS.get(salary_month, salary_month)}/{salary_year} بالكامل قبل كده ومفيش متبقي. '
                    'لو عايزة تسجلي صرف إضافي (مثلاً مكافأة)، فعّلي خيار "تأكيد الصرف مرة تانية".'
                )
                return redirect(f"{reverse('add_salary_record')}?teacher={teacher_id}&salary_year={salary_year}&salary_month={salary_month}")

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

    teachers_data = []
    for t in Teacher.objects.all():
        remaining = t.remaining_salary(year=salary_year, month=salary_month)
        has_record = t.has_salary_record_for(salary_year, salary_month)
        teachers_data.append({
            'teacher': t,
            'calculated_salary': remaining,  # اللي هيتسجل كأساسي = المتبقي
            'already_paid_this_month': has_record,
            'fully_paid': has_record and remaining <= 0,
        })

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
            lesson.mark(new_status, was_late=was_late, by='admin')
            messages.success(request, f'تم تسجيل حالة الحلقة: {valid_statuses[new_status]}.')

    return redirect(_safe_next(request, 'lessons_dashboard'))


@staff_member_required
def mark_lesson_started(request, lesson_id):
    """تسجيل إن الحلقة بدأت فعليًا (زرار "بدء الحلقة")"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if request.method == 'POST':
        lesson.mark_started()
        messages.success(request, f'تم تسجيل بدء حلقة {lesson.student.name}.')
    return redirect(_safe_next(request, 'lessons_dashboard'))


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

        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), base_username)
        if error:
            messages.error(request, error)
            return render(request, 'core/create_teacher_login.html', {
                'teacher': teacher, 'entered_username': request.POST.get('username', '').strip(),
            })

        try:
            create_kwargs = {
                username_field: base_username,
                'is_staff': False,      # <-- الأهم: مفيش دخول للوحة الإدارة نهائيًا
                'is_superuser': False,
            }
            if 'user_type' in user_field_names:
                # من غيرها كان بياخد 'student' افتراضيًا وبيتعمله ملف طالب فاضي بالغلط
                create_kwargs['user_type'] = 'teacher'
            if 'first_name' in user_field_names:
                create_kwargs['first_name'] = teacher.name
            user = User(**create_kwargs)
            user.set_password(password)
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
            f'تم إنشاء حساب دخول لـ "{teacher.name}". {username_field}: {base_username} - بكلمة السر اللي كتبتيها (ابعتيها للمعلمة بنفسك).'
        )
        return redirect('teacher_detail', teacher_id=teacher.id)

    return render(request, 'core/create_teacher_login.html', {'teacher': teacher})


@staff_member_required
def reset_teacher_login_password(request, teacher_id):
    """تغيير كلمة سر المعلمة لو نسيتها - الأدمن هي اللي بتكتب الكلمة الجديدة (مش بتتولد تلقائي)"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    if not teacher.user_id:
        messages.error(request, 'المعلمة دي معندهاش حساب دخول أصلًا.')
        return redirect('teacher_detail', teacher_id=teacher.id)

    if request.method == 'POST':
        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), getattr(teacher.user, User.USERNAME_FIELD, ''))
        if error:
            messages.error(request, error)
        else:
            teacher.user.set_password(password)
            teacher.user.save(update_fields=['password'])
            messages.success(request, f'تم تغيير كلمة سر "{teacher.name}" للكلمة اللي كتبتيها (ابعتيها لها بنفسك).')
            return redirect('teacher_detail', teacher_id=teacher.id)

    return render(request, 'core/reset_login_password.html', {
        'person': teacher.name, 'kind': 'المعلمة',
        'login_name': getattr(teacher.user, User.USERNAME_FIELD, ''),
        'back_url': reverse('teacher_detail', args=[teacher.id]),
    })


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
def teacher_lessons_table(request):
    """جدول حلقات المعلمة عن شهر: تمت / غياب / مؤجلة / قادمة + أجر كل حلقة والإجمالي.
    الأجر = سعر الحصة للحلقات اللي *تمت* بس."""
    teacher = request.user.teacher_profile
    now = timezone.now()
    stat_year = _to_int_or_none(request.GET.get('year')) or now.year
    stat_month = _to_int_or_none(request.GET.get('month')) or now.month
    group = request.GET.get('group', '')
    if group not in ('completed', 'absent', 'postponed', 'upcoming'):
        group = ''

    lessons = teacher.lessons_for_period(stat_year, stat_month).select_related('student').order_by('scheduled_at')

    counts = {'completed': 0, 'absent': 0, 'postponed': 0, 'upcoming': 0}
    total_earned = 0.0
    rows = []
    for lesson in lessons:
        g = lesson.table_group()
        counts[g] += 1
        earned = lesson.earned_amount()
        total_earned += earned
        if not group or group == g:
            rows.append({'lesson': lesson, 'group': g, 'label': lesson.status_label(), 'earned': earned})

    context = {
        'teacher': teacher,
        'rows': rows,
        'counts': counts,
        'total_all': sum(counts.values()),
        'total_earned': round(total_earned, 2),
        'shown_earned': round(sum(r['earned'] for r in rows), 2),
        'lesson_rate': teacher.lesson_rate,
        'group': group,
        'monthly_stats': teacher.monthly_lesson_stats(year=stat_year, month=stat_month),
        'stat_year': stat_year,
        'stat_month': stat_month,
        'stat_month_name': ARABIC_MONTHS.get(stat_month, stat_month),
        'arabic_months': ARABIC_MONTHS,
        'stat_years_range': sorted({now.year - 1, now.year, now.year + 1, stat_year}, reverse=True),
    }
    return render(request, 'core/teacher_lessons_table.html', context)


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
    """المعلمة بتسجل بنفسها حالة حلقتها (تمت / الطالب غاب / عذر / مؤجلة) ووقت التسجيل بيتحفظ
    وبيظهر للأدمن لحظيًا في الداشبورد. القواعد في Lesson.teacher_mark_options."""
    teacher = request.user.teacher_profile
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher=teacher)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status not in lesson.teacher_mark_options():
            messages.error(request, 'مش مسموح تسجلي الحالة دي للحلقة دي دلوقتي (يمكن موعدها لسه ماجاش، أو اتسجلت من المشرفة، أو عدّت ساعة على تسجيلك).')
        else:
            lesson.mark(new_status, by='teacher')
            TeacherActivity.log(teacher, 'marked', lesson, status=new_status)
            messages.success(request, f'تم تسجيل حلقة {lesson.student.name}: {Lesson.TEACHER_MARK_LABELS[new_status]}.')

    return redirect(_safe_next(request, 'teacher_lessons_table'))


@teacher_login_required
def teacher_add_lessons(request):
    """المعلمة بتبني جدولها بنفسها: بتختار طالب من طلابها + اليوم + الساعة (+ تكرار أسبوعي)"""
    teacher = request.user.teacher_profile
    now = timezone.now()
    students = teacher.students.filter(status='active').order_by('name')
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)

    if request.method == 'POST':
        student = students.filter(pk=_to_int_or_none(request.POST.get('student'))).first()
        date_s = request.POST.get('date', '').strip()
        time_s = request.POST.get('time', '').strip()
        duration = min(max(_to_int_or_none(request.POST.get('duration_minutes')) or 30, 10), 180)
        weeks = min(max(_to_int_or_none(request.POST.get('repeat_weeks')) or 1, 1), MAX_REPEAT_WEEKS)
        try:
            start = timezone.make_aware(datetime.strptime(f'{date_s} {time_s}', '%Y-%m-%d %H:%M'))
        except ValueError:
            start = None

        if not student or not start:
            messages.error(request, 'من فضلك اختاري الطالب وحددي اليوم والساعة.')
        elif not TEACHER_CAN_ADD_PAST_LESSONS and start < today_start:
            messages.error(request, 'مينفعش تضيفي حلقة في يوم فات. الحلقات الفايتة بتتسجل من المشرفة.')
        else:
            created = []
            for w in range(weeks):
                when = start + timedelta(weeks=w)
                if Lesson.objects.filter(teacher=teacher, student=student, scheduled_at=when).exists():
                    continue
                created.append(Lesson.objects.create(
                    student=student, teacher=teacher, scheduled_at=when,
                    duration_minutes=duration, created_by='teacher',
                ))
            if created:
                TeacherActivity.log(teacher, 'added', created[0], count=len(created))
                messages.success(request, f'تم إضافة {len(created)} حلقة مع {student.name} لجدولك.')
                return redirect('teacher_lessons_table')
            messages.info(request, 'الحلقات دي موجودة بالفعل في جدولك.')

    context = {
        'teacher': teacher,
        'students': students,
        'today': timezone.localdate(),
        'upcoming': teacher.lessons.filter(status='scheduled', scheduled_at__gte=now).select_related('student').order_by('scheduled_at')[:30],
        'max_weeks': MAX_REPEAT_WEEKS,
        'allow_past': TEACHER_CAN_ADD_PAST_LESSONS,
    }
    return render(request, 'core/teacher_add_lessons.html', context)


@teacher_login_required
def teacher_delete_lesson(request, lesson_id):
    """المعلمة تمسح حلقة هي اللي أضافتها ولسه ما جاش موعدها (والأدمن بيشوف إنها اتمسحت)"""
    teacher = request.user.teacher_profile
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher=teacher)
    if request.method == 'POST':
        if lesson.teacher_can_delete():
            TeacherActivity.log(teacher, 'removed', lesson)
            lesson.delete()
            messages.success(request, 'تم حذف الحلقة من جدولك.')
        else:
            messages.error(request, 'تقدري تمسحي بس حلقة إنتِ اللي أضفتيها ولسه ماجاش موعدها. غير كده كلمي المشرفة.')
    return redirect(_safe_next(request, 'teacher_add_lessons'))


# =======================
# متابعة نشاط المعلمات (للأدمن): فيد لحظي + صفحة تفصيلية
# =======================
@staff_member_required
def activity_feed_json(request):
    """الداشبورد بيسأله كل ~15 ثانية: عايز أي نشاط جديد بعد آخر رقم شفته؟
    من غير after بيرجع آخر رقم بس (عشان الصفحة تبدأ من دلوقتي وماترنش على القديم)."""
    last_id = TeacherActivity.objects.order_by('-id').values_list('id', flat=True).first() or 0
    after = _to_int_or_none(request.GET.get('after'))
    events = []
    if after is not None:
        for e in TeacherActivity.objects.select_related('teacher').filter(id__gt=after).order_by('id')[:30]:
            events.append({
                'id': e.id, 'teacher': e.teacher.name, 'text': e.text(), 'tone': e.tone(),
                'kind': e.kind, 'time': e.short_time(),
            })
    return JsonResponse({'last_id': last_id, 'events': events})


@staff_member_required
def teacher_activity(request):
    """سجل نشاط المعلمات في يوم معيّن (افتراضيًا النهاردة) + ملخص لكل معلمة"""
    day = timezone.localdate()
    raw = request.GET.get('date', '').strip()
    if raw:
        try:
            day = datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    teacher_id = _to_int_or_none(request.GET.get('teacher'))

    events = TeacherActivity.objects.select_related('teacher').filter(created_at__date=day)
    if teacher_id:
        events = events.filter(teacher_id=teacher_id)

    summary = {}
    for e in events:
        row = summary.setdefault(e.teacher_id, {'teacher': e.teacher, 'added': 0, 'completed': 0, 'absent': 0, 'other': 0})
        if e.kind == 'added':
            row['added'] += e.count
        elif e.kind == 'marked':
            if e.status == 'completed':
                row['completed'] += 1
            elif e.status == 'student_absent':
                row['absent'] += 1
            else:
                row['other'] += 1

    context = {
        'events': events,
        'day': day,
        'teachers': Teacher.objects.all(),
        'selected_teacher': teacher_id,
        'summary_rows': list(summary.values()),
    }
    return render(request, 'core/teacher_activity.html', context)


@teacher_login_required
def teacher_schedule_requests(request):
    """المعلمة تشوف طلبات تعديل المواعيد بتاعتها وتقدر تبعت طلب تعديل جديد
    لحلقة قائمة - مش بيتفعّل على طول، لازم موافقة مشرفتها. (تسجيل مواعيد
    جديدة بقى بتتم من خلال المشرفة)"""
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
        messages.success(request, 'تم إرسال طلب تعديل الموعد لمشرفتك، هيتفعّل بعد الموافقة عليه.')
        return redirect('teacher_schedule_requests')

    context = {
        'teacher': teacher,
        'requests': teacher.schedule_requests.all(),
        'upcoming_lessons': teacher.lessons.filter(status='scheduled').order_by('scheduled_at')[:20],
    }
    return render(request, 'core/teacher_schedule_requests.html', context)


@teacher_login_required
def teacher_evaluations_list(request):
    """المعلمة تشوف (بس تشوف - من غير تعديل) كل التقييمات الشهرية اللي
    اتعملت لطلابها، سواء من الإدارة أو من مشرفتها"""
    teacher = request.user.teacher_profile
    evaluations = MonthlyEvaluation.objects.filter(student__teacher=teacher).select_related('student').order_by('-created_at')
    return render(request, 'core/teacher_evaluations_list.html', {
        'teacher': teacher, 'evaluations': evaluations,
    })


@teacher_login_required
def teacher_evaluation_detail(request, evaluation_id):
    teacher = request.user.teacher_profile
    evaluation = get_object_or_404(MonthlyEvaluation, pk=evaluation_id, student__teacher=teacher)
    public_url = request.build_absolute_uri(reverse('public_evaluation', args=[evaluation.public_token]))
    return render(request, 'core/teacher_evaluation_detail.html', {
        'teacher': teacher, 'evaluation': evaluation, 'public_url': public_url,
    })


@teacher_login_required
def teacher_register_schedule(request):
    """المعلمة بتبني جدولها بنفسها - بنحوّلها لصفحة إضافة الحلقات"""
    return redirect('teacher_add_lessons')


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
        'students_json': json.dumps(students_data, ensure_ascii=False).replace('<', '\\u003c'),
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
    evaluation = get_object_or_404(MonthlyEvaluation.objects.select_related('student'), public_token=token)
    return render(request, 'core/evaluation_public.html', {
        'evaluation': evaluation,
        'student_portal_url': reverse('student_login'),
    })

# =======================
# إدارة المشرفات (من لوحة الأدمن)
# =======================
@staff_member_required
def supervisors_list(request):
    supervisors = Supervisor.objects.all()
    unassigned_teachers = Teacher.objects.filter(supervisor__isnull=True)

    if request.method == 'POST':
        # تعيين/تغيير المعلمات المربوطة بمشرفة معينة
        supervisor_id = request.POST.get('supervisor_id')
        teacher_ids = request.POST.getlist('teacher_ids')
        supervisor = get_object_or_404(Supervisor, pk=supervisor_id)

        if len(teacher_ids) > 5:
            messages.error(request, 'المفروض كل مشرفة متبقاش مسؤولة عن أكتر من 5 معلمات.')
        else:
            Teacher.objects.filter(supervisor=supervisor).update(supervisor=None)
            Teacher.objects.filter(id__in=teacher_ids).update(supervisor=supervisor)
            messages.success(request, f'تم تحديث معلمات "{supervisor.name}".')
        return redirect('supervisors_list')

    context = {
        'supervisors': supervisors,
        'unassigned_teachers': unassigned_teachers,
        'all_teachers': Teacher.objects.all(),
    }
    return render(request, 'core/supervisors_list.html', context)


@staff_member_required
def add_supervisor(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'من فضلك أدخلي اسم المشرفة.')
        else:
            Supervisor.objects.create(name=name, phone=_or_none(request.POST.get('phone')))
            messages.success(request, 'تم إضافة المشرفة بنجاح.')
            return redirect('supervisors_list')
    return render(request, 'core/add_supervisor.html')


@staff_member_required
def create_supervisor_login(request, supervisor_id):
    """نفس فكرة create_teacher_login بالظبط بس لحساب مشرفة"""
    supervisor = get_object_or_404(Supervisor, pk=supervisor_id)
    username_field = User.USERNAME_FIELD
    user_field_names = {f.name for f in User._meta.get_fields()}

    if supervisor.user_id:
        messages.error(request, f'"{supervisor.name}" عندها حساب دخول بالفعل ({getattr(supervisor.user, username_field)}).')
        return redirect('supervisors_list')

    if request.method == 'POST':
        base_username = request.POST.get('username', '').strip()
        if not base_username:
            base_username = 'supervisor_' + str(supervisor.id)
            if username_field == 'email' and '@' not in base_username:
                base_username = f'supervisor{supervisor.id}@example.com'

        if User.objects.filter(**{username_field: base_username}).exists():
            messages.error(request, f'"{base_username}" مستخدم قبل كده، اختاري قيمة تانية.')
            return redirect('create_supervisor_login', supervisor_id=supervisor.id)

        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), base_username)
        if error:
            messages.error(request, error)
            return render(request, 'core/create_supervisor_login.html', {
                'supervisor': supervisor, 'entered_username': request.POST.get('username', '').strip(),
            })

        create_kwargs = {
            username_field: base_username,
            'is_staff': False,
            'is_superuser': False,
        }
        if 'user_type' in user_field_names:
            create_kwargs['user_type'] = 'supervisor'
        if 'first_name' in user_field_names:
            create_kwargs['first_name'] = supervisor.name
        user = User(**create_kwargs)
        user.set_password(password)
        user.save()

        supervisor.user = user
        supervisor.save(update_fields=['user'])

        messages.success(
            request,
            f'تم إنشاء حساب دخول لـ "{supervisor.name}". {username_field}: {base_username} - بكلمة السر اللي كتبتيها (ابعتيها للمشرفة بنفسك).'
        )
        return redirect('supervisors_list')

    return render(request, 'core/create_supervisor_login.html', {'supervisor': supervisor})


@staff_member_required
def reset_supervisor_login_password(request, supervisor_id):
    """تغيير كلمة سر المشرفة - الأدمن هي اللي بتكتب الكلمة الجديدة (مش بتتولد تلقائي)"""
    supervisor = get_object_or_404(Supervisor, pk=supervisor_id)
    if not supervisor.user_id:
        messages.error(request, 'المشرفة دي معندهاش حساب دخول أصلًا.')
        return redirect('supervisors_list')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), getattr(supervisor.user, User.USERNAME_FIELD, ''))
        if error:
            messages.error(request, error)
        else:
            supervisor.user.set_password(password)
            supervisor.user.save(update_fields=['password'])
            messages.success(request, f'تم تغيير كلمة سر "{supervisor.name}" للكلمة اللي كتبتيها (ابعتيها لها بنفسك).')
            return redirect('supervisors_list')

    return render(request, 'core/reset_login_password.html', {
        'person': supervisor.name, 'kind': 'المشرفة',
        'login_name': getattr(supervisor.user, User.USERNAME_FIELD, ''),
        'back_url': reverse('supervisors_list'),
    })


@staff_member_required
def revoke_supervisor_login(request, supervisor_id):
    supervisor = get_object_or_404(Supervisor, pk=supervisor_id)
    if request.method == 'POST' and supervisor.user_id:
        old_user = supervisor.user
        supervisor.user = None
        supervisor.save(update_fields=['user'])
        old_user.is_active = False
        old_user.save(update_fields=['is_active'])
        messages.success(request, f'تم إلغاء حساب دخول "{supervisor.name}".')
    return redirect('supervisors_list')


# =======================
# بورتال المشرفة (تسجيل دخول محدود - بتشوف بس معلماتها الخمسة وطلابهم)
# =======================
def supervisor_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'supervisor_profile'):
        return redirect('supervisor_portal_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'اسم المستخدم أو كلمة السر غلط.')
        elif not hasattr(user, 'supervisor_profile'):
            messages.error(request, 'الحساب ده مش حساب مشرفة.')
        elif not user.is_active:
            messages.error(request, 'الحساب ده متوقف، كلمي الإدارة.')
        else:
            auth_login(request, user)
            return redirect('supervisor_portal_home')

    return render(request, 'core/supervisor_login.html')


def supervisor_logout(request):
    auth_logout(request)
    return redirect('supervisor_login')


@supervisor_login_required
def supervisor_portal_home(request):
    """داشبورد المشرفة الرئيسية: نظرة شاملة على كل معلماتها - مواعيد اليوم،
    إحصائيات الحضور/الغياب، طلبات المواعيد المعلقة، آخر التقارير الشهرية،
    ورسم بياني لأداء الأسبوع"""
    supervisor = request.user.supervisor_profile
    teachers = supervisor.teachers.all()
    today = timezone.localdate()
    week_ago = today - timedelta(days=6)

    today_lessons = Lesson.objects.filter(
        teacher__in=teachers, scheduled_at__date=today
    ).select_related('teacher', 'student').order_by('scheduled_at')

    week_lessons = Lesson.objects.filter(teacher__in=teachers, scheduled_at__date__gte=week_ago, scheduled_at__date__lte=today)

    teachers_summary = []
    for t in teachers:
        teachers_summary.append({
            'teacher': t,
            'students_count': t.students.filter(status='active').count(),
            'lessons_today_count': today_lessons.filter(teacher=t).count(),
            'unrecorded_count': len([l for l in t.lessons.filter(status='scheduled') if l.is_overdue_unrecorded()]),
        })

    # إحصائيات عامة للأسبوع الحالي (لرسم بياني بسيط في الداشبورد)
    ARABIC_DAY_ABBR = ['اثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت', 'أحد']
    week_chart_labels = []
    week_chart_completed = []
    week_chart_absent = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_lessons = week_lessons.filter(scheduled_at__date=day)
        week_chart_labels.append(ARABIC_DAY_ABBR[day.weekday()])
        week_chart_completed.append(day_lessons.filter(status='completed').count())
        week_chart_absent.append(day_lessons.filter(status__in=['student_absent', 'teacher_absent']).count())

    total_students = sum(row['students_count'] for row in teachers_summary)
    pending_requests = ScheduleRequest.objects.filter(teacher__in=teachers, status='pending').select_related('student', 'teacher').order_by('-created_at')
    recent_evaluations = MonthlyEvaluation.objects.filter(student__teacher__in=teachers).select_related('student').order_by('-created_at')[:6]

    context = {
        'supervisor': supervisor,
        'teachers_summary': teachers_summary,
        'today_lessons': today_lessons,
        'today': today,
        'total_teachers': teachers.count(),
        'total_students': total_students,
        'week_completed': week_lessons.filter(status='completed').count(),
        'week_absent': week_lessons.filter(status__in=['student_absent', 'teacher_absent']).count(),
        'week_excused': week_lessons.filter(status='excused').count(),
        'pending_requests_count': pending_requests.count(),
        'pending_requests': pending_requests[:5],
        'recent_evaluations': recent_evaluations,
        'week_chart_labels': json.dumps(week_chart_labels, ensure_ascii=False),
        'week_chart_completed': json.dumps(week_chart_completed),
        'week_chart_absent': json.dumps(week_chart_absent),
    }
    return render(request, 'core/supervisor_portal_home.html', context)


@supervisor_login_required
def supervisor_schedule_requests_list(request):
    """طلبات تعديل/إضافة مواعيد من معلمات المشرفة - بتراجعها وتوافق أو ترفض"""
    supervisor = request.user.supervisor_profile
    teachers = supervisor.teachers.all()
    status = request.GET.get('status', 'pending')
    requests_qs = ScheduleRequest.objects.filter(teacher__in=teachers).select_related('student', 'teacher')
    if status in ('pending', 'approved', 'rejected'):
        requests_qs = requests_qs.filter(status=status)
    return render(request, 'core/supervisor_schedule_requests.html', {
        'supervisor': supervisor, 'requests': requests_qs, 'selected_status': status,
    })


@supervisor_login_required
def supervisor_review_schedule_request(request, request_id):
    supervisor = request.user.supervisor_profile
    req = get_object_or_404(ScheduleRequest, pk=request_id, teacher__supervisor=supervisor)
    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('admin_note', '').strip()
        if action == 'approve':
            req.approve(admin_note=note)
            messages.success(request, f'تمت الموافقة على طلب "{req.student.name}".')
        elif action == 'reject':
            req.reject(admin_note=note)
            messages.warning(request, f'تم رفض طلب "{req.student.name}".')
    return redirect('supervisor_schedule_requests_list')


@supervisor_login_required
def supervisor_teacher_detail(request, teacher_id):
    """المشرفة تدخل على معلمة معينة (لازم تكون من ضمن معلماتها) وتشوف
    طلابها وحلقاتهم وتسجل حالة كل حلقة (تمت / لم تتم + السبب) + ملاحظات
    + إحصائية غياب واعتذارات المعلمة"""
    supervisor = request.user.supervisor_profile
    teacher = get_object_or_404(Teacher, pk=teacher_id, supervisor=supervisor)

    lessons = teacher.lessons.select_related('student').order_by('-scheduled_at')[:60]

    all_lessons = teacher.lessons.all()
    attendance_stats = {
        'total': all_lessons.count(),
        'completed': all_lessons.filter(status='completed').count(),
        'teacher_absent': all_lessons.filter(status='teacher_absent').count(),
        'excused': all_lessons.filter(status='excused').count(),
        'student_absent': all_lessons.filter(status='student_absent').count(),
        'cancelled': all_lessons.filter(status='cancelled').count(),
    }

    context = {
        'supervisor': supervisor,
        'teacher': teacher,
        'students': teacher.students.filter(status='active'),
        'lessons': lessons,
        'status_choices': Lesson.STATUS_CHOICES,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'core/supervisor_teacher_detail.html', context)


@supervisor_login_required
def supervisor_mark_lesson(request, lesson_id):
    """المشرفة تسجل حالة حلقة معلمة من معلماتها هي بس (مش أي معلمة تانية)
    مع السبب (غياب / عذر / مؤجلة) والملاحظات"""
    supervisor = request.user.supervisor_profile
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher__supervisor=supervisor)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('notes', '').strip()
        valid_statuses = dict(Lesson.STATUS_CHOICES)

        if not new_status or new_status not in valid_statuses or new_status == 'unregistered':
            messages.error(request, 'من فضلك اختاري حالة صحيحة قبل الحفظ.')
        else:
            lesson.mark(new_status, by='supervisor')
            if note:
                lesson.notes = note
                lesson.save(update_fields=['notes'])
            messages.success(request, f'تم تسجيل حالة حلقة {lesson.student.name}: {valid_statuses[new_status]}.')

    next_url = request.POST.get('next')
    if next_url == 'home':
        return redirect('supervisor_portal_home')
    return redirect('supervisor_teacher_detail', teacher_id=lesson.teacher_id)


@supervisor_login_required
def supervisor_register_student_schedule(request, student_id):
    """المشرفة تسجل جدول مواعيد أسبوعي متكرر لطالب معين عند إحدى معلماتها
    (بديل عن كون المعلمة هي اللي بتسجل مواعيدها بنفسها)"""
    supervisor = request.user.supervisor_profile
    student = get_object_or_404(Student, pk=student_id, teacher__supervisor=supervisor)
    teacher = student.teacher

    WEEKDAYS = [
        (0, 'الإثنين'), (1, 'الثلاثاء'), (2, 'الأربعاء'), (3, 'الخميس'),
        (4, 'الجمعة'), (5, 'السبت'), (6, 'الأحد'),
    ]

    if request.method == 'POST':
        weekdays = request.POST.getlist('weekday')
        lesson_time = _or_none(request.POST.get('lesson_time'))
        weeks_count = _to_int_or_none(request.POST.get('weeks_count')) or 4
        duration_minutes = _to_int_or_none(request.POST.get('duration_minutes')) or 30

        if not weekdays or not lesson_time:
            messages.error(request, 'من فضلك حددي يوم/أيام الحلقة والوقت.')
            return redirect('supervisor_register_student_schedule', student_id=student.id)

        try:
            weekdays = {int(w) for w in weekdays if 0 <= int(w) <= 6}
            hour, minute = [int(x) for x in lesson_time.split(':')[:2]]
            if not (0 <= hour <= 23 and 0 <= minute <= 59) or not weekdays:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'الأيام أو الوقت مش مظبوطين.')
            return redirect('supervisor_register_student_schedule', student_id=student.id)
        weeks_count = min(max(weeks_count, 1), MAX_REPEAT_WEEKS)
        duration_minutes = min(max(duration_minutes, 10), 180)

        created_count = 0
        today = timezone.localdate()
        end_date = today + timedelta(days=weeks_count * 7)
        current_date = today
        while current_date <= end_date:
            if current_date.weekday() in weekdays:
                naive_dt = datetime.combine(current_date, datetime.min.time()).replace(hour=hour, minute=minute)
                scheduled_at = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
                if scheduled_at >= timezone.now() and not Lesson.objects.filter(student=student, teacher=teacher, scheduled_at=scheduled_at).exists():
                    Lesson.objects.create(student=student, teacher=teacher, scheduled_at=scheduled_at, duration_minutes=duration_minutes)
                    created_count += 1
            current_date += timedelta(days=1)

        if created_count:
            messages.success(request, f'تم تسجيل {created_count} حلقة لـ "{student.name}".')
        else:
            messages.warning(request, 'مفيش حلقات جديدة اتضافت (ممكن تكون كل المواعيد دي متسجلة قبل كده).')
        return redirect('supervisor_student_schedule_view', student_id=student.id)

    return render(request, 'core/supervisor_register_student_schedule.html', {
        'supervisor': supervisor, 'student': student, 'teacher': teacher, 'weekdays': WEEKDAYS,
    })


def _format_arabic_time(dt):
    """تنسيق الوقت بصيغة عربية (12 ساعة) بدون الاعتماد على %-I اللي مش
    شغالة على ويندوز - بنحسبها يدويًا عشان تشتغل على أي سيرفر"""
    local_dt = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    hour24 = local_dt.hour
    period = 'صباحًا' if hour24 < 12 else 'مساءً'
    hour12 = hour24 % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12}:{local_dt.minute:02d} {period}"


@supervisor_login_required
def supervisor_student_schedule_view(request, student_id):
    """عرض جدول مواعيد الطالب الأسبوعي بشكل بصري (يوم/وقت) - مبني على
    الحلقات الفعلية المسجلة للطالب، مش جدول منفصل"""
    supervisor = request.user.supervisor_profile
    student = get_object_or_404(Student, pk=student_id, teacher__supervisor=supervisor)

    DAY_ORDER = [(5, 'السبت', '#FADCE3'), (6, 'الأحد', '#D6E8FA'), (0, 'الاثنين', '#DCF3DD'),
                 (1, 'الثلاثاء', '#E7DEF7'), (2, 'الأربعاء', '#D6E8FA'), (3, 'الخميس', '#FADCE3'),
                 (4, 'الجمعة', '#E7DEF7')]

    upcoming = list(student.lessons.filter(scheduled_at__gte=timezone.now() - timedelta(days=1)).order_by('scheduled_at'))
    schedule_rows = []
    for weekday_num, day_name, color in DAY_ORDER:
        match = next((l for l in upcoming if l.scheduled_at.weekday() == weekday_num), None)
        schedule_rows.append({
            'day': day_name, 'color': color,
            'time': _format_arabic_time(match.scheduled_at) if match else None,
        })

    return render(request, 'core/supervisor_student_schedule_view.html', {
        'supervisor': supervisor, 'student': student, 'schedule_rows': schedule_rows,
    })


@supervisor_login_required
def supervisor_add_evaluation(request, student_id):
    """المشرفة تنشئ تقرير/تقييم شهري لطالب عند إحدى معلماتها - بيستخدم نفس
    نموذج التقييم اللي الإدارة بتستخدمه"""
    supervisor = request.user.supervisor_profile
    student = get_object_or_404(Student, pk=student_id, teacher__supervisor=supervisor)
    default_month = timezone.localdate().strftime('%Y-%m')

    if request.method == 'POST':
        evaluation = MonthlyEvaluation.objects.create(
            student=student,
            student_name=request.POST.get('student_name', '').strip() or student.name,
            teacher_name=request.POST.get('teacher_name', '').strip() or (student.teacher.name if student.teacher else ''),
            package_name=request.POST.get('package_name', '').strip() or student.package_name,
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
        messages.success(request, f'تم إنشاء تقرير "{evaluation.student_name}" الشهري بنجاح.')
        return redirect('supervisor_evaluation_detail', evaluation_id=evaluation.id)

    return render(request, 'core/supervisor_add_evaluation.html', {
        'supervisor': supervisor, 'student': student, 'default_month': default_month,
    })


@supervisor_login_required
def supervisor_evaluation_detail(request, evaluation_id):
    supervisor = request.user.supervisor_profile
    evaluation = get_object_or_404(MonthlyEvaluation, pk=evaluation_id, student__teacher__supervisor=supervisor)
    public_url = request.build_absolute_uri(reverse('public_evaluation', args=[evaluation.public_token]))
    return render(request, 'core/supervisor_evaluation_detail.html', {
        'supervisor': supervisor, 'evaluation': evaluation, 'public_url': public_url,
    })


# =======================
# بورتال المعلمة: المنهج / السبورة التفاعلية / الألعاب
# =======================
@teacher_login_required
def teacher_curriculum(request):
    """قائمة ملفات المنهج (والمصحف) - بتتفتح جوه البورتال بس ومفيهاش لينك
    مباشر للملف يتشارك برا؛ كل عرض بيمر على teacher_curriculum_view اللي
    بتتأكد إن اللي بيفتح فعلًا معلمة مسجلة دخول"""
    documents = CurriculumDocument.objects.filter(is_active=True)
    return render(request, 'core/teacher_curriculum.html', {
        'documents': documents,
        'teacher': request.user.teacher_profile,
    })


@teacher_login_required
def teacher_quran_reader(request):
    """المصحف الشريف - بيتجاب مباشرة من مصدر مفتوح وموثوق على الإنترنت
    (صفحة بصفحة حسب السورة المختارة)، فمش محتاج رفع ملف من الإدارة خالص"""
    return render(request, 'core/teacher_quran_reader.html', {'teacher': request.user.teacher_profile})


@teacher_login_required
def teacher_curriculum_view(request, doc_id):
    """فتح ملف منهج معين جوه إطار محمي (بدون إظهار رابط الملف الأصلي في
    الصفحة، ومع علامة مائية باسم المعلمة عشان لو اتصور تتعرف مين بعته)"""
    document = get_object_or_404(CurriculumDocument, pk=doc_id, is_active=True)
    return render(request, 'core/teacher_curriculum_view.html', {
        'document': document,
        'teacher': request.user.teacher_profile,
    })


@teacher_login_required
def teacher_curriculum_stream(request, doc_id):
    """بتبعت محتوى ملف الـ PDF نفسه (bytes) للمعلمة اللي عاملة تسجيل دخول
    بس، من غير ما تحتاج تعرف رابط الملف الأصلي في storage. الصفحة بتحول
    الناتج لـ blob محلي جوه المتصفح، فمينفعش يتشارك كلينك زي ملف عادي"""
    from django.http import FileResponse, Http404
    document = get_object_or_404(CurriculumDocument, pk=doc_id, is_active=True)
    if not document.file:
        raise Http404
    return FileResponse(document.file.open('rb'), content_type='application/pdf')


@teacher_login_required
def teacher_whiteboard(request):
    return render(request, 'core/teacher_whiteboard.html', {'teacher': request.user.teacher_profile})


@teacher_login_required
def teacher_games(request):
    return render(request, 'core/teacher_games.html', {'teacher': request.user.teacher_profile})


# =======================
# حساب بوابة الطالب (الطالب أو ولي أمره بيدخل بيه للشات مع المعلمة)
# =======================
@staff_member_required
def create_student_login(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if student.user_id:
        messages.info(request, f'"{student.name}" عنده حساب بالفعل ({student.user.get_username()}).')
        return redirect('student_detail', student_id=student.id)

    suggested = f'st{student.id}'
    if request.method == 'POST':
        username = request.POST.get('username', '').strip() or suggested
        if User.objects.filter(**{User.USERNAME_FIELD: username}).exists():
            messages.error(request, f'"{username}" مستخدم قبل كده، اختاري اسم تاني.')
            return render(request, 'core/create_student_login.html', {'student': student, 'suggested': suggested, 'entered_username': username})
        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), username)
        if error:
            messages.error(request, error)
            return render(request, 'core/create_student_login.html', {'student': student, 'suggested': suggested, 'entered_username': username})
        user = User(**{User.USERNAME_FIELD: username, 'is_staff': False, 'is_superuser': False})
        if hasattr(user, 'user_type'):
            user.user_type = 'student'
        if hasattr(user, 'first_name'):
            user.first_name = student.name[:150]
        user._skip_student_profile = True
        user.set_password(password)
        user.save()
        student.user = user
        student.save(update_fields=['user'])
        messages.success(request, f'تم إنشاء حساب بوابة الطالب لـ "{student.name}": اسم المستخدم {username} - ابعتيله اسم المستخدم وكلمة السر ورابط الدخول.')
        return redirect('student_detail', student_id=student.id)
    return render(request, 'core/create_student_login.html', {'student': student, 'suggested': suggested})


@staff_member_required
def reset_student_login_password(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if not student.user_id:
        messages.error(request, 'الطالب ده معندوش حساب أصلًا.')
        return redirect('student_detail', student_id=student.id)
    if request.method == 'POST':
        password = request.POST.get('password', '')
        error = _check_chosen_password(password, request.POST.get('password2', ''), student.user.get_username())
        if error:
            messages.error(request, error)
        else:
            student.user.set_password(password)
            student.user.is_active = True
            student.user.save(update_fields=['password', 'is_active'])
            messages.success(request, f'تم تغيير كلمة سر "{student.name}".')
            return redirect('student_detail', student_id=student.id)
    return render(request, 'core/reset_login_password.html', {
        'person': student.name, 'kind': 'الطالب', 'login_name': student.user.get_username(),
        'back_url': reverse('student_detail', args=[student.id]),
    })


@staff_member_required
def revoke_student_login(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST' and student.user_id:
        old = student.user
        student.user = None
        student.save(update_fields=['user'])
        old.is_active = False
        old.save(update_fields=['is_active'])
        messages.success(request, f'تم إلغاء حساب "{student.name}".')
    return redirect('student_detail', student_id=student.id)
