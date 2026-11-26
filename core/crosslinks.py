"""ربط المدونة بالأسئلة والأجوبة في الاتجاهين (عنقود موضوعي).

صفحات كتير واقفة في المركز 7–11 في جوجل لأن الصفحة لوحدها؛ السؤال القصير مالوش لينك
للشرح الكامل، والمقال مالوش لينك للأسئلة اللي بتتسأل عنه. لما الصفحتين يلينكوا على بعض
بنص واضح، جوجل بيفهم مين الصفحة الأقوى في الموضوع وبيرفعها، وبنقلل تنافس الصفحتين على نفس الكلمة.
"""
import time

from django.core.cache import cache

from blog.related import _phrases, _tokens

MIN_SCORE = 2.5
_GENERIC = {'اقرا', 'اقرء', 'كلمه', 'كلمات', 'المصحف', 'مصحف', 'الصحيح', 'الصحيحه', 'الفرق', 'فرق', 'معني', 'طفلي', 'ابني',
            'children', 'kids', 'child', 'learn', 'learning', 'what', 'which', 'best', 'can', 'does'}


_MEMO = {}
_TTL = 6 * 3600


def _memo(name, build):
    hit = _MEMO.get(name)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    val = build()
    _MEMO[name] = (time.time(), val)
    return val


def _weights():
    return _memo('idf', _build_weights)


def _build_weights():
    from collections import Counter
    df = Counter()
    for row in _post_rows():
        df.update(row[3])
    for row in _question_rows():
        df.update(row[3])
    return {t: (2.0 if n <= 6 else 1.0 if n <= 40 else 0.4) for t, n in df.items()}


def _score(a, b):
    w = _weights()
    return sum(0 if t in _GENERIC else w.get(t, 2.0) for t in a & b)


def _post_rows():
    return _memo('posts', _build_posts)


def _build_posts():
    from blog.models import Post
    return [(pk, slug, title, _tokens(title, kw), _phrases(kw))
            for pk, slug, title, kw in Post.objects.indexable().values_list('pk', 'slug', 'title', 'keywords')]


def _question_rows():
    return _memo('questions', _build_questions)


def _build_questions():
    from qna.models import PublicQuestion
    return [(pk, slug, title, _tokens(title, ''))
            for pk, slug, title in PublicQuestion.objects.filter(status='approved').values_list('pk', 'slug', 'title')]


def _latin(text):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and sum(c.isascii() for c in letters) > len(letters) / 2


def posts_for_question(question, limit=2):
    """أقرب مقالات شرح كامل لسؤال: [(slug, title)]"""
    key = f'xlinks:q2p:v2:{question.pk}'
    out = cache.get(key)
    if out is None:
        mine, lat = _tokens(question.title, ''), _latin(question.title)
        scored = []
        for pk, slug, title, toks, phr in _post_rows():
            if _latin(title) != lat:
                continue
            s = _score(mine, toks)
            if s >= MIN_SCORE:
                scored.append((s, -len(title), slug, title))
        scored.sort(reverse=True)
        out = [(slug, title) for _, _, slug, title in scored[:limit]]
        cache.set(key, out, 6 * 3600)
    return out


def questions_for_post(post, limit=4):
    """أسئلة الزوار القريبة من موضوع المقال: [(slug, title)]"""
    key = f'xlinks:p2q:v2:{post.pk}'
    out = cache.get(key)
    if out is None:
        mine, lat = _tokens(post.title, post.keywords), _latin(post.title)
        scored = []
        for pk, slug, title, toks in _question_rows():
            if _latin(title) != lat:
                continue
            s = _score(mine, toks)
            if s >= MIN_SCORE:
                scored.append((s, -pk, slug, title))
        scored.sort(reverse=True)
        out = [(slug, title) for _, _, slug, title in scored[:limit]]
        cache.set(key, out, 6 * 3600)
    return out
