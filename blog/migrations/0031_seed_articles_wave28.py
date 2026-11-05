"""الدفعة الثامنة والعشرون: أدلة الأجزاء 24-25 (عربي وإنجليزي)، المقالات 2203-2206، وتحديث روابط التنقل في أدلة الأجزاء الإنجليزية."""
from django.db import migrations

REFRESH = [f'juz-{n}-of-the-quran-summary-english' for n in (17, 18, 19, 21, 22, 23)]


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0030_seed_articles_wave27'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
