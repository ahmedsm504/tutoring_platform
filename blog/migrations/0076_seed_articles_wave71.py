"""Seed wave 71: tafsir 17:33 and 17:79"""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0075_seed_articles_wave70'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
