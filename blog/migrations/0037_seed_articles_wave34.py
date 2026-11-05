"""الدفعة الرابعة والثلاثون: توسيع مقالي مخارج الحروف وخريطة تعلم التجويد (عربي وإنجليزي) إلى أكثر من 2000 كلمة."""
from django.db import migrations

REFRESH = ['makharij-al-huruf', 'makharij-al-huruf-english', 'learn-tajweed-roadmap', 'learn-tajweed-roadmap-english']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0036_seed_articles_wave33'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
