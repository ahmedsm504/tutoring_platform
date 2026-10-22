"""الدفعة العاشرة من المقالات (عربي)، مع تصحيح بداية الجزء 21 في مقالين قديمين."""
from django.db import migrations

REFRESH = ['juz-21-memorization-plan', 'history-of-juz-and-hizb-divisions']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles, seed_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0012_seed_articles_wave9'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
