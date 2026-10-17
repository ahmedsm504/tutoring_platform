from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import StudentProfile

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_student_profile(sender, instance, created, **kwargs):
    # حسابات بوابة الطالب الجديدة (core.Student.user) مش محتاجة ملف الطالب القديم
    if created and instance.user_type == 'student' and not getattr(instance, '_skip_student_profile', False):
        # get_or_create لضمان عدم تكرار profile
        StudentProfile.objects.get_or_create(user=instance)
