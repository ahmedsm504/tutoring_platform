"""Seed wave 114: tafsir 24:21 and 36:65"""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, ['tafsir-ayat-index-by-surah'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0118_seed_articles_wave113'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
