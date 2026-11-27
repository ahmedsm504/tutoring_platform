from django.db import migrations


def run(apps, schema_editor):
    """ملخصات الأجزاء 1–10: إضافة خطة قراءة الجزء في يوم رمضاني، وأسئلة تدبر للعائلة، ونشاط للأطفال."""
    from content_seed.seeding import refresh_articles
    refresh_articles(apps, [f'juz-{n}-themes-and-summary' for n in range(1, 11)])


class Migration(migrations.Migration):
    dependencies = [('blog', '0154_serp')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
