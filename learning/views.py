import json
import os
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Max, Prefetch, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from chat.views import student_login_required
from core.models import Student, Teacher
from core.views import teacher_login_required

from . import quran, services
from .models import Homework, StudentActivity, Submission


def _player_ctx(extra=None):
    ctx = {'reciters': quran.RECITERS, 'default_reciter': quran.DEFAULT_RECITER,
           'quran_index': quran.index()}
    ctx.update(extra or {})
    return ctx


def _parse_hw_form(request, teacher):
    p = request.POST
    errors = []
    ids = [int(x) for x in p.getlist('students') if x.isdigit()]
    students = list(Student.objects.filter(teacher=teacher, pk__in=ids))
    if not students:
        errors.append('اختاري طالب واحد على الأقل.')
    kind = p.get('kind') if p.get('kind') in dict(Homework.KIND_CHOICES) else 'memorize'
    data = {'kind': kind, 'title': p.get('title', ''), 'instructions': p.get('instructions', '')}
    s = p.get('surah', '')
    if s.isdigit() and 1 <= int(s) <= 114:
        s = int(s)
        n = quran.ayah_count(s)
        a = int(p['ayah_from']) if p.get('ayah_from', '').isdigit() else 1
        b = int(p['ayah_to']) if p.get('ayah_to', '').isdigit() else n
        a, b = max(1, min(a, n)), max(1, min(b, n))
        if a > b:
            a, b = b, a
        data.update(surah=s, ayah_from=a, ayah_to=b)
    elif kind != 'other':
        errors.append('اختاري السورة والآيات.')
    if not data.get('surah') and not data['title'].strip() and not data['instructions'].strip():
        errors.append('اكتبي عنوان أو تعليمات للنشاط.')
    d = p.get('due_date', '')
    if d:
        try:
            data['due_date'] = date.fromisoformat(d)
        except ValueError:
            errors.append('تاريخ التسليم مش صحيح.')
    return students, data, errors


# =========================================================
# المعلمة
# =========================================================
@teacher_login_required
def teacher_list(request):
    teacher = request.user.teacher_profile
    f = request.GET.get('f', 'review')
    qs = (Homework.objects.filter(teacher=teacher).select_related('student')
          .prefetch_related('submissions'))
    sid = request.GET.get('student', '')
    if sid.isdigit():
        qs = qs.filter(student_id=sid)
    rows = list(qs[:300])
    pending = [h for h in rows if h.status() == 'submitted']
    if f == 'review':
        shown = pending
    elif f == 'open':
        shown = [h for h in rows if h.status() in ('new', 'redo')]
    else:
        shown = rows
    return render(request, 'learning/teacher_list.html', {
        'teacher': teacher, 'rows': shown, 'f': f, 'pending_count': len(pending),
        'students': Student.objects.filter(teacher=teacher).order_by('name'), 'sid': sid,
    })


@teacher_login_required
def teacher_new(request):
    teacher = request.user.teacher_profile
    students = Student.objects.filter(teacher=teacher, status='active').order_by('name')
    if not students.exists():
        students = Student.objects.filter(teacher=teacher).order_by('name')
    if request.method == 'POST':
        chosen, data, errors = _parse_hw_form(request, teacher)
        if not errors:
            try:
                created = services.create_homework(teacher=teacher, students=chosen, data=data,
                                                   teacher_audio=request.FILES.get('teacher_audio'))
            except services.Refused as e:
                errors.append(str(e))
            else:
                messages.success(request, f'تم إرسال الواجب لـ {len(created)} طالب، وهيوصلهم إشعار 🎉')
                return redirect('learning_teacher_list' if len(created) > 1 else 'learning_teacher_detail',
                                *([] if len(created) > 1 else [created[0].pk]))
        for e in errors:
            messages.error(request, e)
    pre = request.GET.get('student', '')
    return render(request, 'learning/teacher_new.html', _player_ctx({
        'teacher': teacher, 'students': students, 'kinds': Homework.KIND_CHOICES,
        'pre_student': int(pre) if pre.isdigit() else None, 'post': request.POST if request.method == 'POST' else {},
        'post_students': request.POST.getlist('students') if request.method == 'POST' else [],
        'today': timezone.localdate().isoformat(),
    }))


@teacher_login_required
def teacher_detail(request, pk):
    teacher = request.user.teacher_profile
    hw = get_object_or_404(Homework.objects.select_related('student'), pk=pk, teacher=teacher)
    latest = hw.latest()
    if request.method == 'POST':
        if not latest or latest.status != 'submitted':
            messages.error(request, 'مفيش تسليم مستني تصحيح.')
        else:
            try:
                services.review(latest, status=request.POST.get('status'), stars=request.POST.get('stars'),
                                feedback=request.POST.get('feedback'), feedback_audio=request.FILES.get('feedback_audio'),
                                teacher=teacher)
            except services.Refused as e:
                messages.error(request, str(e))
            else:
                messages.success(request, 'تم إرسال التصحيح للطالب ✓')
                nxt = (Submission.objects.filter(homework__teacher=teacher, status='submitted')
                       .order_by('submitted_at').values_list('homework_id', flat=True).first())
                if nxt and request.POST.get('next') == '1':
                    return redirect('learning_teacher_detail', nxt)
                return redirect('learning_teacher_detail', hw.pk)
    return render(request, 'learning/teacher_detail.html', _player_ctx({
        'teacher': teacher, 'hw': hw, 'latest': latest, 'subs': hw.submissions.all(),
        'verses': hw.verses(), 'role': 'teacher',
    }))


@teacher_login_required
@require_POST
def teacher_delete(request, pk):
    hw = get_object_or_404(Homework, pk=pk, teacher=request.user.teacher_profile)
    if hw.submissions.exists():
        messages.error(request, 'مينفعش تمسحي واجب الطالب سلّمه (الإدارة بتحتفظ بيه).')
        return redirect('learning_teacher_detail', pk)
    hw.delete()
    messages.success(request, 'تم مسح الواجب.')
    return redirect('learning_teacher_list')


# =========================================================
# الطالب
# =========================================================
@student_login_required
def student_list(request):
    student = request.user.core_student
    hws = list(Homework.objects.filter(student=student).select_related('teacher').prefetch_related('submissions')[:200])
    todo = [h for h in hws if h.status() in ('new', 'redo')]
    waiting = [h for h in hws if h.status() == 'submitted']
    done = [h for h in hws if h.status() == 'approved']
    return render(request, 'learning/student_list.html', {
        'student': student, 'todo': todo, 'waiting': waiting, 'done': done, 'st': services.stats(student)})


@student_login_required
def student_homework(request, pk):
    student = request.user.core_student
    hw = get_object_or_404(Homework.objects.select_related('teacher'), pk=pk, student=student)
    if request.method == 'POST':
        try:
            services.submit(hw, audio=request.FILES.get('audio'), note=request.POST.get('note'), user=request.user)
        except services.Refused as e:
            if request.headers.get('x-requested-with') == 'fetch':
                return JsonResponse({'ok': False, 'error': str(e)}, status=400)
            messages.error(request, str(e))
        else:
            if request.headers.get('x-requested-with') == 'fetch':
                return JsonResponse({'ok': True, 'points': services.POINTS_SUBMIT})
            messages.success(request, 'برافو! الواجب وصل لمعلمتك 🎉')
        return redirect('learning_student_homework', hw.pk)
    if not hw.seen_at:
        Homework.objects.filter(pk=hw.pk).update(seen_at=timezone.now())
    hw.submissions.filter(reviewed_at__isnull=False, feedback_seen=False).update(feedback_seen=True)
    latest = hw.latest()
    return render(request, 'learning/student_homework.html', _player_ctx({
        'student': student, 'hw': hw, 'latest': latest, 'subs': hw.submissions.all(),
        'verses': hw.verses(), 'can_submit': hw.status() in ('new', 'redo'), 'role': 'student',
        'celebrate': bool(latest and latest.status == 'approved' and latest.reviewed_at and
                          (timezone.now() - latest.reviewed_at).days < 2),
    }))


@student_login_required
def student_listen(request):
    s = request.GET.get('s', '')
    return render(request, 'learning/student_listen.html', _player_ctx({
        'student': request.user.core_student, 'start_surah': int(s) if s.isdigit() and 1 <= int(s) <= 114 else None}))


@student_login_required
def student_games(request):
    student = request.user.core_student
    # الألعاب بتستخدم السور اللي الطالب بيحفظها (من واجباته) + جزء عم
    mine = list(Homework.objects.filter(student=student, surah__isnull=False)
                .values_list('surah', flat=True).distinct()[:30])
    pool = sorted(set(mine) | set(range(78, 115)) | {1})
    idx = quran.index()
    cfg = {'pool': pool, 'all_short': list(range(93, 115)), 'score_url': reverse('learning_api_score'),
           'reciter': quran.DEFAULT_RECITER}
    return render(request, 'learning/student_games.html', {
        'student': student, 'pool': [(n, idx[n - 1]['name']) for n in pool], 'mine': mine,
        'st': services.stats(student), 'cfg': cfg, 'reciters': quran.RECITERS})


@student_login_required
def student_achievements(request):
    student = request.user.core_student
    recent = StudentActivity.objects.filter(student=student).exclude(points=0)[:25]
    return render(request, 'learning/student_achievements.html', {
        'student': student, 'st': services.stats(student), 'recent': recent, 'levels': services.LEVELS})


@student_login_required
@require_POST
def api_score(request):
    student = request.user.core_student
    try:
        data = json.loads(request.body or '{}')
    except ValueError:
        data = {}
    kind = 'listen' if data.get('kind') == 'listen' else 'game'
    try:
        pts = int(data.get('points', 0))
    except (TypeError, ValueError):
        pts = 0
    added = services.award(student, kind, str(data.get('detail', ''))[:60], pts)
    return JsonResponse({'ok': True, 'added': added, 'total': StudentActivity.total_points(student)})


# =========================================================
# ملفات الصوت (مش public - بنتأكد من الصلاحية)
# =========================================================
def _can_view(user, hw):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_staff:
        return True
    if hasattr(user, 'core_student') and user.core_student.pk == hw.student_id:
        return True
    if hasattr(user, 'teacher_profile') and user.teacher_profile.pk == hw.teacher_id:
        return True
    if hasattr(user, 'supervisor_profile') and hw.teacher.supervisor_id == user.supervisor_profile.pk:
        return True
    return False


def audio(request, kind, pk):
    if kind == 'task':
        hw = get_object_or_404(Homework.objects.select_related('teacher'), pk=pk)
        f, mime = hw.teacher_audio, ''
    elif kind in ('sub', 'fb'):
        sub = get_object_or_404(Submission.objects.select_related('homework__teacher'), pk=pk)
        hw = sub.homework
        f, mime = (sub.audio, sub.audio_mime) if kind == 'sub' else (sub.feedback_audio, '')
    else:
        raise Http404
    if not f or not _can_view(request.user, hw):
        raise Http404
    try:
        fh = f.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404
    import mimetypes
    mime = mime or mimetypes.guess_type(f.name)[0] or 'audio/webm'
    resp = FileResponse(fh, content_type=mime, filename=os.path.basename(f.name))
    resp['Cache-Control'] = 'private, max-age=86400'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


# =========================================================
# الإدارة: متابعة كل الواجبات
# =========================================================
@staff_member_required
def admin_list(request):
    qs = Homework.objects.select_related('student', 'teacher').prefetch_related('submissions')
    t = request.GET.get('teacher', '')
    if t.isdigit():
        qs = qs.filter(teacher_id=t)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(student__name__icontains=q) | Q(title__icontains=q))
    rows = list(qs[:400])
    f = request.GET.get('f', '')
    if f:
        rows = [h for h in rows if h.status() == f or (f == 'overdue' and h.is_overdue())]
    agg = Submission.objects.aggregate(waiting=Count('id', filter=Q(status='submitted')),
                                       approved=Count('id', filter=Q(status='approved')))
    return render(request, 'learning/admin_list.html', {
        'rows': rows, 'teachers': Teacher.objects.order_by('name'), 't': t, 'q': q, 'f': f,
        'total': Homework.objects.count(), 'agg': agg,
    })


@staff_member_required
def admin_detail(request, pk):
    hw = get_object_or_404(Homework.objects.select_related('student', 'teacher'), pk=pk)
    return render(request, 'learning/admin_detail.html', _player_ctx({
        'hw': hw, 'latest': hw.latest(), 'subs': hw.submissions.all(), 'verses': hw.verses(), 'role': 'admin'}))


# =========================================================
# صفحات عامة للسيو: المصحف مكتوب + استماع
# =========================================================
def quran_index(request):
    return render(request, 'learning/quran_index.html', _player_ctx({'surahs': quran.index()}))


def quran_surah(request, n):
    if not 1 <= n <= 114:
        raise Http404
    s = quran.surah(n)
    idx = quran.index()
    meta = idx[n - 1]
    rec = request.GET.get('r')
    related = [('/blog/how-to-memorize-quran-plan/', 'كيف تحفظ القرآن وتثبّته: خطة خطوة بخطوة'),
               ('/blog/madd-types-tajweed/', 'أنواع المد في التجويد وعدد حركاته')]
    if n == 1:
        related.insert(0, ('/blog/common-mistakes-surat-al-fatiha/', 'أخطاء شائعة في قراءة سورة الفاتحة وتصحيحها'))
    elif n >= 78:
        related.insert(0, ('/blog/juz-amma-plan-for-kids/', 'جدول حفظ جزء عمّ للأطفال في 6 أشهر'))
    else:
        related.insert(0, ('/blog/quran-revision-system/', 'كيف تراجع حفظك ولا تنساه'))
    return render(request, 'learning/quran_surah.html', _player_ctx({
        'surah': s, 'meta': meta, 'verses': list(enumerate(s['verses'], start=1)),
        'prev': idx[n - 2] if n > 1 else None, 'next': idx[n] if n < 114 else None,
        'reciter_name': quran.RECITER_NAMES.get(rec or '', quran.RECITER_NAMES[quran.DEFAULT_RECITER]),
        'audio_first': quran.audio_url(quran.DEFAULT_RECITER, n, 1), 'related': related,
        'surah_articles': quran.surah_articles(n),
    }))
