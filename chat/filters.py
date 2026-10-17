"""فلتر المحتوى: بيكتشف أي محاولة لتبادل وسيلة تواصل خاصة بين المعلمة
والطالب/ولي الأمر (أرقام، روابط، إيميلات، حسابات سوشيال...).

مستويين (بيتطبقوا على الطرفين):
- strong (بيانات تواصل صريحة): الرسالة بتتمنع ومبتوصلش للطرف التاني،
  والإدارة بتشوفها وبيوصلها تنبيه.
- soft (كلمات مريبة زي "كلميني على الخاص"): الرسالة بتوصل عادي بس بتتعلّم
  للإدارة عشان تراجعها.
"""
import re
from dataclasses import dataclass, field

from django.conf import settings

_ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')


def to_ascii_digits(text):
    return (text or '').translate(_ARABIC_DIGITS)

MASK = '[🔒 محجوب]'

_TASHKEEL = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')


def normalize_ar(text):
    t = to_ascii_digits(text or '').lower()
    t = _TASHKEEL.sub('', t)
    t = (t.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
          .replace('ة', 'ه').replace('ى', 'ي'))
    t = re.sub(r'(.)\1{2,}', r'\1', t)  # "واااتس" -> "واتس"
    return t


# أرقام (8 أرقام أو أكتر حتى لو بينهم مسافات/شرط/نقط)
_PHONE_RE = re.compile(r'\+?\d(?:[\s\-\.\(\)_]{0,3}\d){7,}')
_DATE_RE = re.compile(r'^\s*(\d{1,2}[\-\.]\d{1,2}[\-\.]\d{2,4}|\d{4}[\-\.]\d{1,2}[\-\.]\d{1,2})\s*$')

_NUM_WORDS = (
    'صفر|زيرو|واحد|اتنين|اثنين|اثنان|تلاته|ثلاثه|تلات|ثلاث|اربعه|اربع|خمسه|خمس|سته|ست|'
    'سبعه|سبع|تمانيه|ثمانيه|تماني|ثماني|تسعه|تسع|'
    'zero|one|two|three|four|five|six|seven|eight|nine'
)
_NUM_WORDS_RE = re.compile(r'(?:\b(?:%s)\b[\s,،\-]*){6,}' % _NUM_WORDS)

_EMAIL_RE = re.compile(r'[\w.+\-]+\s*(?:@|\(at\)|\[at\])\s*[\w\-]+\s*\.\s*[a-z]{2,}', re.I)
_URL_RE = re.compile(
    r'(?:https?://|www\.)\S+'
    r'|\b[a-z0-9][a-z0-9\-]{1,62}\s?\.\s?(?:com|net|org|me|io|co|info|link|ly|gl|app|site|online|xyz|eg|sa|ae|kw|qa|tv|gg|to|cc|us|uk)\b(?:/\S*)?',
    re.I,
)
_HANDLE_RE = re.compile(r'(?<![\w.])@[a-z0-9_.]{3,30}', re.I)

_SOFT_WORDS = [
    'واتس', 'وتس', 'whats', 'واتساب', 'تليجرام', 'تيليجرام', 'تلجرام', 'telegram', 'انستا', 'insta',
    'فيسبوك', 'فيس بوك', 'facebook', 'ماسنجر', 'messenger', 'سناب', 'snap', 'تيك توك', 'tiktok',
    'رقمي', 'رقمك', 'نمرتي', 'نمرتك', 'رقم تليفون', 'رقم التليفون', 'رقم موبايل', 'رقم الموبايل',
    'رقم الواتس', 'ابعتلي رقم', 'ابعتيلي رقم', 'على الخاص', 'ع الخاص', 'في الخاص', 'برايفت', 'private',
    'ايميل', 'email', 'جيميل', 'gmail', 'اتصلي بيا', 'اتصل بيا', 'كلميني', 'كلمني بره',
    'بره المنصه', 'برا المنصه', 'من غير المنصه', 'بدون المنصه', 'بعيد عن المنصه', 'من ورا المنصه',
    'ارخص', 'سعر خاص', 'درس خصوصي', 'دروس خصوصيه', 'خصوصي معايا', 'اشتراك معايا',
]
_SOFT_RE = re.compile('|'.join(re.escape(normalize_ar(w)) for w in _SOFT_WORDS))


@dataclass
class ScanResult:
    strong: list = field(default_factory=list)   # [(kind, matched_text)]
    soft: list = field(default_factory=list)     # [matched_word]

    @property
    def is_strong(self):
        return bool(self.strong)

    @property
    def is_soft(self):
        return bool(self.soft)

    @property
    def flagged(self):
        return self.is_strong or self.is_soft

    def reasons(self):
        labels = {'phone': 'رقم تليفون', 'email': 'إيميل', 'link': 'رابط', 'handle': 'حساب سوشيال',
                  'number_words': 'رقم مكتوب بالحروف', 'contact_card': 'كارت جهة اتصال', 'location': 'موقع'}
        out = sorted({labels.get(k, k) for k, _ in self.strong})
        if self.soft:
            out.append('كلمات مريبة: ' + '، '.join(sorted(set(self.soft))[:5]))
        return ' | '.join(out)


def _allowed_domains():
    return [d.lower() for d in getattr(settings, 'CHAT_ALLOWED_LINK_DOMAINS', ['alagme.com'])]


def _is_allowed_url(match_text):
    m = match_text.lower().replace(' ', '')
    m = re.sub(r'^https?://', '', m)
    m = re.sub(r'^www\.', '', m)
    host = m.split('/')[0]
    return any(host == d or host.endswith('.' + d) for d in _allowed_domains())


def _strong_spans(text):
    """[(start, end, kind)] على النص بعد تحويل الأرقام العربية بس (نفس الطول)"""
    t = to_ascii_digits(text or '')
    spans = []
    for m in _PHONE_RE.finditer(t):
        if _DATE_RE.match(m.group(0)):
            continue
        if len(re.sub(r'\D', '', m.group(0))) >= 8:
            spans.append((m.start(), m.end(), 'phone'))
    for m in _EMAIL_RE.finditer(t):
        spans.append((m.start(), m.end(), 'email'))
    for m in _URL_RE.finditer(t):
        if not _is_allowed_url(m.group(0)):
            spans.append((m.start(), m.end(), 'link'))
    for m in _HANDLE_RE.finditer(t):
        spans.append((m.start(), m.end(), 'handle'))
    low = t.lower()
    for m in _NUM_WORDS_RE.finditer(normalize_ar(t)):
        # normalize_ar ممكن تغير الطول (تشكيل/تكرار)، فبنحجب الرسالة كلها في الحالة النادرة دي
        spans.append((0, len(low), 'number_words'))
    return spans


def scan(text):
    res = ScanResult()
    t = to_ascii_digits(text or '')
    for s, e, kind in _strong_spans(text):
        res.strong.append((kind, t[s:e]))
    res.soft = _SOFT_RE.findall(normalize_ar(text))
    return res


def mask(text):
    """نسخة النص اللي بتشوفها المعلمة/المشرفة: أي بيانات تواصل بتتشال"""
    if not text:
        return text
    spans = sorted(_strong_spans(text))
    if not spans:
        return text
    t = to_ascii_digits(text)
    out, pos = [], 0
    for s, e, _ in spans:
        if s < pos:
            pos = max(pos, e)
            continue
        out.append(t[pos:s])
        out.append(MASK)
        pos = e
    out.append(t[pos:])
    return ''.join(out)
