"""الدفعة الخمسون: تفسير «قل للمؤمنين يغضوا من أبصارهم» و«اعلموا أنما الحياة الدنيا لعب ولهو» (2249-2250)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0053_seed_articles_wave49'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
