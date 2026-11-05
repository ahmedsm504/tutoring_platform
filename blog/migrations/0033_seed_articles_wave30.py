"""الدفعة الثلاثون: أدلة الجزأين 29 و30 (عربي وإنجليزي)، المقالات 2213-2216، واكتمال سلسلة أدلة الأجزاء الثلاثين، وتحديث روابط دليل الجزء 28."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['juz-28-of-the-quran-summary-english'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0032_seed_articles_wave29'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
