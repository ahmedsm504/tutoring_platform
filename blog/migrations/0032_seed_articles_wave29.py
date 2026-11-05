"""الدفعة التاسعة والعشرون: أدلة الأجزاء 26-28 (عربي وإنجليزي)، المقالات 2207-2212، وتحديث روابط دليل الجزء 25."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['juz-25-of-the-quran-summary-english'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0031_seed_articles_wave28'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
