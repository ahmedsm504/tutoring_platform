from django.core.management.base import BaseCommand
from core.models import Student, Payment


class Command(BaseCommand):
    """
    أمر لمرة واحدة: بيعمل "دفعة" في سجل المدفوعات الجديد لكل طالب عنده قيمة اشتراك
    ومفيش له أي دفعة مسجلة أصلاً، عشان بياناتك القديمة تظهر في صفحة "السنوات"
    والتقارير المالية بدل ما تبدأ من صفر.

    الاستخدام:
        python manage.py seed_payments_from_students
    """
    help = 'ينشئ دفعات تاريخية للطلاب القدامى اللي مفيش لهم سجل مدفوعات بعد'

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for student in Student.objects.all():
            if student.payments.exists():
                skipped_count += 1
                continue

            if not student.subscription_fee or student.subscription_fee <= 0:
                skipped_count += 1
                continue

            payment_date = student.last_payment_date or student.start_date
            Payment.objects.create(
                student=student,
                amount=student.subscription_fee,
                date=payment_date,
                note='دفعة تلقائية (تم إنشاؤها من البيانات القديمة)',
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'تم إنشاء {created_count} دفعة جديدة، وتم تخطي {skipped_count} طالب (كان عنده دفعات بالفعل أو مفيش قيمة اشتراك).'
        ))
