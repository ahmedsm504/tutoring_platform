"""أسعار الباقات بعملة الزائر.

القاعدة (من صاحب الموقع، نوفمبر 2026):
- الحصة (30 دقيقة) بـ 7 ريال سعودي، وباقي العملات بما يعادلها، مقرّبة لرقم سهل.
- مصر: 4 حصص بـ 200 جنيه، 8 بـ 350، 12 بـ 500.
- الحصة 60 دقيقة بضعف سعر الـ 30 دقيقة.
- الدورات (نور البيان، الأربعون النووية) من غير سعر على الموقع.

لتغيير السعر: عدّل SAR_PER_CLASS أو EGP_PACKAGES أو أسعار الصرف تحت.
"""
import json
from decimal import ROUND_HALF_UP, Decimal

SAR_PER_CLASS = Decimal('7')
COUNTS = (4, 8, 12)
EGP_PACKAGES = {4: 200, 8: 350, 12: 500}

# ريال سعودي -> العملة (سعر تقريبي، نوفمبر 2026). step = التقريب لأقرب كام.
CURRENCIES = {
    'SAR': {'rate': Decimal('1'), 'step': Decimal('1'), 'ar': 'ريال سعودي', 'en': 'SAR', 'sym': 'ر.س'},
    'AED': {'rate': Decimal('0.978'), 'step': Decimal('1'), 'ar': 'درهم إماراتي', 'en': 'AED', 'sym': 'د.إ'},
    'QAR': {'rate': Decimal('0.98'), 'step': Decimal('1'), 'ar': 'ريال قطري', 'en': 'QAR', 'sym': 'ر.ق'},
    'KWD': {'rate': Decimal('0.0832'), 'step': Decimal('0.05'), 'ar': 'دينار كويتي', 'en': 'KWD', 'sym': 'د.ك'},
    'USD': {'rate': Decimal('0.2663'), 'step': Decimal('0.5'), 'ar': 'دولار أمريكي', 'en': 'USD', 'sym': '$'},
    'CAD': {'rate': Decimal('0.383'), 'step': Decimal('0.5'), 'ar': 'دولار كندي', 'en': 'CAD', 'sym': 'C$'},
    'GBP': {'rate': Decimal('0.2047'), 'step': Decimal('0.5'), 'ar': 'جنيه إسترليني', 'en': 'GBP', 'sym': '£'},
    'EUR': {'rate': Decimal('0.2447'), 'step': Decimal('0.5'), 'ar': 'يورو', 'en': 'EUR', 'sym': '€'},
    'EGP': {'rate': None, 'step': Decimal('1'), 'ar': 'جنيه مصري', 'en': 'EGP', 'sym': 'ج.م'},
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


def _nice(value, step):
    return (value / step).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * step


def _fmt(d):
    d = d.normalize()
    s = f'{d:f}'
    return s


def package_price(code, count, minutes=30):
    """سعر الباقة الشهرية (Decimal)"""
    c = CURRENCIES[code]
    if code == 'EGP':
        base = Decimal(EGP_PACKAGES[count])
    else:
        base = _nice(SAR_PER_CLASS * count * c['rate'], c['step'])
    return base * (2 if minutes == 60 else 1)


def table(code):
    """[(count, سعر 30 دقيقة, سعر 60 دقيقة)] كنصوص جاهزة"""
    return [(n, _fmt(package_price(code, n, 30)), _fmt(package_price(code, n, 60))) for n in COUNTS]


def all_tables():
    """كل العملات للجافاسكربت: {code: {name_ar, name_en, sym, rows: [[n, p30, p60], ...]}}"""
    return {code: {'ar': c['ar'], 'en': c['en'], 'sym': c['sym'], 'rows': [list(r) for r in table(code)]}
            for code, c in CURRENCIES.items()}


def context(code=None, en=False):
    code = code if code in CURRENCIES else (DEFAULT_EN if en else DEFAULT)
    return {
        'price_currency': code,
        'price_name': CURRENCIES[code]['en' if en else 'ar'],
        'price_rows': table(code),
        'price_currencies': [(k, v['en' if en else 'ar']) for k, v in CURRENCIES.items()],
        'prices_json': json.dumps({'tables': all_tables(), 'tz': TZ_CURRENCY}, ensure_ascii=False),
    }
