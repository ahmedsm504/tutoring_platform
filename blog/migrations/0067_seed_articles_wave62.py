"""Seed wave 62: tafsir 3:164 and 4:125"""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0066_seed_articles_wave61'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
