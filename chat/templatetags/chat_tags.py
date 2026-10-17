from django import template

register = template.Library()


@register.simple_tag
def sender_label(m, role):
    if m.sender_type == 'admin':
        return '🏢 الإدارة'
    if m.sender_type == role:
        return 'أنت' if role == 'student' else 'أنتِ'
    if m.sender_type == 'teacher':
        return f"👩‍🏫 {m.teacher.name}" if m.teacher_id else '👩‍🏫 المعلمة'
    return f"🎓 {m.conversation.student.name}"


@register.filter
def is_mine(m, role):
    return m.sender_type == role
