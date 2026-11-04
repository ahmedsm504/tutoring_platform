"""الدفعة التاسعة عشرة من المقالات (عربي وإنجليزي): المقالات 1655-1754 (عدا 1711 و1716)."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0021_seed_articles_wave18'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
