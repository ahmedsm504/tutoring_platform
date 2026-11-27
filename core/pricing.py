"""أسعار الباقات بعملة الزائر.

القاعدة (من صاحب الموقع، 24 نوفمبر 2026):
- الحصة 40 دقيقة بـ 3 دولار، والحصة 60 دقيقة بـ 5 دولار. باقي العملات بما يعادلها،
  وسعر الباقة كلها متقرّب لأقرب رقم صحيح (من غير كسور).
- مصر: حصة 40 دقيقة: 4 حصص بـ 200 جنيه، 8 بـ 350، 12 بـ 500، والـ 60 دقيقة بالضعف.
- الدورات (نور البيان، الأربعون النووية) من غير سعر على الموقع.

لتغيير السعر: عدّل USD_PER_CLASS أو EGP_PACKAGES أو أسعار الصرف تحت.
"""
import json
from decimal import ROUND_HALF_UP, Decimal

USD_PER_CLASS = {40: Decimal('3'), 60: Decimal('5')}
COUNTS = (4, 8, 12)
EGP_PACKAGES = {4: 200, 8: 350, 12: 500}  # حصة 40 دقيقة، والـ 60 بالضعف
DURATIONS = {}  # كل العملات (ومصر) حصة 40 دقيقة أو ساعة
DEFAULT_DURATIONS = (40, 60)

# العملة مقابل 1 دولار (تقريبي، نوفمبر 2026)
CURRENCIES = {
    'SAR': {'rate': Decimal('3.755'), 'ar': 'ريال سعودي', 'en': 'SAR', 'sym': 'ر.س'},
    'AED': {'rate': Decimal('3.673'), 'ar': 'درهم إماراتي', 'en': 'AED', 'sym': 'د.إ'},
    'QAR': {'rate': Decimal('3.682'), 'ar': 'ريال قطري', 'en': 'QAR', 'sym': 'ر.ق'},
    'KWD': {'rate': Decimal('0.3122'), 'ar': 'دينار كويتي', 'en': 'KWD', 'sym': 'د.ك'},
    'USD': {'rate': Decimal('1'), 'ar': 'دولار أمريكي', 'en': 'USD', 'sym': '$'},
    'CAD': {'rate': Decimal('1.438'), 'ar': 'دولار كندي', 'en': 'CAD', 'sym': 'C$'},
    'GBP': {'rate': Decimal('0.7685'), 'ar': 'جنيه إسترليني', 'en': 'GBP', 'sym': '£'},
    'EUR': {'rate': Decimal('0.919'), 'ar': 'يورو', 'en': 'EUR', 'sym': '€'},
    'EGP': {'rate': None, 'ar': 'جنيه مصري', 'en': 'EGP', 'sym': 'ج.م'},
}
DEFAULT = 'SAR'
DEFAULT_EN = 'USD'

# توقيت المتصفح -> العملة (الجافاسكربت بتختار بيه تلقائيًا، والزائر يقدر يغير)
TZ_CURRENCY = {
    'Asia/Riyadh': 'SAR', 'Asia/Dubai': 'AED', 'Asia/Qatar': 'QAR', 'Asia/Kuwait': 'KWD',
    'Africa/Cairo': 'EGP', 'Europe/London': 'GBP',
    'Europe/Berlin': 'EUR', 'Europe/Paris': 'EUR', 'Europe/Amsterdam': 'EUR', 'Europe/Brussels': 'EUR',
    'Europe/Vienna': 'EUR', 'Europe/Rome': 'EUR', 'Europe/Madrid': 'EUR', 'Europe/Dublin': 'EUR',
    'Europe/Stockholm': 'EUR', 'Europe/Copenhagen': 'EUR', 'Europe/Oslo': 'EUR', 'Europe/Zurich': 'EUR',
    'America/Toronto': 'CAD', 'America/Vancouver': 'CAD', 'America/Edmonton': 'CAD', 'America/Winnipeg': 'CAD',
    'America/Halifax': 'CAD', 'America/Regina': 'CAD', 'America/St_Johns': 'CAD',
}


def durations(code):
    return DURATIONS.get(code, DEFAULT_DURATIONS)


def package_price(code, count, minutes=None):
    """سعر الباقة الشهرية (عدد صحيح). minutes الافتراضي = أقصر حصة في العملة دي"""
    short, long_ = durations(code)
    minutes = minutes or short
    if code == 'EGP':
        return EGP_PACKAGES[count] * (2 if minutes == 60 else 1)
    usd = USD_PER_CLASS[60 if minutes == 60 else 40] * count
    return int((usd * CURRENCIES[code]['rate']).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def table(code):
    """[(count, سعر الحصة القصيرة, سعر الساعة)]"""
    short, long_ = durations(code)
    return [(n, str(package_price(code, n, short)), str(package_price(code, n, long_))) for n in COUNTS]


def all_tables():
    """كل العملات للجافاسكربت: {code: {name_ar, name_en, sym, rows: [[n, p30, p60], ...]}}"""
    return {code: {'ar': c['ar'], 'en': c['en'], 'sym': c['sym'], 'dur': list(durations(code)),
                   'rows': [list(r) for r in table(code)]}
            for code, c in CURRENCIES.items()}


def context(code=None, en=False):
    code = code if code in CURRENCIES else (DEFAULT_EN if en else DEFAULT)
    return {
        'price_currency': code,
        'price_name': CURRENCIES[code]['en' if en else 'ar'],
        'price_rows': table(code),
        'price_durations': durations(code),
    }
