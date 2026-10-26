"""الدفعة الثالثة عشرة من المقالات (عربي): المقالات 951-1150."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0015_seed_articles_wave12'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
