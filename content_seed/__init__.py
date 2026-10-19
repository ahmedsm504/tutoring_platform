"""محتوى جاهز (مقالات وأسئلة) بيتضاف للموقع تلقائيًا مع migrate.
- كل مقال في ملف .txt جوه articles/ : سطور الهيدر، وبعدين سطر --- وبعدين نص المقال.
- الأسئلة في questions.py
لو مقال أو سؤال بنفس الرابط (slug) موجود أصلًا، مبيتعدلش (عشان تعديلاتك من لوحة التحكم متضيعش)."""
from functools import lru_cache
from pathlib import Path

ARTICLES_DIR = Path(__file__).resolve().parent / 'articles'

BLOG_CATEGORIES = {
    'tajweed': ('أحكام التجويد', '📖', 'شرح أحكام التجويد برواية حفص بالأمثلة من المصحف، للأطفال والكبار.'),
    'hifz': ('طرق الحفظ والمراجعة', '🧠', 'خطط عملية لحفظ القرآن وتثبيته ومراجعته من غير نسيان.'),
    'kids': ('تحفيظ الأطفال', '🌱', 'نصائح لأولياء الأمور لتحفيظ الأطفال القرآن بحب ومن غير إجبار.'),
    'quran-life': ('حياة مع القرآن', '🌙', 'فضل القرآن وأهله، وإزاي نخلي القرآن جزء من يومنا.'),
    'english': ('Learn Quran in English', '🌍', 'Guides in English on Tajweed, Quran memorization and teaching kids, for non-Arabic speakers and Muslim families abroad.'),
}


def load_articles():
    items = []
    for f in sorted(ARTICLES_DIR.glob('*.txt')):
        raw = f.read_text(encoding='utf-8')
        head, body = raw.split('\n---\n', 1)
        meta = {}
        for line in head.strip().splitlines():
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
        meta['slug'] = f.stem.split('_', 1)[1] if '_' in f.stem else f.stem
        meta['body'] = body.strip() + '\n'
        items.append(meta)
    return items


@lru_cache(maxsize=1)
def translation_pairs():
    """{slug: slug_المقابل} في الاتجاهين، من سطر translation_of في المقالات الإنجليزي"""
    pairs = {}
    for a in load_articles():
        other = a.get('translation_of')
        if other:
            pairs[a['slug']] = other
            pairs[other] = a['slug']
    return pairs
