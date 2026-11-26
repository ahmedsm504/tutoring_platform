"""صفحة «فرص الصفحة الأولى» في الأدمن: /admin/seo-opportunities/
الصفحات اللي جوجل بيظهرها كتير (ترتيب 3 لـ 20) ومحدش بيدوس عليها، مرتبة بالنقرات الضايعة،
مع العنوان والوصف اللي بيظهروا في جوجل دلوقتي وأهم كلمات البحث، وتنبيه لو كلمة البحث الأساسية
مش موجودة في العنوان. وفي آخرها نص جاهز للنسخ عشان يتبعت لكلود يكتب عناوين ووصف أحسن."""
import re
from urllib.parse import urlparse, unquote

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

_AR = re.compile(r'[ً-ٰٟ]')  # تشكيل


def _norm(s):
    s = _AR.sub('', (s or '').lower())
    return s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')


def _top_query(top_queries):
    first = (top_queries or '').split('، ')[0]
    return re.sub(r'\s*\(\d+\)$', '', first).strip()


def query_in_title(query, title):
    """كلمة البحث «موجودة» لو أغلب كلماتها (اللي أطول من حرفين) موجودة في العنوان"""
    words = [w for w in _norm(query).split() if len(w) > 2]
    if not words:
        return True
    t = _norm(title)
    return sum(w in t for w in words) >= max(1, round(len(words) * 0.6))


@staff_member_required
def seo_opportunities(request):
    from blog.models import Post
    from core.models import GscPagePerformance
    from core.templatetags.content_tags import seo_title
    min_impr = int(request.GET.get('min', 50))
    rows = []
    qs = GscPagePerformance.objects.filter(position__gte=2.5, position__lte=20, impressions__gte=min_impr)
    for p in qs.order_by('-opportunity')[:100]:
        path = unquote(urlparse(p.url).path)
        post, title, meta = None, '', ''
        m = re.match(r'^/blog/([^/]+)/$', path)
        if m:
            post = Post.objects.filter(slug=m.group(1)).only('title', 'meta_description', 'excerpt', 'slug').first()
        if post:
            title = seo_title(post.title)
            meta = (post.meta_description or post.excerpt or '')[:160]
        q = _top_query(p.top_queries)
        rows.append({'p': p, 'path': path, 'post': post, 'title': title, 'meta': meta, 'query': q,
                     'missing': bool(post and q and not query_in_title(q, post.title)),
                     'long': len(title) > 62})
    text = '\n\n'.join(
        f"{r['path']} | ظهور {r['p'].impressions} | نقرات {r['p'].clicks} | CTR {r['p'].ctr}% | ترتيب {r['p'].position}\n"
        f"الكلمات: {r['p'].top_queries}\nالعنوان: {r['title'] or '(صفحة مش مقال)'}\nالوصف: {r['meta']}"
        for r in rows[:40])
    return render(request, 'admin/seo_opportunities.html', {
        'rows': rows, 'text': text, 'min': min_impr, 'title': 'فرص الصفحة الأولى في جوجل',
        'updated': qs.order_by('-updated_at').values_list('updated_at', flat=True).first()})
