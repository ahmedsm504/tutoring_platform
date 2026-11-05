"""الدفعة السابعة والعشرون: أدلة الأجزاء 21-23 (عربي وإنجليزي)، المقالات 2197-2202، وتحديث روابط دليل الجزء 20."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['juz-20-of-the-quran-summary-english'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0029_seed_articles_wave26'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
