"""بلد الزائر من الـ IP (بقاعدة بيانات geoip2fast المدمجة، من غير أي خدمة خارجية).

طلب صاحب الموقع (27 نوفمبر 2026): كل زائر يدخل على صفحة بلده وأسعارها على طول،
ومحدش يشوف أسعار بلد تانية. فالسيرفر هو اللي بيحدد العملة، ومفيش اختيار عملة في الصفحة.
محركات البحث مستثناة من التحويل عشان كل صفحات الدول تفضل متفهرسة بأسعارها.
"""
import logging
import re
import threading

log = logging.getLogger(__name__)

# بلد -> صفحة البلد عندنا (core/countries.py)
COUNTRY_PAGE = {
    'SA': 'saudi-arabia', 'AE': 'uae', 'KW': 'kuwait', 'QA': 'qatar', 'EG': 'egypt',
    'US': 'usa', 'CA': 'canada', 'GB': 'uk', 'DE': 'germany', 'FR': 'france',
}
_EURO = {'AT', 'BE', 'HR', 'CY', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PT',
         'SK', 'SI', 'ES', 'BG'}
# بلد -> العملة؛ أي بلد مش هنا بيشوف الدولار
COUNTRY_CURRENCY = {'SA': 'SAR', 'AE': 'AED', 'QA': 'QAR', 'KW': 'KWD', 'EG': 'EGP', 'US': 'USD',
                    'CA': 'CAD', 'GB': 'GBP', **{c: 'EUR' for c in _EURO}}
FALLBACK_CURRENCY = 'USD'

_BOT = re.compile(r'bot|crawl|spider|slurp|facebookexternalhit|embedly|preview|lighthouse|pagespeed|'
                  r'mediapartners|adsbot|feedfetcher|validator|bingpreview|whatsapp|telegram', re.I)

_db = None
_lock = threading.Lock()


def _lookup(ip):
    global _db
    if _db is None:
        with _lock:
            if _db is None:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    from geoip2fast import GeoIP2Fast
                    _db = GeoIP2Fast(geoip2fast_data_file='geoip2fast-ipv6.dat.gz')
    code = _db.lookup(ip).country_code
    return code if code and len(code) == 2 and code.isalpha() else ''


def client_ip(request):
    real = request.META.get('HTTP_X_REAL_IP', '').strip()  # Railway بيحطه بـ IP الزائر الحقيقي
    if real:
        return real
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')) or ''


def is_bot(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    return not ua or bool(_BOT.search(ua))


def visitor_country(request):
    """كود البلد بحرفين (EG, SA, ...) أو '' لو مش معروف"""
    if not hasattr(request, '_geo_country'):
        try:
            request._geo_country = _lookup(client_ip(request))
        except Exception:
            log.exception('geo lookup failed')
            request._geo_country = ''
    return request._geo_country


def visitor_currency(request):
    return COUNTRY_CURRENCY.get(visitor_country(request), FALLBACK_CURRENCY)


def visitor_country_slug(request):
    return COUNTRY_PAGE.get(visitor_country(request))


def private(response):
    """الصفحة بتختلف حسب بلد الزائر: متتخزنش في كاش مشترك"""
    response['Cache-Control'] = 'private, max-age=0'
    return response


def price_code(request, page_currency=None):
    """العملة اللي تتعرض: الزائر يشوف عملة بلده بس؛ محركات البحث تشوف عملة الصفحة"""
    if is_bot(request):
        return page_currency
    return visitor_currency(request)
