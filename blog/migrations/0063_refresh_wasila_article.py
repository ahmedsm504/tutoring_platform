"""تحديث مقال «وابتغوا إليه الوسيلة» بعد إكماله إلى أكثر من 2000 كلمة."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, ['tafsir-ayah-wabtaghu-ilayhi-al-wasila'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0062_seed_articles_wave58'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
