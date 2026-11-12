"""100 مقال تفسير سور كاملة (75 عربي + 25 إنجليزي) + تحديث فهرس تفسير السور."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-surahs-index'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0136_merge_thin_articles'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
