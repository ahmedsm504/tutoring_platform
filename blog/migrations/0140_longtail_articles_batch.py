"""50 مقالًا جديدًا (عربي + إنجليزي) لكلمات بحث طويلة قليلة المنافسة: أحكام التلاوة والمصحف والحفظ والأطفال."""
from django.db import migrations


def run(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0139_full_tafsir_all_surahs'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
