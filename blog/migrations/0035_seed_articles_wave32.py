"""الدفعة الثانية والثلاثون: توسيع مقالات التجويد الأساسية: أحكام النون الساكنة والتنوين وأحكام الميم الساكنة (عربي وإنجليزي) إلى أكثر من 2000 كلمة."""
from django.db import migrations

REFRESH = ['noon-sakinah-tanween-rules', 'noon-sakinah-tanween-rules-english',
           'meem-sakinah-rules', 'meem-sakinah-rules-english']


def seed(apps, schema_editor):
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0034_seed_articles_wave31'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
