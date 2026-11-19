from django.db import migrations
from django.utils.dateparse import parse_datetime


def seed(apps, schema_editor):
    """فيديوهات قناة منصة العجمي التعليمية على يوتيوب (مرة واحدة - مابيلمسش فيديو موجود بنفس الـ ID)"""
    from videos.channel_seed import VIDEOS
    from videos.models import parse_youtube_id
    Video = apps.get_model('videos', 'Video')
    for v in VIDEOS:
        yid = parse_youtube_id(v['youtube_url'])
        if Video.objects.filter(youtube_id=yid).exists():
            continue
        Video.objects.create(
            youtube_url=v['youtube_url'], youtube_id=yid, slug=v['slug'], title=v['title'],
            description=v['description'], transcript=v.get('transcript', ''), category=v['category'],
            duration=v.get('duration', ''), is_short='/shorts/' in v['youtube_url'],
            is_featured=v.get('is_featured', False), published_at=parse_datetime(v['published_at']),
        )


class Migration(migrations.Migration):
    dependencies = [('videos', '0001_initial')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
