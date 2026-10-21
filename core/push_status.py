"""صفحة «حالة الإشعارات» في الأدمن: هل Firebase متظبط؟ كام زائر مشترك؟ آخر إشعار اتبعت إمتى؟
ومنها تقدر تبعت إشعار تجريبي لنفسك أو للكل. الرابط: /admin/push-status/"""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


def _last(model, field, **filters):
    obj = model.objects.filter(**filters).exclude(**{f'{field}__isnull': True}).order_by(f'-{field}').first()
    return obj


@staff_member_required
@require_http_methods(['GET', 'POST'])
def push_status(request):
    from accounts.models import FCMToken
    from accounts.notifications import WEB_PROJECT, _send, is_configured, key_project, last_error
    from blog.models import Post
    from qna.models import PublicQuestion
    from core.models import PushLog

    configured = is_configured()
    if request.method == 'POST' and request.POST.get('target') == 'token':
        # اختبار متصفح بعينه من لوحة التشخيص (بيرجع JSON بالنتيجة الحرفية من Firebase)
        token = request.POST.get('token', '').strip()
        if not configured:
            return JsonResponse({'ok': False, 'error': last_error() or 'Firebase مش متظبط'})
        if not token:
            return JsonResponse({'ok': False, 'error': 'مفيش توكن'})
        res = _send([token], '🔔 إشعار تجريبي', 'لو شايف الرسالة دي يبقى الإشعارات شغالة ✅', '/blog/')
        if not res:
            return JsonResponse({'ok': False, 'error': last_error() or 'الإرسال فشل قبل ما يوصل Firebase'})
        r = res[0][1].responses[0]
        if r.success:
            return JsonResponse({'ok': True, 'message_id': r.message_id})
        from accounts.notifications import _err_text
        return JsonResponse({'ok': False, 'error': _err_text(r.exception)})
    if request.method == 'POST':
        target = request.POST.get('target', 'me')
        is_fetch = request.headers.get('X-Requested-With') == 'fetch'
        if not configured:
            if is_fetch:
                return JsonResponse({'ok': False, 'sent': 0, 'total': 0, 'error': last_error() or 'Firebase مش متظبط'})
            messages.error(request, 'Firebase مش متظبط، الإشعار مش هيتبعت. شوف الخطوات تحت.')
            return redirect('push_status')
        if target == 'everyone' and request.user.is_superuser:
            qs = FCMToken.objects.all()
        elif target == 'admins':
            qs = FCMToken.objects.filter(is_admin=True)
        else:
            qs = FCMToken.objects.filter(user=request.user)
        tokens = list(qs.values_list('token', flat=True))
        if not tokens:
            if is_fetch:
                return JsonResponse({'ok': False, 'sent': 0, 'total': 0, 'error': 'مفيش متصفحات مشتركة للفئة دي. استخدم «اختبار المتصفح ده» تحت عشان تشترك.'})
            messages.warning(request, 'مفيش متصفحات مشتركة للفئة دي. افتح الموقع وانت عامل دخول، واضغط «🔔 إشعارات المقالات الجديدة» في الفوتر ووافق على الإذن.')
            return redirect('push_status')
        res = _send(tokens, '🔔 إشعار تجريبي', 'إشعارات موقع العجمي شغالة ✅', '/blog/')
        ok = sum(r.success_count for _, r in (res or []))
        if request.headers.get('X-Requested-With') == 'fetch':
            return JsonResponse({'ok': bool(ok), 'sent': ok, 'total': len(tokens), 'error': '' if ok else (last_error() or 'غير معروف')})
        level = messages.SUCCESS if ok else messages.ERROR
        messages.add_message(request, level, f'Firebase قبل الإرسال لـ {ok} من {len(tokens)} متصفح.' + (
            ' لو مظهرش عندك إشعار، جرّب «اختبار المتصفح ده» تحت.' if ok else f' الخطأ: {last_error() or "غير معروف"}'))
        return redirect('push_status')

    context = {
        'title': 'حالة الإشعارات',
        'configured': configured,
        'error': last_error(),
        'key_project': key_project(),
        'web_project': WEB_PROJECT,
        'total': FCMToken.objects.count(),
        'admins': FCMToken.objects.filter(is_admin=True).count(),
        'mine': FCMToken.objects.filter(user=request.user).count(),
        'last_post': _last(Post, 'push_sent_at'),
        'last_question': _last(PublicQuestion, 'push_sent_at'),
        'pending_posts': Post.objects.filter(status='published', push_sent_at__isnull=True).count(),
        'logs': PushLog.objects.all()[:15],
    }
    return render(request, 'admin/push_status.html', context)
