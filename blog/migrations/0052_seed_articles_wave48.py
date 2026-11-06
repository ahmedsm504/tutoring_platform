"""الدفعة الثامنة والأربعون: تفسير «اجتنبوا كثيرا من الظن» و«لم تقولون ما لا تفعلون» (2245-2246)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0051_seed_articles_wave47'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
