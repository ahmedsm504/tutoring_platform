"""نص المصحف (الرسم العثماني - موسوعة القرآن الكريم QuranEnc، رخصة CC BY-SA 4.0)
محفوظ كملفات JSON في static/quran، وبنقراه هنا مرة واحدة ونخليه في الذاكرة."""
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings

QURAN_DIR = Path(settings.BASE_DIR) / 'static' / 'quran'

# المشايخ (أسماء الفولدرات على everyayah.com - كل آية في ملف mp3 لوحدها)
RECITERS = [
    ('Husary_128kbps', 'محمود خليل الحصري'),
    ('Husary_Muallim_128kbps', 'الحصري - المصحف المعلم (للأطفال)'),
    ('Minshawy_Murattal_128kbps', 'محمد صديق المنشاوي'),
    ('Abdul_Basit_Murattal_192kbps', 'عبد الباسط عبد الصمد'),
    ('Alafasy_128kbps', 'مشاري العفاسي'),
    ('Abdurrahmaan_As-Sudais_192kbps', 'عبد الرحمن السديس'),
    ('MaherAlMuaiqly128kbps', 'ماهر المعيقلي'),
    ('Ghamadi_40kbps', 'سعد الغامدي'),
    ('Ali_Jaber_64kbps', 'علي جابر'),
]
DEFAULT_RECITER = 'Husary_128kbps'
RECITER_NAMES = dict(RECITERS)


@lru_cache(maxsize=1)
def index():
    return json.loads((QURAN_DIR / 'index.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=128)
def surah(n):
    n = int(n)
    if not 1 <= n <= 114:
        raise ValueError('رقم سورة غير صحيح')
    return json.loads((QURAN_DIR / f'{n}.json').read_text(encoding='utf-8'))


def surah_name(n):
    return index()[int(n) - 1]['name'] if n else ''


def ayah_count(n):
    return index()[int(n) - 1]['count']


def verses(n, start=1, end=None):
    """[(رقم الآية, النص)]"""
    s = surah(n)
    end = min(end or len(s['verses']), len(s['verses']))
    start = max(1, start or 1)
    return [(i, s['verses'][i - 1]) for i in range(start, end + 1)]


def audio_url(reciter, s, a):
    return f"https://everyayah.com/data/{reciter}/{int(s):03d}{int(a):03d}.mp3"


def range_label(s, a, b):
    if not s:
        return ''
    name = surah_name(s)
    if a and b and (a, b) != (1, ayah_count(s)):
        return f"سورة {name} من الآية {a} إلى {b}" if a != b else f"سورة {name} الآية {a}"
    return f"سورة {name} كاملة"


@lru_cache(maxsize=1)
def _title_patterns():
    import re
    pats = []
    for s in index():
        name = s['name']
        pats.append((len(name), s['id'], name, re.compile(rf'سور[ةه]\s+{re.escape(name)}(?![ء-ي])')))
    pats.sort(reverse=True)  # الأسماء الأطول الأول (عشان «ق» ماتمسكش «القمر» مثلًا)
    return pats


def surah_from_title(title):
    """لو عنوان المقال فيه «سورة X» نرجّع (رقمها، اسمها)، وإلا None."""
    for _, sid, name, rx in _title_patterns():
        if rx.search(title or ''):
            return sid, name
    return None


def surah_articles(n, limit=6):
    """مقالات المدونة الخاصة بالسورة (تفسير، خطة حفظ، تطبيق تجويد...) عشان صفحة السورة تلينك عليها.
    بترجع [(رابط، عنوان)]: المقالات اللي عنوانها عن السورة، وبعدها أقسام الصفحات الشاملة
    (اللي اتجمعت فيها المقالات القصيرة) اللي عنوان القسم فيها عن السورة -> رابط للقسم نفسه."""
    from django.core.cache import cache
    key = f'quran:articles:v2:{n}'
    items = cache.get(key)
    if items is None:
        from django.urls import reverse
        from blog.models import Post
        from core.templatetags.content_tags import toc
        name = index()[n - 1]['name']
        rx = [p for p in _title_patterns() if p[1] == n][0][3]

        def about(text):
            return rx.search(text) and surah_from_title(text) == (n, name)
        posts = list(Post.objects.filter(status='published', content__contains=name).values_list('slug', 'title', 'content'))
        items = [(reverse('blog_detail', args=[s]), t) for s, t, _ in posts if about(t)]
        for s, t, content in posts:
            if len(items) >= limit:
                break
            if about(t):
                continue
            for sid, heading in toc(content):
                if about(heading) and len(items) < limit:
                    items.append((reverse('blog_detail', args=[s]) + f'#{sid}', heading))
        items = items[:limit]
        cache.set(key, items, 6 * 3600)
    return items
