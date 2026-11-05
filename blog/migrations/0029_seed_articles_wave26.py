"""الدفعة السادسة والعشرون: أدلة الأجزاء 17-20 (عربي وإنجليزي)، المقالات 2189-2196، وتحديث روابط دليل الجزء 16."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['juz-16-of-the-quran-summary-english'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0028_seed_articles_wave25'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
