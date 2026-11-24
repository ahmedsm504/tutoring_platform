"""مصدر كل حجز: منين الزائر جه (جوجل، فيسبوك...) وأنهي صفحة/زرار ودّاه للحجز.

static/js/track.js بيحفظ في كوكي أول صفحة دخلها الزائر والموقع اللي جه منه والـ UTM،
وآخر صفحة شافها قبل صفحة الحجز، وفورم الحجز بيبعتهم في حقول مخفية (trk_first, trk_prev).
"""
import json
from urllib.parse import urlparse

SOURCES = [
    ('google_ads', 'إعلانات جوجل'), ('facebook_ads', 'إعلانات فيسبوك/إنستجرام'),
    ('google', 'بحث جوجل'), ('bing', 'بحث بينج'), ('facebook', 'فيسبوك'), ('instagram', 'إنستجرام'),
    ('youtube', 'يوتيوب'), ('tiktok', 'تيك توك'), ('whatsapp', 'واتساب'), ('ai', 'ChatGPT وأدوات الذكاء الاصطناعي'),
    ('other_site', 'موقع تاني'), ('direct', 'مباشر (كتب الرابط أو من غير مصدر)'),
]
SOURCE_LABELS = dict(SOURCES)

_HOSTS = [
    ('google.', 'google'), ('bing.', 'bing'), ('facebook.', 'facebook'), ('fb.', 'facebook'),
    ('instagram.', 'instagram'), ('youtube.', 'youtube'), ('youtu.be', 'youtube'), ('tiktok.', 'tiktok'),
    ('whatsapp.', 'whatsapp'), ('wa.me', 'whatsapp'), ('chatgpt.', 'ai'), ('openai.', 'ai'),
    ('perplexity.', 'ai'), ('gemini.', 'ai'), ('claude.ai', 'ai'), ('copilot.', 'ai'),
]


def _clip(v, n=255):
    return str(v or '')[:n]


def classify(referrer='', utm='', click=''):
    """click: 'gclid' أو 'fbclid' لو موجودين في رابط الدخول. utm بالشكل: source|medium|campaign"""
    u = (utm or '').lower()
    paid = any(k in u for k in ('cpc', 'paid', 'ads', 'ppc'))
    if click == 'gclid' or (paid and 'google' in u):
        return 'google_ads'
    if paid and any(k in u for k in ('facebook', 'instagram', 'fb', 'meta', 'ig')):
        return 'facebook_ads'
    for key, src in _HOSTS:
        if key in u:
            return src
    host = (urlparse(referrer).hostname or '').lower() if referrer else ''
    if host and not host.endswith('alagme.com'):
        for key, src in _HOSTS:
            if key in host:
                return src
        return 'other_site'
    if click == 'fbclid':
        return 'facebook'
    return 'direct'


def apply(booking, data, get=None):
    """يملا حقول المصدر في الحجز من بيانات الفورم (POST) وباراميترات الرابط"""
    get = get or {}
    try:
        first = json.loads(data.get('trk_first') or '{}')
        if not isinstance(first, dict):
            first = {}
    except (ValueError, TypeError):
        first = {}
    referrer, utm, click = _clip(first.get('r')), _clip(first.get('u'), 200), _clip(first.get('c'), 10)
    booking.landing_page = _clip(first.get('l'))
    booking.referrer = referrer
    booking.campaign = utm
    booking.source = classify(referrer, utm, click)
    booking.from_page = _clip(data.get('trk_prev'))
    booking.cta = _clip(data.get('ref') or get.get('ref'), 60)
    prog = data.get('program') or get.get('program')
    if prog:
        from core.site_content import PROGRAMS
        if any(p['slug'] == prog for p in PROGRAMS):
            booking.program = prog
    return booking
