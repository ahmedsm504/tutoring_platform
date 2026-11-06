"""الدفعة السابعة والأربعون: تفسير دعاء زكريا «رب لا تذرني فردا» و«توبوا إلى الله توبة نصوحا» (2243-2244)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0050_seed_articles_wave46'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
