"""يعمل نسخ WebP خفيفة (640px) من صور أغلفة المقالات عشان كروت المدونة تحمل أسرع.

تشغيل:  python manage.py make_blog_thumbs
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate 640px WebP thumbnails for blog cover images'

    def handle(self, *args, **opts):
        from PIL import Image
        src_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'blog'
        out_dir = src_dir / 'thumbs'
        out_dir.mkdir(exist_ok=True)
        made = 0
        for src in sorted(src_dir.glob('*.jpg')):
            out = out_dir / (src.stem + '.webp')
            if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
                continue
            with Image.open(src) as im:
                im = im.convert('RGB')
                im.thumbnail((640, 640))
                im.save(out, 'WEBP', quality=78, method=6)
            made += 1
        self.stdout.write(self.style.SUCCESS(f'{made} thumbnails generated'))
