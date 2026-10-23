"""مقالات ذات صلة حقيقية + السابق/التالي.

قبل كده كانت «المقالات ذات الصلة» = أحدث 3 مقالات في نفس التصنيف، فكل مقالات التصنيف
(مئات) كانت بتلينك على نفس الـ3 مقالات، والمقالات القديمة مالهاش لينكات داخلية خالص.
دلوقتي بنختار حسب تشابه الكلمات المفتاحية والعنوان، ونكمّل بجيران المقال في نفس التصنيف،
فاللينكات الداخلية بتتوزع على كل المقالات (أحسن للزحف والفهرسة).
"""
import re

from django.core.cache import cache

from .models import Post

_STOP = {
    'في', 'من', 'على', 'إلى', 'الى', 'عن', 'مع', 'ما', 'هل', 'كيف', 'لماذا', 'أو', 'ثم', 'بين',
    'القرآن', 'القران', 'الكريم', 'سورة', 'تفسير', 'شرح', 'دليل', 'طريقة', 'خطة', 'كامل',
    'للأطفال', 'الأطفال', 'للكبار', 'أحكام', 'حكم', 'تطبيق', 'التجويد', 'تجويد', 'قصة', 'قصص', 'حفظ',
    'الله', 'عند', 'الذين', 'إنما', 'أيها', 'التي', 'الذي', 'لكم', 'عليهم', 'وهو', 'منهم', 'فيها',
    'the', 'and', 'for', 'quran', 'how', 'with',
}
_TASHKEEL = re.compile(r'[ً-ْٰـ]')


def _norm(word):
    w = _TASHKEEL.sub('', word.strip().lower())
    w = w.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')
    if w.startswith('وال'):
        w = w[1:]
    if w.startswith('ال') and len(w) > 4:
        w = w[2:]
    return w


def _tokens(title, keywords):
    words = re.findall(r'[\w؀-ۿ]+', f'{title} {keywords or ""}')
    return {n for n in (_norm(w) for w in words) if len(n) >= 3 and n not in _STOP}


def _phrases(keywords):
    return {_norm(k) for k in (keywords or '').split(',') if k.strip()}


def related_posts(post, limit=4):
    key = f'blog:related:v1:{post.pk}'
    ids = cache.get(key)
    if ids is None:
        qs = Post.objects.filter(status='published').exclude(pk=post.pk)
        if post.category_id:
            qs = qs.filter(category_id=post.category_id)
        rows = list(qs.values_list('pk', 'title', 'keywords', 'published_at'))
        mine, my_phr = _tokens(post.title, post.keywords), _phrases(post.keywords)
        scored = []
        for pk, title, kw, pub in rows:
            score = len(mine & _tokens(title, kw)) + 2 * len(my_phr & _phrases(kw))
            if score:
                scored.append((score, pub.timestamp() if pub else 0, pk))
        scored.sort(reverse=True)
        ids = [pk for _, _, pk in scored[:limit]]
        if len(ids) < limit and post.published_at:
            # نكمّل بأقرب المقالات زمنيًا في نفس التصنيف (قبل وبعد) عشان كل مقال ياخد لينك
            before = [r for r in rows if r[3] and r[3] < post.published_at and r[0] not in ids]
            after = [r for r in rows if r[3] and r[3] >= post.published_at and r[0] not in ids]
            before.sort(key=lambda r: r[3], reverse=True)
            after.sort(key=lambda r: r[3])
            for a, b in zip(before + [None] * len(after), after + [None] * len(before)):
                for r in (a, b):
                    if r and len(ids) < limit and r[0] not in ids:
                        ids.append(r[0])
                if len(ids) >= limit:
                    break
        cache.set(key, ids, 6 * 3600)
    by_id = Post.objects.select_related('category').in_bulk(ids)
    return [by_id[i] for i in ids if i in by_id]


def prev_next(post):
    """المقال السابق والتالي في نفس التصنيف (بترتيب النشر)"""
    if not post.published_at:
        return None, None
    qs = Post.objects.filter(status='published').exclude(pk=post.pk)
    if post.category_id:
        qs = qs.filter(category_id=post.category_id)
    prev = qs.filter(published_at__lt=post.published_at).order_by('-published_at').only('slug', 'title').first()
    nxt = qs.filter(published_at__gt=post.published_at).order_by('published_at').only('slug', 'title').first()
    return prev, nxt
