"""الدفعة السادسة والثلاثون: توسيع مقال أخطاء الفاتحة (عربي وإنجليزي) إلى أكثر من 2000 كلمة، وتصحيح معلومة القلقلة في اهدنا."""
from django.db import migrations

REFRESH = ['common-mistakes-surat-al-fatiha', 'surah-al-fatiha-common-mistakes']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0038_seed_articles_wave35'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
