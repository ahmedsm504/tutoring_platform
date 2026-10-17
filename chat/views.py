import os

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.models import Student, Teacher
from core.views import supervisor_login_required, teacher_login_required

from . import services
from .models import ChatMessage, Conversation


def student_login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'core_student'):
            messages.error(request, 'من فضلك سجّل الدخول بحساب الطالب.')
            return redirect('student_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


# =========================================================
# الصلاحيات: مين يشوف المحادثة وبأي دور
# =========================================================
def role_for(user, conv):
    if not user.is_authenticated or not user.is_active:
        return None
    if user.is_staff:
        return 'admin'
    student = conv.student
    if hasattr(user, 'core_student') and user.core_student.pk == student.pk:
        return 'student'
    teacher = student.teacher
    if teacher and hasattr(user, 'teacher_profile') and user.teacher_profile.pk == teacher.pk:
        return 'teacher'
    if teacher and hasattr(user, 'supervisor_profile') and teacher.supervisor_id == user.supervisor_profile.pk:
        return 'supervisor'
    return None


def _bubbles(request, msgs, role):
    return ''.join(render_to_string('chat/_bubble.html', {'m': m, 'role': role}, request=request) for m in msgs)


def _thread_ctx(request, conv, role):
    msgs = list(services.visible_messages(conv, role).order_by('-id')[:150])[::-1]
    student = conv.student
    other_online = conv.student_online() if role in ('teacher', 'admin', 'supervisor') else conv.teacher_online()
    return {
        'conv': conv, 'student': student, 'teacher': student.teacher, 'role': role,
        'chat_messages': msgs, 'last_id': msgs[-1].id if msgs else 0,
        'can_send': role == 'admin' or (role in ('teacher', 'student') and not conv.is_locked and student.teacher_id),
        'other_online': other_online,
        'student_has_account': bool(student.user_id),
        'back_url': {'teacher': reverse('chat_teacher_inbox'), 'admin': reverse('chat_admin_inbox'),
                     'supervisor': reverse('chat_supervisor_inbox'), 'student': reverse('student_portal_home')}[role],
    }


# =========================================================
# API لحظي (مشترك لكل الأدوار)
# =========================================================
def api_poll(request, conv_id):
    conv = get_object_or_404(Conversation.objects.select_related('student__teacher'), pk=conv_id)
    role = role_for(request.user, conv)
    if not role:
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        after = int(request.GET.get('after', 0))
    except ValueError:
        after = 0
    if role in ('teacher', 'student', 'admin') and not request.GET.get('passive'):
        services.mark_seen(conv, role)
        conv.refresh_from_db()
    new = list(services.visible_messages(conv, role).filter(id__gt=after).order_by('id')[:100])
    # علامات القراءة لرسايلي أنا (✓✓ زرقا)
    mine = {'teacher': ['teacher'], 'student': ['student'], 'admin': ['admin']}.get(role, [])
    read_ids = list(conv.messages.filter(sender_type__in=mine, read_at__isnull=False)
                    .order_by('-id').values_list('id', flat=True)[:60]) if mine else []
    if role == 'student':
        typing, online = conv.teacher_typing(), conv.teacher_online()
    else:
        typing, online = conv.student_typing(), conv.student_online()
    return JsonResponse({
        'html': _bubbles(request, new, role), 'last_id': new[-1].id if new else after,
        'read_ids': read_ids, 'typing': typing, 'online': online, 'locked': conv.is_locked,
    })


@require_POST
def api_send(request, conv_id):
    conv = get_object_or_404(Conversation.objects.select_related('student__teacher'), pk=conv_id)
    role = role_for(request.user, conv)
    ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if role not in ('teacher', 'student', 'admin'):
        return JsonResponse({'error': 'مش مسموح.'}, status=403) if ajax else redirect('home')
    try:
        msg = services.send_message(conv, role=role, user=request.user,
                                    text=request.POST.get('text', ''), upload=request.FILES.get('file'))
    except services.SendRefused as e:
        if ajax:
            return JsonResponse({'error': str(e)}, status=400)
        messages.error(request, str(e))
        return redirect(_thread_url(conv, role))
    warning = ''
    if msg.is_blocked:
        warning = '⛔ الرسالة متبعتتش: ممنوع تبادل أرقام أو روابط أو حسابات تواصل خاصة. الكلام بيكون هنا على المنصة بس، والإدارة اتبلغت.'
    if ajax:
        return JsonResponse({'html': _bubbles(request, [msg], role), 'id': msg.id, 'warning': warning})
    if warning:
        messages.error(request, warning)
    return redirect(_thread_url(conv, role))


@require_POST
def api_typing(request, conv_id):
    conv = get_object_or_404(Conversation.objects.select_related('student__teacher'), pk=conv_id)
    role = role_for(request.user, conv)
    if role in ('teacher', 'student'):
        services.set_typing(conv, role)
    return JsonResponse({'ok': True})


def attachment(request, message_id):
    msg = get_object_or_404(ChatMessage.objects.select_related('conversation__student__teacher'), pk=message_id)
    role = role_for(request.user, msg.conversation)
    if not role or not msg.attachment:
        raise Http404
    if role != 'admin' and msg.attachment_hidden:
        raise Http404
    if msg.is_blocked and role not in ('admin', 'supervisor'):
        raise Http404
    try:
        f = msg.attachment.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404
    inline = msg.attachment_kind in ('image', 'audio', 'video') or msg.attachment_mime == 'application/pdf'
    resp = FileResponse(f, content_type=msg.attachment_mime or 'application/octet-stream',
                        as_attachment=not inline or bool(request.GET.get('download')),
                        filename=msg.attachment_name or os.path.basename(msg.attachment.name))
    resp['Cache-Control'] = 'private, max-age=86400'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


def unread(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0, 'latest': None})
    return JsonResponse(services.unread_summary(request.user))


def _thread_url(conv, role):
    if role == 'student':
        return reverse('student_chat')
    if role == 'teacher':
        return reverse('chat_teacher_thread', args=[conv.student_id])
    return reverse('chat_admin_thread', args=[conv.student_id])


# =========================================================
# المعلمة
# =========================================================
@teacher_login_required
def teacher_inbox(request):
    teacher = request.user.teacher_profile
    students = (Student.objects.filter(teacher=teacher)
                .filter(Q(status='active') | Q(chat__messages__isnull=False)).distinct()
                .select_related('chat', 'user')
                .annotate(last_msg_id=Max('chat__messages__id', filter=~Q(chat__messages__status='blocked', chat__messages__sender_type='student'))))
    last = {m.id: m for m in ChatMessage.objects.filter(id__in=[s.last_msg_id for s in students if s.last_msg_id])}
    rows = [{'student': s, 'conv': getattr(s, 'chat', None), 'last': last.get(s.last_msg_id)} for s in students]
    rows.sort(key=lambda r: (-(r['conv'].teacher_unread if r['conv'] else 0),
                             -(r['last'].id if r['last'] else 0), r['student'].name))
    return render(request, 'chat/teacher_inbox.html', {'teacher': teacher, 'rows': rows})


@teacher_login_required
def teacher_thread(request, student_id):
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student.objects.select_related('teacher', 'user'), pk=student_id, teacher=teacher)
    conv = services.conversation_for(student)
    services.mark_seen(conv, 'teacher')
    ctx = _thread_ctx(request, conv, 'teacher')
    ctx['teacher'] = teacher
    return render(request, 'chat/teacher_thread.html', ctx)


# =========================================================
# الطالب / ولي الأمر
# =========================================================
@student_login_required
def student_chat(request):
    student = request.user.core_student
    conv = services.conversation_for(student)
    services.mark_seen(conv, 'student')
    return render(request, 'chat/student_thread.html', _thread_ctx(request, conv, 'student'))


# =========================================================
# الإدارة: كل المحادثات
# =========================================================
@staff_member_required
def admin_inbox(request):
    qs = Conversation.objects.select_related('student', 'student__teacher').annotate(
        last_msg_id=Max('messages__id'), blocked_count=Count('messages', filter=Q(messages__status='blocked')))
    f = request.GET.get('f', '')
    q = request.GET.get('q', '').strip()
    teacher_id = request.GET.get('teacher', '')
    if f == 'flagged':
        qs = qs.filter(is_flagged=True)
    elif f == 'unread':
        qs = qs.filter(admin_unread__gt=0)
    elif f == 'locked':
        qs = qs.filter(is_locked=True)
    if teacher_id.isdigit():
        qs = qs.filter(student__teacher_id=int(teacher_id))
    if q:
        qs = qs.filter(Q(student__name__icontains=q) | Q(messages__body__icontains=q)).distinct()
    qs = qs.filter(last_msg_id__isnull=False).order_by('-last_message_at', '-id')
    page = Paginator(qs, 40).get_page(request.GET.get('page'))
    last = {m.id: m for m in ChatMessage.objects.filter(id__in=[c.last_msg_id for c in page])}
    totals = Conversation.objects.aggregate(
        all=Count('id', filter=Q(last_message_at__isnull=False)),
        flagged=Count('id', filter=Q(is_flagged=True)),
        unread=Count('id', filter=Q(admin_unread__gt=0)),
        locked=Count('id', filter=Q(is_locked=True)),
    )
    return render(request, 'chat/admin_inbox.html', {
        'rows': [{'conv': c, 'last': last.get(c.last_msg_id)} for c in page], 'page': page,
        'f': f, 'q': q, 'teacher_id': teacher_id, 'teachers': Teacher.objects.all(), 'totals': totals,
        'blocked_attempts': ChatMessage.objects.filter(status='blocked').count(),
        'students_with_accounts': Student.objects.filter(user__isnull=False).count(),
        'students_total': Student.objects.filter(status='active').count(),
    })


@staff_member_required
def admin_thread(request, student_id):
    student = get_object_or_404(Student.objects.select_related('teacher', 'user'), pk=student_id)
    conv = services.conversation_for(student)
    services.mark_seen(conv, 'admin')
    ctx = _thread_ctx(request, conv, 'admin')
    ctx['flagged_messages'] = conv.messages.filter(flagged=True, flag_resolved=False).order_by('-id')[:20]
    return render(request, 'chat/admin_thread.html', ctx)


@staff_member_required
@require_POST
def admin_update(request, student_id):
    conv = get_object_or_404(Conversation, student_id=student_id)
    action = request.POST.get('action')
    if action == 'toggle_lock':
        conv.is_locked = not conv.is_locked
        conv.save(update_fields=['is_locked'])
        messages.warning(request, 'تم قفل المحادثة (الطرفين مش هيقدروا يبعتوا).' if conv.is_locked else 'تم فتح المحادثة.')
    elif action == 'resolve':
        conv.messages.filter(flagged=True).update(flag_resolved=True)
        conv.is_flagged = False
        conv.save(update_fields=['is_flagged'])
        messages.success(request, 'تم تعليم التنبيهات كمُراجَعة.')
    elif action == 'note':
        conv.admin_note = request.POST.get('admin_note', '').strip()
        conv.save(update_fields=['admin_note'])
        messages.success(request, 'تم حفظ الملاحظة.')
    elif action == 'hide_attachment':
        msg = get_object_or_404(ChatMessage, pk=request.POST.get('message_id'), conversation=conv)
        msg.attachment_hidden = not msg.attachment_hidden
        msg.save(update_fields=['attachment_hidden'])
        messages.success(request, 'تم تحديث ظهور المرفق.')
    return redirect('chat_admin_thread', student_id=student_id)


# =========================================================
# المشرفة (متابعة بس)
# =========================================================
@supervisor_login_required
def supervisor_inbox(request):
    supervisor = request.user.supervisor_profile
    convs = (Conversation.objects.filter(student__teacher__supervisor=supervisor, last_message_at__isnull=False)
             .select_related('student', 'student__teacher')
             .annotate(blocked_count=Count('messages', filter=Q(messages__status='blocked'))))
    return render(request, 'chat/supervisor_inbox.html', {'supervisor': supervisor, 'convs': convs})


@supervisor_login_required
def supervisor_thread(request, student_id):
    supervisor = request.user.supervisor_profile
    student = get_object_or_404(Student.objects.select_related('teacher'), pk=student_id, teacher__supervisor=supervisor)
    conv = services.conversation_for(student)
    ctx = _thread_ctx(request, conv, 'supervisor')
    ctx['supervisor'] = supervisor
    return render(request, 'chat/supervisor_thread.html', ctx)
