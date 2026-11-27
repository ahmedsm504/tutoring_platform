from django.db import migrations


def run(apps, schema_editor):
    """ملخصات الأجزاء 11–30: خطة قراءة الجزء في يوم رمضاني، وأسئلة تدبر للعائلة، ونشاط للأطفال."""
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, [f'juz-{n}-themes-and-summary' for n in range(11, 31)])


class Migration(migrations.Migration):
    dependencies = [('blog', '0155_juz_ramadan_sections')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
