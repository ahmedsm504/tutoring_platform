def learning_counts(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or user.is_staff:
        return {}
    try:
        from . import services
        if hasattr(user, 'teacher_profile'):
            return {'hw_teacher_pending': services.teacher_pending(user.teacher_profile)}
        if hasattr(user, 'core_student'):
            todo, fresh = services.student_counts(user.core_student)
            return {'hw_student_todo': todo + fresh}
    except Exception:
        return {}
    return {}
