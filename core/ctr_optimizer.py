"""محسّن نسبة النقر التلقائي (بيشتغل لوحده يوميًا بعد سحب بيانات Search Console، من غير ما حد يفتح الأدمن).

الفكرة: صفحة بتظهر في جوجل في الترتيب 3 لـ 15 بمرات ظهور كتير، ونسبة النقر عليها أقل بكتير من المتوقع
لترتيبها، وأهم كلمة بيكتبها الناس مش موجودة في عنوانها → نجرب عنوان جديد يبدأ بكلمة البحث نفسها
(بنفس إملاء المقال)، ونحفظ الأرقام قبل التغيير. بعد 28 يوم (نافذة بيانات جوجل كلها بقت بعد التغيير)
نقارن نسبة النقر بالنسبة للمتوقع لترتيبها: لو اتحسنت 10% أو أكتر العنوان يتثبت، لو لأ يرجع زي ما كان
والكلمة دي ماتتجربش تاني لمدة 90 يوم."""
import re
from datetime import timedelta
from urllib.parse import unquote, urlparse

from django.utils import timezone

MIN_IMPRESSIONS = 100
POSITION_RANGE = (2.5, 15)
CTR_RATIO = 0.6          # أقل من 60% من النقر المتوقع لترتيبها = فرصة
TEST_DAYS = 28
RETRY_AFTER_DAYS = 90
MAX_NEW_PER_DAY = 15
IMPROVE_BY = 1.10
BRAND = ('عجمي', 'العجمي', 'agmi', 'alagme', 'alagmi')

_AR_MARKS = re.compile(r'[ً-ٰٟـ]')


def _norm(w):
    w = _AR_MARKS.sub('', (w or '').lower())
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ٱ', 'ا'), ('ة', 'ه'), ('ى', 'ي')):
        w = w.replace(a, b)
    return re.sub(r'[^\w]', '', w)


def _words(s):
    return re.findall(r'[\w؀-ۿ\'’-]+', s or '')


def query_covered(query, title):
    qs = [_norm(w) for w in _words(query) if len(_norm(w)) > 2]
    if not qs:
        return True
    t = {_norm(w) for w in _words(title)}
    tn = _norm(title)
    hit = sum(1 for w in qs if w in t or w in tn)
    return hit >= max(1, round(len(qs) * 0.7))


def _top_query(top_queries):
    first = (top_queries or '').split('، ')[0]
    return re.sub(r'\s*\(\d+\)$', '', first).strip()


def usable_query(query, title):
    q = (query or '').strip()
    words = _words(q)
    if not (2 <= len(words) <= 7) or len(q) > 48:
        return False
    if any(b in _norm(q) for b in BRAND):
        return False
    latin_q = bool(re.search(r'[a-z]', q.lower()))
    latin_t = bool(re.search(r'[A-Za-z]', title)) and not re.search(r'[؀-ۿ]', title)
    return latin_q == latin_t  # كلمة إنجليزي لمقال إنجليزي وعربي لعربي


def spell_like_title(query, title):
    """نكتب كلمة البحث بإملاء المقال (الناس بتكتب «للاطفال» والمقال «للأطفال»)"""
    by_norm = {}
    for w in _words(title):
        by_norm.setdefault(_norm(w), w)
    qw, out, i = _words(query), [], 0
    while i < len(qw):  # «al fil» في البحث = «Al-Fil» في العنوان
        pair = _norm(qw[i] + (qw[i + 1] if i + 1 < len(qw) else '')) if i + 1 < len(qw) else None
        if pair and pair in by_norm:
            out.append(by_norm[pair]); i += 2
        else:
            out.append(by_norm.get(_norm(qw[i]), qw[i])); i += 1
    text = ' '.join(out)
    if re.search(r'[a-z]', text) and not re.search(r'[؀-ۿ]', text):
        small = {'a', 'an', 'the', 'of', 'for', 'and', 'in', 'to', 'on', 'with', 'by', 'or'}
        text = ' '.join(w if (i and w.lower() in small) else (w[:1].upper() + w[1:]) for i, w in enumerate(text.split()))
    return text


def build_title(query, post_title):
    from core.templatetags.content_tags import serp_title
    q = spell_like_title(query, post_title)
    base = serp_title(post_title)
    tail = base.split(':', 1)[1].strip() if ':' in base else base
    if query_covered(q, tail):  # الذيل فيه الكلمة أصلًا: ناخد اللي بعده بس
        tail = re.split(r'[،,]', tail, 1)[-1].strip() if re.search(r'[،,]', tail) else ''
    new = f'{q}: {tail}' if tail and _norm(tail) != _norm(q) else q
    if len(new) > 62:
        new = serp_title(new)
    if len(new) > 62:  # الذيل مايتقصش بشكل نضيف: الكلمة + اسم المؤسسة
        latin = bool(re.search(r'[A-Za-z]', q)) and not re.search(r'[\u0600-\u06FF]', q)
        new = f"{q} | {'Al-Agmi Quran Academy' if latin else 'مؤسسة العجمي'}"
    return new


def _ratio(ctr, position):
    from core.gsc import expected_ctr
    return (ctr or 0) / max(0.1, expected_ctr(position))


def _post_for(url):
    from blog.models import Post
    m = re.match(r'^/blog/([^/]+)/$', unquote(urlparse(url).path))
    return Post.objects.filter(slug=m.group(1), status='published').first() if m else None


def evaluate(now=None, write=print):
    from core.models import GscPagePerformance, SerpTitleTest
    now = now or timezone.now()
    done = 0
    for t in SerpTitleTest.objects.filter(status=SerpTitleTest.ACTIVE, started_at__lte=now - timedelta(days=TEST_DAYS)):
        perf = GscPagePerformance.objects.filter(url__endswith=f'/blog/{t.post.slug}/').first()
        if not perf or perf.impressions < 30:
            continue  # لسه مفيش بيانات كفاية: نستنى
        t.result_ctr, t.result_position, t.decided_at = perf.ctr, perf.position, now
        better = _ratio(perf.ctr, perf.position) >= _ratio(t.base_ctr, t.base_position) * IMPROVE_BY
        if better:
            t.status = SerpTitleTest.KEPT
        else:
            t.status = SerpTitleTest.REVERTED
            t.post.serp_title = ''
            t.post.save(update_fields=['serp_title'])
        t.save()
        done += 1
        write(f"CTR: {'✅ اتثبت' if better else '↩️ اترجع'} {t.new_title} ({t.base_ctr}% ← {perf.ctr}%)")
    return done


def start_tests(now=None, write=print, limit=MAX_NEW_PER_DAY):
    from core.models import GscPagePerformance, SerpTitleTest
    from core.templatetags.content_tags import serp_title
    now = now or timezone.now()
    started = 0
    qs = GscPagePerformance.objects.filter(impressions__gte=MIN_IMPRESSIONS, position__gte=POSITION_RANGE[0],
                                           position__lte=POSITION_RANGE[1]).order_by('-opportunity')
    for perf in qs[:300]:
        if started >= limit:
            break
        if _ratio(perf.ctr, perf.position) >= CTR_RATIO:
            continue  # نسبة النقر كويسة لترتيبها
        post = _post_for(perf.url)
        if not post or post.serp_title:
            continue
        if SerpTitleTest.objects.filter(post=post).filter(
                status=SerpTitleTest.ACTIVE).exists() or SerpTitleTest.objects.filter(
                post=post, started_at__gte=now - timedelta(days=RETRY_AFTER_DAYS)).exists():
            continue
        query = _top_query(perf.top_queries)
        current = serp_title(post.title)
        if not usable_query(query, post.title) or query_covered(query, current):
            continue
        new = build_title(query, post.title)
        if not new or _norm(new) == _norm(current) or not query_covered(query, new):
            continue
        SerpTitleTest.objects.create(post=post, query=query, old_title=current, new_title=new,
                                     base_impressions=perf.impressions, base_ctr=perf.ctr,
                                     base_position=perf.position, started_at=now)
        post.serp_title = new
        post.save(update_fields=['serp_title'])
        started += 1
        write(f'CTR: تجربة جديدة «{new}» بدل «{current}» (كلمة البحث: {query})')
    return started


def run(write=print):
    return evaluate(write=write), start_tests(write=write)
