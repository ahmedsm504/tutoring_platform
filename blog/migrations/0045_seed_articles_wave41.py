"""الدفعة الحادية والأربعون: تفسير «شهر رمضان الذي أنزل فيه القرآن» و«يا بني لا تشرك بالله» (2231-2232)، وتحديث فهرس التفسير."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0044_seed_articles_wave40'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
