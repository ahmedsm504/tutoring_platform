"""الدفعة الثالثة والثلاثون: توسيع مقالي المد والقلقلة (عربي وإنجليزي) إلى أكثر من 2000 كلمة."""
from django.db import migrations

REFRESH = ['madd-types-tajweed', 'madd-rules-tajweed-english', 'qalqalah-rules', 'qalqalah-rules-english']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0035_seed_articles_wave32'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
