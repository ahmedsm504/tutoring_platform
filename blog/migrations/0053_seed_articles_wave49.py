"""الدفعة التاسعة والأربعون: تفسير آيات الجمعة «إذا نودي للصلاة» و«لا تلهكم أموالكم ولا أولادكم» (2247-2248)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0052_seed_articles_wave48'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
