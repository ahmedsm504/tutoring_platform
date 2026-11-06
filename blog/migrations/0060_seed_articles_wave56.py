"""الدفعة السادسة والخمسون: تفسير «ولا تحسبن الذين قتلوا في سبيل الله أمواتا» و«وهو الذي جعلكم خلائف الأرض» (2261-2262)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0059_seed_articles_wave55'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
