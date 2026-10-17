"""بوابة الطالب: الطالب (أو ولي أمره) بيدخل يشوف مواعيده وتقاريره ويكلم معلمته في الشات."""
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.utils import timezone

from chat.views import student_login_required


def student_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'core_student'):
        return redirect('student_portal_home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username', '').strip(),
                            password=request.POST.get('password', ''))
        if user is None:
            messages.error(request, 'اسم المستخدم أو كلمة السر غلط.')
        elif not hasattr(user, 'core_student'):
            messages.error(request, 'الحساب ده مش حساب طالب.')
        else:
            auth_login(request, user)
            return redirect('student_portal_home')
    return render(request, 'core/student_login.html')


def student_logout(request):
    auth_logout(request)
    return redirect('student_login')


@student_login_required
def student_portal_home(request):
    student = request.user.core_student
    now = timezone.now()
    conv = getattr(student, 'chat', None)
    last_msg = None
    if conv:
        last_msg = conv.messages.exclude(status='blocked', sender_type__in=['teacher', 'admin']).order_by('-id').first()
    month_lessons = student.lessons.filter(scheduled_at__year=now.year, scheduled_at__month=now.month)
    completed_month = month_lessons.filter(status='completed').count()
    completed_all = student.lessons_completed_count()
    pct = min(100, round(completed_all / student.lessons_count * 100)) if student.lessons_count else 0
    return render(request, 'core/student_portal_home.html', {
        'student': student,
        'teacher': student.teacher,
        'conv': conv,
        'last_msg': last_msg,
        'upcoming': student.lessons.filter(status='scheduled', scheduled_at__gte=now).order_by('scheduled_at')[:6],
        'completed_month': completed_month,
        'month_total': month_lessons.count(),
        'completed_all': completed_all,
        'progress_pct': pct,
        'evaluations': student.evaluations.all()[:6],
        **_learning_ctx(student),
    })


def _learning_ctx(student):
    """الواجبات والنجوم وآية اليوم في الصفحة الرئيسية للطالب"""
    try:
        from learning import quran, services
        from learning.models import Homework
    except Exception:
        return {}
    hws = list(Homework.objects.filter(student=student).prefetch_related('submissions')[:50])
    todo = [h for h in hws if h.status() in ('new', 'redo')]
    # آية اليوم: بتتغير كل يوم من جزء عم والسور القصيرة المشهورة
    day = timezone.localdate().toordinal()
    pool = [(s, a) for s in [1] + list(range(78, 115)) for a in range(1, quran.ayah_count(s) + 1)]
    s, a = pool[(day * 7919) % len(pool)]
    return {
        'hw_todo': todo[:3], 'hw_todo_count': len(todo), 'st': services.stats(student),
        'daily': {'surah': s, 'ayah': a, 'name': quran.surah_name(s), 'text': quran.verses(s, a, a)[0][1],
                  'audio': quran.audio_url(quran.DEFAULT_RECITER, s, a)},
    }
