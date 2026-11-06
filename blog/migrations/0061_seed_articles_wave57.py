"""الدفعة السابعة والخمسون: تفسير «فاستبقوا الخيرات» و«ما عندكم ينفد وما عند الله باق» (2263-2264)، وتحديث فهرس التفسير، وتصحيح حكم لام الجلالة في مقال «لم تقولون ما لا تفعلون»."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah', 'tafsir-ayah-lima-taquluna-ma-la-tafalun'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0060_seed_articles_wave56'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
