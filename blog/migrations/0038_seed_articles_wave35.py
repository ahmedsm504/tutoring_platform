"""الدفعة الخامسة والثلاثون: توسيع مقالي خطة الحفظ ونظام المراجعة (عربي وإنجليزي) إلى أكثر من 2000 كلمة."""
from django.db import migrations

REFRESH = ['how-to-memorize-quran-plan', 'how-to-memorize-quran-step-by-step',
           'quran-revision-system', 'quran-revision-system-english']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0037_seed_articles_wave34'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
