from django.db import migrations


def run(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0144_qiraat_tajweed_articles_batch5')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
