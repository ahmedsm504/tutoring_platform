from django.conf import settings
from django.utils.encoding import iri_to_uri


def seo(request):
    """رابط الـ canonical الصح دايمًا على https://alagme.com مهما كان الدومين اللي الزائر جه منه"""
    site_url = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    # الروابط العربية بتتكتب percent-encoded زي ما هي في sitemap.xml بالظبط (نفس الرابط حرفيًا في الاتنين)
    canonical = site_url + iri_to_uri(request.path)
    page = request.GET.get('page', '')
    if page.isdigit() and int(page) > 1:
        canonical += f'?page={int(page)}'
    wa = getattr(settings, 'WHATSAPP_PUBLIC_NUMBER', '')
    return {
        'SITE_URL': site_url,
        'canonical_url': canonical,
        'SITE_NAME': getattr(settings, 'SITE_NAME', ''),
        'WHATSAPP_PUBLIC_NUMBER': wa,
        'BING_SITE_VERIFICATION': getattr(settings, 'BING_SITE_VERIFICATION', ''),
        'WHATSAPP_LINK': f'https://wa.me/{wa}' if wa else '',
    }


def lang(request):
    """لغة الصفحة: كل اللي تحت /en/ إنجليزي (LTR)، والباقي عربي.
    ALT_URL = رابط نفس الصفحة باللغة التانية (لزرار تبديل اللغة و hreflang). الـ view تقدر تبعت LANG/ALT_URL بنفسها
    (زي المقالات الإنجليزي) وده بيغلب على القيم هنا."""
    from django.urls import NoReverseMatch, reverse
    from core.en_content import PAIRS
    path = request.path or '/'
    is_en = path == '/en' or path.startswith('/en/')
    alt = ''
    m = getattr(request, 'resolver_match', None)
    if m and m.url_name in PAIRS and not m.namespace:
        try:
            alt = reverse(PAIRS[m.url_name])
        except NoReverseMatch:
            alt = ''
    return {'LANG': 'en' if is_en else 'ar', 'ALT_URL': alt}


# شريط رمضان: بيظهر لوحده من أول شعبان لحد العيد ويختفي بعدها (مش محتاج حد يشغله أو يقفله).
# لرمضان الجاي: غيّر التواريخ دي بس.
RAMADAN_START = (2027, 2, 8)   # 1 رمضان 1448 تقريبًا
BANNER_FROM = (2027, 1, 9)     # حوالي 1 شعبان
BANNER_UNTIL = (2027, 3, 12)   # بعد العيد بيومين
_NO_BANNER = ('/admin', '/dashboard', '/teacher', '/student', '/supervisor', '/learning/admin', '/ramadan',
              '/en/ramadan', '/login', '/register', '/accounts')


def season(request):
    from datetime import date
    from django.utils import timezone
    today = timezone.localdate()
    path = request.path or '/'
    if not (date(*BANNER_FROM) <= today <= date(*BANNER_UNTIL)) or path.startswith(_NO_BANNER):
        return {}
    en = path == '/en' or path.startswith('/en/')
    days = (date(*RAMADAN_START) - today).days
    if days > 0:
        text = (f'{days} day{"" if days == 1 else "s"} to Ramadan 🌙 Get your Quran plan ready' if en
                else f'باقي {days} {"أيام" if 3 <= days <= 10 else "يوم"} على رمضان 🌙 جهّز خطة ختمتك وتحدي طفلك')
    else:
        text = ('Ramadan Mubarak 🌙 Your daily Quran plan and kids\' challenge' if en
                else 'رمضان كريم 🌙 خطة الختمة اليومية وتحدي الأطفال')
    return {'RAMADAN_BANNER': {'text': text, 'url': '/en/ramadan/' if en else '/ramadan/'}}
