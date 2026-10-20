"""حقل push_sent_at: الأسئلة المعتمدة قبل كده بتتعلم إنها اتبعت عنها إشعار."""
from django.db import migrations, models
from django.utils import timezone


def mark_existing(apps, schema_editor):
    Q = apps.get_model('qna', 'PublicQuestion')
    Q.objects.filter(status='approved').update(push_sent_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('qna', '0007_seed_questions_wave4')]
    operations = [
        migrations.AddField(
            model_name='publicquestion', name='push_sent_at',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='وقت إرسال الإشعار'),
        ),
        migrations.RunPython(mark_existing, migrations.RunPython.noop),
    ]
