from django.db.models import Count, Q, Sum


def chat_counts(request):
    """عدادات الشات للقوائم (بس جوه البورتالات ولوحة الإدارة - مفيش استعلامات للزوار)"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    try:
        from .models import Conversation
        if user.is_staff:
            agg = Conversation.objects.aggregate(
                unread=Count('id', filter=Q(admin_unread__gt=0)),
                flagged=Count('id', filter=Q(is_flagged=True)),
            )
            return {'chat_admin_unread': agg['unread'] or 0, 'chat_admin_flagged': agg['flagged'] or 0}
        if hasattr(user, 'teacher_profile'):
            n = Conversation.objects.filter(student__teacher=user.teacher_profile).aggregate(n=Sum('teacher_unread'))['n']
            return {'chat_teacher_unread': n or 0}
        if hasattr(user, 'core_student'):
            conv = Conversation.objects.filter(student=user.core_student).only('student_unread').first()
            return {'chat_student_unread': conv.student_unread if conv else 0}
    except Exception:
        return {}
    return {}
