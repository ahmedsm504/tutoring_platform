"""الدفعة الخامسة والخمسون: تفسير «الأخلاء يومئذ بعضهم لبعض عدو إلا المتقين» و«اعملوا آل داود شكرا» (2259-2260)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0058_seed_articles_wave54'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
