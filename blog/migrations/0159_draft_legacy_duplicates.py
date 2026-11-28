import json
from pathlib import Path

from django.db import migrations
from django.utils import timezone


def run(apps, schema_editor):
    """المقالات اللي في merged_redirects.json تتحول مسودة عشان الرابط القديم يعمل 301 للمقال الأشمل.
    (0158 كانت بتنادي seed_articles بس، والتحويل لمسودة موجود في apply_merges.)"""
    Post = apps.get_model('blog', 'Post')
    path = Path(__file__).resolve().parents[2] / 'content_seed' / 'merged_redirects.json'
    redirects = json.loads(path.read_text(encoding='utf-8'))
    Post.objects.filter(slug__in=list(redirects), status='published').update(status='draft', updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('blog', '0158_legacy_consolidation')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
