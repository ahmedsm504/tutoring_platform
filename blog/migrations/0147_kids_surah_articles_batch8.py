from django.db import migrations


def run(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0146_kids_surah_articles_batch7')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
