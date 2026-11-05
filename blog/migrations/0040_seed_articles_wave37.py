"""الدفعة السابعة والثلاثون: توسيع دليل تحفيظ القرآن للأطفال (عربي وإنجليزي) إلى أكثر من 2000 كلمة."""
from django.db import migrations

REFRESH = ['teaching-quran-to-kids', 'learn-quran-online-for-kids']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0039_seed_articles_wave36'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
