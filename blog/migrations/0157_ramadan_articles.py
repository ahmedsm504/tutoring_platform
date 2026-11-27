from django.db import migrations


def run(apps, schema_editor):
    """مقالات رمضان: القيام بالمحفوظ، والاستعداد في شعبان، والأطفال، والتجويد، والأم المشغولة (عربي وإنجليزي)."""
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0156_juz_ramadan_sections_11_30')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
