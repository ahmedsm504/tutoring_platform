from django.db import migrations


def run(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0147_kids_surah_articles_batch8')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
