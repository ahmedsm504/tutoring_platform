"""Seed wave 81: tafsir 14:27 and 23:60"""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0085_seed_articles_wave80'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
