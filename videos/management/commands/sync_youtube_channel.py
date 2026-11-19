"""يضيف أي فيديو جديد على قناة يوتيوب بتاعة المؤسسة لمكتبة الفيديوهات على الموقع (من RSS القناة، من غير مفتاح API).
بيشتغل تلقائي كل 3 ساعات (core/indexnow_scheduler.py)، وتقدر تشغله بإيدك:
  python manage.py sync_youtube_channel
الفيديوهات الموجودة مابتتلمسش (لو عدّلت وصف فيديو من الأدمن بيفضل زي ما هو)."""
import re
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015',
      'media': 'http://search.yahoo.com/mrss/'}

KEYWORDS = [
    ('tajweed', ('تجويد', 'نطق', 'مخارج', 'حرف', 'النون الساكنة', 'مد ', 'إدغام', 'ادغام', 'إخفاء', 'قلقلة', 'tajweed')),
    ('kids', ('أطفال', 'اطفال', 'للأطفال', 'طفل', 'لعب', 'العاب', 'ألعاب', 'kids')),
    ('hifz', ('حفظ', 'تحفيظ', 'مراجعة', 'hifz')),
    ('classes', ('حلقة', 'حلقات', 'الحلقة')),
    ('recitation', ('تلاوة', 'تلاوات', 'قراءة سورة')),
    ('tafsir', ('تفسير', 'تدبر', 'معنى', 'معاني', 'آية')),
]


def clean_title(t):
    t = re.sub(r'#\S+', '', t or '')
    t = t.replace('القرءان', 'القرآن')
    return re.sub(r'\s{2,}', ' ', t).strip(' -|')


def guess_category(text):
    for cat, words in KEYWORDS:
        if any(w in text for w in words):
            return cat
    return 'other'


def default_description(title):
    return (f'فيديو من قناة منصة العجمي التعليمية على يوتيوب: {title}.\n'
            'منصة العجمي بتقدم حصص فردية أونلاين لتحفيظ القرآن الكريم والتجويد للأطفال والكبار، '
            'من أي دولة وبتوقيت بلدك، وأول حلقة تجريبية مجانية.')


class Command(BaseCommand):
    help = 'استيراد الفيديوهات الجديدة من قناة يوتيوب المؤسسة'

    def handle(self, *args, **opts):
        try:
            self._run()
        except Exception as e:  # مايوقعش أي حاجة
            self.stderr.write(f'sync_youtube_channel: تخطّي ({e})')

    def _run(self):
        import requests
        from videos.channel_seed import CHANNEL_ID
        from videos.models import Video
        r = requests.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}', timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        added = 0
        for e in root.findall('a:entry', NS):
            vid = e.findtext('yt:videoId', '', NS)
            if not vid or Video.objects.filter(youtube_id=vid).exists():
                continue
            link = e.find('a:link', NS)
            url = link.get('href') if link is not None else f'https://www.youtube.com/watch?v={vid}'
            raw_title = e.findtext('a:title', '', NS)
            title = clean_title(raw_title) or raw_title
            desc = (e.findtext('media:group/media:description', '', NS) or '').strip()
            desc = re.sub(r'#\S+', '', desc).strip()
            extra = {}
            published = parse_datetime(e.findtext('a:published', '', NS) or '')
            if published:
                extra['published_at'] = published
            Video.objects.create(
                youtube_url=url, title=title[:200], category=guess_category(raw_title + ' ' + desc),
                description=desc if len(desc) >= 60 else default_description(title), **extra,
            )
            added += 1
        self.stdout.write(f'sync_youtube_channel: اتضاف {added} فيديو جديد')
