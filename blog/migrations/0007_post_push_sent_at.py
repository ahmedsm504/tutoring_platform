"""حقل push_sent_at: المقالات المنشورة قبل كده بتتعلم إنها اتبعت عنها إشعار، عشان مفيش إشعارات قديمة تطلع."""
from django.db import migrations, models
from django.utils import timezone


def mark_existing(apps, schema_editor):
    Post = apps.get_model('blog', 'Post')
    Post.objects.filter(status='published').update(push_sent_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('blog', '0006_seed_articles_wave4')]
    operations = [
        migrations.AddField(
            model_name='post', name='push_sent_at',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='وقت إرسال الإشعار'),
        ),
        migrations.RunPython(mark_existing, migrations.RunPython.noop),
    ]
