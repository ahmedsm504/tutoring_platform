"""الدفعة الخامسة عشرة من المقالات (عربي): المقالات 1351-1478 (عدا 1367 و1453)."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0017_seed_articles_wave14'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
