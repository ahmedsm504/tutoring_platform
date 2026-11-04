"""الدفعة السابعة عشرة من المقالات (عربي وإنجليزي): المقالات 1551-1610 (عدا 1578 و1579)."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0019_seed_articles_wave16'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
