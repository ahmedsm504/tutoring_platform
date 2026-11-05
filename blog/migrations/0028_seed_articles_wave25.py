"""الدفعة الخامسة والعشرون: أدلة الأجزاء 12-16 (عربي وإنجليزي)، المقالات 2179-2188، وتحديث روابط دليل الجزء 11."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['juz-11-of-the-quran-summary-english'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0027_seed_articles_wave24'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
