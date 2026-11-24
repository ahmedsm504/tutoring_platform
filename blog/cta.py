"""دعوة الحجز في المقال على حسب موضوعه: مقال عن الأطفال يكلم ولي الأمر عن طفله، ومقال عن التجويد يعرض
تصحيح التلاوة، ومقال عن الحفظ يعرض خطة حفظ... ومعاها رابط للباقة المناسبة في صفحة الباقات.

الزرار بيبعت ?program=<slug>&ref=article-mid|article-end عشان تقرير مصادر الحجوزات يعرف أنهي مقال جاب الحجز.
"""
import re

TOPICS = {
    'kids': {
        'program': 'nourania',
        'ar': ('عايز طفلك يحفظ القرآن وهو بيحبه؟ في الحلقة التجريبية المعلمة بتحدد مستواه وتبدأ معاه بالتشجيع واللعب، من غير ضغط.',
               'احجز حلقة مجانية لطفلك', 'تفاصيل باقة البداية النورانية'),
        'en': ('Want your child to love learning the Quran? In the free trial class the teacher checks their level and starts with encouragement and games, never pressure.',
               "Book your child's free class", 'See the kids programme'),
    },
    'teens': {
        'program': 'himma',
        'ar': ('ابنك أو بنتك بين 10 و15 سنة؟ باقة الهمة العالية بتمشي معاهم في الحفظ بتدرج ومتابعة أسبوعية تناسب المدرسة.',
               'احجز حلقة تجريبية مجانية', 'تفاصيل باقة الهمة العالية'),
        'en': ('Is your child between 10 and 15? Our teen programme builds memorisation step by step with weekly follow-up that fits around school.',
               'Book a free trial class', 'See the teen programme'),
    },
    'tajweed': {
        'program': 'ghiras',
        'ar': ('عايز تتأكد إن تلاوتك صح؟ معلمة متقنة هتسمعك وتصحح مخارجك وأحكامك في حلقة تجريبية مجانية.',
               'احجز حلقة تصحيح مجانية', 'تفاصيل باقة تصحيح التلاوة'),
        'en': ('Not sure your recitation is right? A qualified teacher will listen to you and correct your letters and tajweed in a free trial class.',
               'Book a free recitation check', 'See the recitation programme'),
    },
    'reading': {
        'program': 'nour-albayan',
        'ar': ('لسه بتتعلم تقرأ الحروف العربية؟ دورة نور البيان بتأسسك في القراءة الصحيحة خطوة بخطوة.',
               'احجز حلقة تجريبية مجانية', 'تفاصيل دورة نور البيان'),
        'en': ('Still learning to read Arabic letters? Our Noor Al-Bayan course builds correct reading step by step.',
               'Book a free trial class', 'See the reading course'),
    },
    'hifz': {
        'program': 'sufaraa',
        'ar': ('عايز تحفظ القرآن وتثبته؟ المعلمة هتعملك خطة حفظ ومراجعة على قد وقتك وتتابعك فيها كل حصة.',
               'احجز حلقة تجريبية مجانية', 'تفاصيل باقة سفراء القرآن'),
        'en': ('Want to memorise the Quran and keep it? Your teacher will build a memorisation and revision plan around your time and follow you every class.',
               'Book a free trial class', 'See the memorisation programme'),
    },
    'general': {
        'program': '',
        'ar': ('عايز تفهم القرآن وتحفظه مع معلمة متقنة أونلاين؟ أول حلقة مجانية، والمواعيد على توقيت بلدك.',
               'احجز حلقة تجريبية مجانية', 'شوف الباقات والأسعار'),
        'en': ('Want to understand and memorise the Quran with a qualified teacher online? Your first class is free, scheduled in your time zone.',
               'Book a free trial class', 'See programmes and prices'),
    },
}

_KW = [
    ('teens', r'مراهق|المراهقين|teen|teenager'),
    ('kids', r'طفل|أطفال|الأطفال|للأطفال|ابني|ابنك|الصغار|kids?\b|child|children|toddler'),
    ('reading', r'نور البيان|القاعدة النورانية|الحروف الهجائية|noor al-?bayan|qaida|arabic letters|learn to read'),
    ('tajweed', r'تجويد|مخارج|إدغام|إخفاء|إظهار|إقلاب|قلقلة|المدود|أحكام المد|الغنة|تفخيم|ترقيق|التلاوة|النطق|لحن|tajweed|tajwid|makharij|pronunciation|recitation|recite|sun and moon|qalqal|ghunnah|madd|idgham|ikhfa|izhar|iqlab|noon sakin|meem sakin|الشمسية|القمرية|النون الساكنة|الميم الساكنة'),
    ('hifz', r'حفظ|الحفظ|مراجعة|المراجعة|تثبيت|نسيان|ختم|memori[sz]|hifz|revision|forget'),
]
_CATEGORY = {'kids': 'kids', 'tajweed': 'tajweed', 'hifz': 'hifz'}


def topic_for(post):
    title = (post.title or '') + ' ' + (post.slug or '')
    for key, rx in _KW:
        if re.search(rx, title, re.I):
            return key
    cat = getattr(getattr(post, 'category', None), 'slug', '')
    return _CATEGORY.get(cat, 'general')


RAMADAN_UNTIL = (2027, 3, 12)  # بعد العيد بيومين بنشيل رابط رمضان من المقالات العامة


def tools_for(post, key):
    """روابط أدوات مجانية مناسبة لموضوع المقال (روابط داخلية بتساعد جوجل يكتشف الصفحات دي ويرتبها)"""
    from datetime import date
    title = f'{post.title} {post.slug}'
    ramadan_season = date.today() <= date(*RAMADAN_UNTIL)
    tools = []
    if re.search(r'رمضان|ramadan', title, re.I) or (ramadan_season and key == 'general'):
        tools.append(('/ramadan/', 'خطة رمضان مع القرآن 🌙'))
    if key in ('kids', 'teens'):
        tools += [('/quran/juz-amma-challenge/', 'تحدي جزء عمّ في 30 يوم'), ('/quran/certificate/', 'شهادة حفظ باسم طفلك 🏅')]
    elif key == 'hifz':
        tools += [('/quran/hifz-tracker/', 'متابعة الحفظ والمراجعة'), ('/quran/juz-amma-challenge/', 'تحدي جزء عمّ في 30 يوم')]
    elif key in ('tajweed', 'reading'):
        tools += [('/level-test/', 'اختبار تحديد المستوى'), ('/quran/', 'المصحف مع الاستماع لكل آية')]
    else:
        tools.append(('/quran/khatma/', 'حاسبة ختم القرآن'))
    return tools[:3]


def for_post(post, en=False):
    key = topic_for(post)
    t = TOPICS[key]
    text, button, program_label = t['en' if en else 'ar']
    return {'topic': key, 'program': t['program'], 'text': text, 'button': button, 'program_label': program_label,
            'tools': [] if en else tools_for(post, key)}
