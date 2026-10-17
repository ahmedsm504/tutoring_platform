"""توحيد أرقام الموبايل عشان نقدر نطابق رقم الواتساب اللي جاي من Meta
(دايمًا بالصيغة الدولية من غير + زي 201012345678) مع الأرقام المتسجلة في
النظام (ممكن تكون 01012345678 أو +20 101 234 5678 أو ٠١٠١٢٣٤٥٦٧٨ ...)."""
import re

from django.conf import settings

_ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')


def to_ascii_digits(text):
    return (text or '').translate(_ARABIC_DIGITS)


def normalize_phone(raw):
    """يرجّع الرقم أرقام بس بالصيغة الدولية (من غير +) أو '' لو مش رقم صالح."""
    if not raw:
        return ''
    digits = re.sub(r'\D', '', to_ascii_digits(str(raw)))
    if digits.startswith('00'):
        digits = digits[2:]
    default_cc = str(getattr(settings, 'CHAT_DEFAULT_COUNTRY_CODE', '20'))
    # رقم محلي مصري 01xxxxxxxxx -> 201xxxxxxxxx (أو كود الدولة الافتراضي من الإعدادات)
    if digits.startswith('0') and len(digits) in (10, 11):
        digits = default_cc + digits[1:]
    if len(digits) < 8 or len(digits) > 15:
        return ''
    return digits


def phone_tail(digits, n=9):
    return digits[-n:] if digits else ''


def mask_phone(digits):
    """للعرض للإدارة في القوائم: 2010•••••678"""
    if not digits:
        return ''
    if len(digits) <= 6:
        return '•' * len(digits)
    return f"{digits[:4]}{'•' * (len(digits) - 7)}{digits[-3:]}"
