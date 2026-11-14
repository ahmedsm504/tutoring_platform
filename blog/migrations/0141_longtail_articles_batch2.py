"""الدفعة الثانية: 50 مقالًا جديدًا (36 عربي + 14 إنجليزي) لكلمات بحث طويلة قليلة المنافسة."""
from django.db import migrations


def run(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0140_longtail_articles_batch'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
