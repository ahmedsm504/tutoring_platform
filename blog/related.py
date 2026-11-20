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
    key = f'blog:related:v2:{post.pk}'
    ids = cache.get(key)
    if ids is None:
        # المقال المفهرس بيرشّح مقالات مفهرسة بس؛ القصير بيرشّح الطويلة الأول عشان القارئ يلاقي محتوى أعمق
        qs = Post.objects.indexable().exclude(pk=post.pk)
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
    qs = Post.objects.indexable().exclude(pk=post.pk)
    if post.category_id:
        qs = qs.filter(category_id=post.category_id)
    prev = qs.filter(published_at__lt=post.published_at).order_by('-published_at').only('slug', 'title').first()
    nxt = qs.filter(published_at__gt=post.published_at).order_by('published_at').only('slug', 'title').first()
    return prev, nxt


def _unindexed_ids():
    """المقالات اللي جوجل لسه مفهرسهاش: حالتها في Search Console مش PASS،
    أو لسه ما اتفحصتش خالص ومنشورة من أقل من 60 يوم. [(pk, category_id, is_english)]"""
    key = 'blog:unindexed:v1'
    rows = cache.get(key)
    if rows is None:
        from datetime import timedelta
        from urllib.parse import unquote, urlsplit
        from django.utils import timezone
        from core.models import GscUrlStatus
        seen, bad = set(), set()
        for url, verdict in GscUrlStatus.objects.filter(url__contains='/blog/').values_list('url', 'verdict'):
            parts = [p for p in unquote(urlsplit(url).path).split('/') if p]
            if len(parts) == 2 and parts[0] == 'blog':
                seen.add(parts[1])
                if verdict != 'PASS':
                    bad.add(parts[1])
        recent = timezone.now() - timedelta(days=60)
        rows = []
        for pk, slug, cat, cslug, pub in Post.objects.indexable().values_list(
                'pk', 'slug', 'category_id', 'category__slug', 'published_at'):
            if slug in bad or (slug not in seen and pub and pub >= recent):
                rows.append((pk, cat, cslug == 'english'))
        cache.set(key, rows, 3 * 3600)
    return rows


def discover_posts(post, exclude=(), limit=5):
    """لينكات داخلية للمقالات اللي جوجل لسه ماوصلهاش، عشان يلاقيها وهو بيزحف على المقالات المفهرسة.
    الاختيار بيتغير كل أسبوع وبيختلف من مقال لمقال، فكل المقالات غير المفهرسة تاخد لينكات."""
    import hashlib
    from django.utils import timezone
    en = bool(post.category_id and getattr(post.category, 'slug', '') == 'english')
    skip = {post.pk, *exclude}
    rows = [r for r in _unindexed_ids() if r[2] == en and r[0] not in skip]
    if not rows:
        return []
    week = timezone.now().isocalendar()[1]

    def rank(r):
        return hashlib.md5(f'{post.pk}:{r[0]}:{week}'.encode()).hexdigest()

    same = sorted((r for r in rows if r[1] == post.category_id), key=rank)
    other = sorted((r for r in rows if r[1] != post.category_id), key=rank)
    picked = same[:3] + other[:limit]
    ids = [r[0] for r in picked][:limit]
    if len(ids) < limit:
        ids += [r[0] for r in same[3:] if r[0] not in ids][:limit - len(ids)]
    by_id = Post.objects.only('slug', 'title').in_bulk(ids)
    return [by_id[i] for i in ids if i in by_id]
