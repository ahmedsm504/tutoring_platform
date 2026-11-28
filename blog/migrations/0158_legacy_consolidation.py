from django.db import migrations


def run(apps, schema_editor):
    """مقالات قديمة متكررة مع مقالات أشمل: تتحول مسودة و301 للمقال الأشمل (merged_redirects.json)."""
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0157_ramadan_articles')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
