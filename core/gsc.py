"""ربط تلقائي بـ Google Search Console (من السيرفر، من غير متصفح ولا كمبيوتر حد مفتوح).

بيستخدم نفس مفتاح الـ service account بتاع Firebase (FIREBASE_CREDENTIALS_JSON) أو مفتاح منفصل
في GSC_CREDENTIALS_JSON. شرط واحد: إيميل الـ service account يكون مضاف كمستخدم (Owner) في
Search Console للموقع، و Search Console API مفعّل في مشروع Google Cloud بتاعه.

ملحوظة مهمة: جوجل مابيوفرش API لزرار «طلب الفهرسة» للصفحات العادية. اللي بنعمله تلقائي:
  1) إعادة إرسال السايت ماب يوميًا (sitemaps.submit) → جوجل يعرف الجديد والمتعدّل.
  2) فحص الروابط (URL Inspection API، لحد 2000 رابط/يوم) وتسجيل حالتها ومشاكلها.
  3) تقرير بالإيميل (لو الإيميل متظبط) عن الأرقام والمشاكل اللي من ناحية الموقع.
"""
import logging
import os
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/webmasters']
SITE = os.environ.get('GSC_SITE', 'sc-domain:alagme.com')
DAILY_INSPECTIONS = int(os.environ.get('GSC_DAILY_INSPECTIONS', '300'))

# حالات جوجل اللي معناها إن فيه مشكلة لازم تتصلح في الموقع نفسه (مش مجرد «لسه ماتفهرستش»)
SITE_PROBLEMS = {
    'noindex': 'عليها noindex',
    'robots.txt': 'محظورة في robots.txt',
    'Server error': 'خطأ سيرفر 5xx',
    'Not found': '404 مش موجودة',
    'Redirect error': 'خطأ في التحويل',
    'Soft 404': 'Soft 404',
    'Blocked due to': 'محظورة',
}


class NotConfigured(Exception):
    pass


def credentials():
    from accounts.notifications import ENV_NAMES, _parse_key
    raw = os.environ.get('GSC_CREDENTIALS_JSON') or next(
        (os.environ.get(k) for k in ENV_NAMES if os.environ.get(k)), None)
    if not raw:
        raise NotConfigured('مفيش مفتاح service account (FIREBASE_CREDENTIALS_JSON أو GSC_CREDENTIALS_JSON)')
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_info(_parse_key(raw), scopes=SCOPES)


def session():
    from google.auth.transport.requests import AuthorizedSession
    return AuthorizedSession(credentials())


def service_email():
    try:
        return credentials().service_account_email
    except Exception:
        return ''


def submit_sitemap(s, sitemap_url):
    url = (f'https://www.googleapis.com/webmasters/v3/sites/{quote(SITE, safe="")}'
           f'/sitemaps/{quote(sitemap_url, safe="")}')
    r = s.put(url, timeout=30)
    if r.status_code == 403:
        raise NotConfigured(f'جوجل رفض الصلاحية (403): ضيف {service_email()} كمستخدم Owner في Search Console، '
                            'وفعّل Search Console API في مشروع Google Cloud.')
    r.raise_for_status()
    return True


def inspect(s, url):
    r = s.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
               json={'inspectionUrl': url, 'siteUrl': SITE, 'languageCode': 'en-US'}, timeout=30)
    if r.status_code == 429:
        return None  # خلصت الحصة اليومية
    if r.status_code == 403:
        raise NotConfigured(f'جوجل رفض الصلاحية (403) للـ URL Inspection: ضيف {service_email()} في Search Console.')
    r.raise_for_status()
    return (r.json().get('inspectionResult') or {}).get('indexStatusResult') or {}


def classify(res):
    cov = res.get('coverageState', '') or ''
    for key, label in SITE_PROBLEMS.items():
        if key.lower() in cov.lower():
            return label
    if res.get('robotsTxtState') == 'DISALLOWED':
        return 'محظورة في robots.txt'
    if res.get('indexingState', '').startswith('BLOCKED'):
        return 'عليها noindex'
    if res.get('pageFetchState') not in (None, '', 'SUCCESSFUL', 'PAGE_FETCH_STATE_UNSPECIFIED'):
        return f"مشكلة في جلب الصفحة ({res.get('pageFetchState')})"
    return ''


def sitemap_urls():
    """{url: lastmod} من نفس السايت ماب بتاع الموقع"""
    from config.urls import sitemaps
    base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    found = {}
    for cls in sitemaps.values():
        sm = cls() if isinstance(cls, type) else cls
        for item in sm.items():
            loc = sm.location(item) if hasattr(sm, 'location') else item.get_absolute_url()
            lastmod = None
            if hasattr(sm, 'lastmod'):
                try:
                    lastmod = sm.lastmod(item)
                except Exception:
                    lastmod = None
            found[base + loc] = lastmod
    return found


def pick_urls(found, limit):
    """الأولوية: اللي عمره ما اتفحص (الأحدث أولًا) ← غير المفهرس من أكتر من 3 أيام ← المفهرس من أكتر من 30 يوم"""
    from core.models import GscUrlStatus
    now = timezone.now()
    done = {g.url: g for g in GscUrlStatus.objects.filter(url__in=list(found))}
    epoch = now - timedelta(days=36500)

    def lm(u):
        v = found.get(u)
        return v if hasattr(v, 'tzinfo') and v and timezone.is_aware(v) else epoch

    never = sorted((u for u in found if u not in done), key=lm, reverse=True)
    stale_bad = sorted((u for u, g in done.items() if not g.indexed and g.checked_at < now - timedelta(days=3)),
                       key=lambda u: done[u].checked_at)
    def newer(u, g):
        v = found.get(u)
        try:
            return bool(v) and hasattr(v, 'tzinfo') and timezone.is_aware(v) and v > g.checked_at
        except Exception:
            return False

    changed = [u for u, g in done.items() if g.indexed and newer(u, g)]
    stale_ok = sorted((u for u, g in done.items() if g.indexed and g.checked_at < now - timedelta(days=30)),
                      key=lambda u: done[u].checked_at)
    out = []
    for u in never + changed + stale_bad + stale_ok:
        if u not in out:
            out.append(u)
        if len(out) >= limit:
            break
    return out


# نسبة النقر المتوقعة تقريبًا حسب الترتيب في جوجل (متوسطات عامة منشورة، للمقارنة بس)
EXPECTED_CTR = {1: 28.0, 2: 15.0, 3: 11.0, 4: 8.0, 5: 6.0, 6: 4.5, 7: 3.5, 8: 3.0, 9: 2.5, 10: 2.0}


def expected_ctr(position):
    p = max(1, int(round(position or 99)))
    return EXPECTED_CTR.get(p, 1.0 if p <= 20 else 0.3)


def sync_performance(s, days=28, write=None):
    """يسحب أداء الصفحات والكلمات من Search Analytics ويحسب «النقرات الضايعة» لكل صفحة"""
    from collections import defaultdict
    from datetime import date
    from core.models import GscPagePerformance
    end = date.today() - timedelta(days=2)
    start = end - timedelta(days=days)
    url = f'https://www.googleapis.com/webmasters/v3/sites/{quote(SITE, safe="")}/searchAnalytics/query'
    rows, start_row = [], 0
    while True:
        r = s.post(url, json={'startDate': str(start), 'endDate': str(end), 'dimensions': ['page', 'query'],
                              'rowLimit': 25000, 'startRow': start_row}, timeout=60)
        r.raise_for_status()
        batch = r.json().get('rows', [])
        rows += batch
        if len(batch) < 25000 or start_row > 100000:
            break
        start_row += 25000
    pages = defaultdict(lambda: {'clicks': 0, 'impr': 0, 'pos_w': 0.0, 'queries': []})
    for row in rows:
        page, query = row['keys']
        d = pages[page]
        d['clicks'] += row.get('clicks', 0)
        d['impr'] += row.get('impressions', 0)
        d['pos_w'] += row.get('position', 0) * row.get('impressions', 0)
        d['queries'].append((row.get('impressions', 0), query))
    now = timezone.now()
    for page, d in pages.items():
        pos = d['pos_w'] / d['impr'] if d['impr'] else 0
        ctr = 100.0 * d['clicks'] / d['impr'] if d['impr'] else 0
        missed = max(0.0, d['impr'] * expected_ctr(pos) / 100 - d['clicks'])
        top = '، '.join(f'{q} ({n})' for n, q in sorted(d['queries'], reverse=True)[:6])
        GscPagePerformance.objects.update_or_create(url=page[:500], defaults={
            'clicks': d['clicks'], 'impressions': d['impr'], 'ctr': round(ctr, 2), 'position': round(pos, 1),
            'opportunity': round(missed, 1), 'top_queries': top, 'updated_at': now})
    GscPagePerformance.objects.filter(updated_at__lt=now).delete()
    if write:
        write(f'GSC: اتسحب أداء {len(pages)} صفحة من نتائج البحث')
    return len(pages)


def run(limit=None, submit=True, report=True, stdout=None):
    from core.models import GscUrlStatus
    write = (stdout.write if stdout else logger.info)
    s = session()
    base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    if submit:
        submit_sitemap(s, base + '/sitemap.xml')
        write('GSC: السايت ماب اتبعت لجوجل')
    try:
        sync_performance(s, write=write)
    except Exception as e:  # الأداء معلومة إضافية؛ متوقفش الفحص لو فشل
        write(f'GSC: سحب أداء البحث فشل: {e}')
    else:
        try:
            from core import ctr_optimizer
            ev, st = ctr_optimizer.run(write=write)
            write(f'GSC: محسّن نسبة النقر: اتحسم {ev} تجربة، وبدأ {st} تجربة جديدة')
        except Exception as e:
            write(f'GSC: محسّن نسبة النقر فشل: {e}')
    found = sitemap_urls()
    todo = pick_urls(found, limit or DAILY_INSPECTIONS)
    checked = 0
    new_problems = []
    for url in todo:
        res = inspect(s, url)
        if res is None:
            write('GSC: الحصة اليومية لفحص الروابط خلصت')
            break
        problem = classify(res)
        prev = GscUrlStatus.objects.filter(url=url).values_list('problem', flat=True).first()
        GscUrlStatus.objects.update_or_create(url=url, defaults={
            'verdict': res.get('verdict', '')[:40],
            'coverage_state': (res.get('coverageState') or '')[:200],
            'indexing_state': (res.get('indexingState') or '')[:60],
            'page_fetch_state': (res.get('pageFetchState') or '')[:60],
            'robots_state': (res.get('robotsTxtState') or '')[:40],
            'google_canonical': (res.get('googleCanonical') or '')[:500],
            'last_crawl': parse_datetime(res['lastCrawlTime']) if res.get('lastCrawlTime') else None,
            'problem': problem,
            'checked_at': timezone.now(),
        })
        if problem and problem != prev:
            new_problems.append((url, problem))
        checked += 1
    write(f'GSC: اتفحص {checked} رابط')
    if report:
        send_report(new_problems)
    return checked, new_problems


def summary():
    from django.db.models import Count
    from core.models import GscUrlStatus
    qs = GscUrlStatus.objects.all()
    return {
        'checked': qs.count(),
        'indexed': qs.filter(verdict='PASS').count(),
        'not_indexed': qs.exclude(verdict='PASS').count(),
        'problems': qs.exclude(problem='').count(),
        'by_state': list(qs.exclude(verdict='PASS').values('coverage_state').annotate(n=Count('id')).order_by('-n')[:10]),
    }


def send_report(new_problems):
    """إيميل: فورًا لو ظهرت مشاكل جديدة من ناحية الموقع، وملخص أسبوعي يوم الجمعة"""
    to = [e.strip() for e in os.environ.get('GSC_REPORT_EMAIL', '').split(',') if e.strip()] or \
         [e for _, e in getattr(settings, 'ADMINS', [])]
    if not to or not getattr(settings, 'EMAIL_HOST', ''):
        return False
    weekly = timezone.localdate().weekday() == 4
    if not new_problems and not weekly:
        return False
    from django.core.mail import send_mail
    sm = summary()
    lines = [f"روابط اتفحصت: {sm['checked']}", f"متفهرسة: {sm['indexed']}", f"مش متفهرسة: {sm['not_indexed']}",
             f"مشاكل من ناحية الموقع: {sm['problems']}", '', 'أكتر أسباب عدم الفهرسة:']
    lines += [f"- {r['coverage_state'] or 'غير معروف'}: {r['n']}" for r in sm['by_state']]
    if new_problems:
        lines += ['', 'مشاكل جديدة محتاجة تتصلح:'] + [f'- {p}: {u}' for u, p in new_problems[:50]]
    lines += ['', 'التفاصيل في لوحة الأدمن: /admin/core/gscurlstatus/']
    try:
        send_mail('تقرير فهرسة جوجل - alagme.com', '\n'.join(lines), None, to, fail_silently=True)
        return True
    except Exception:
        logger.exception('GSC report email')
        return False
