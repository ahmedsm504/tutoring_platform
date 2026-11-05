"""الدفعة الرابعة والعشرون من المقالات (عربي وإنجليزي): أدلة الأجزاء 1-11، المقالات 2157-2178."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0026_seed_articles_wave23'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
