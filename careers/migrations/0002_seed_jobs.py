from django.db import migrations


def run(apps, schema_editor):
    from careers.seed import seed
    seed(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('careers', '0001_initial')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
