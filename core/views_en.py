"""النسخة الإنجليزية من الصفحات العامة (/en/...) للزوار من برا الدول العربية.
نفس البيانات والفورم بتاع العربي، بس بنصوص إنجليزي وقوالب LTR في templates/en/."""
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils import translation

from . import en_content as en
from .site_content import REVIEWS
from .views import _latest_videos


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')


def _english_posts():
    from blog.models import Post
    return (Post.objects.indexable().filter(category__slug='english')
            .select_related('category').order_by('-is_featured', '-published_at'))


def home(request):
    return render(request, 'en/home.html', {
        'programs': en.PROGRAMS, 'steps': en.STEPS, 'features': en.FEATURES, 'faq': en.FAQ,
        'reviews': REVIEWS,
        'faq_ldjson': _ld(en.faq_schema()),
        'latest_posts': _english_posts()[:3],
        'latest_videos': _latest_videos(),
    })


def pricing(request):
    from core import geo
    from core.countries import EN
    from core.pricing import context as pricing_ctx
    mine = None if geo.is_bot(request) else geo.visitor_country_slug(request)
    if mine in EN:
        return geo.private(redirect(f'/en/online-quran-classes/{mine}/#prices'))
    site = settings.CANONICAL_URL.rstrip('/')
    return geo.private(render(request, 'en/pricing.html', {
        'programs': en.PROGRAMS, 'courses_ldjson': _ld(en.courses_schema(site)),
        **pricing_ctx(geo.price_code(request), en=True),
    }))


def about(request):
    return render(request, 'en/about.html')


def quality_standards(request):
    return render(request, 'en/quality_standards.html')


def privacy(request):
    return render(request, 'en/privacy.html')


def terms(request):
    return render(request, 'en/terms.html')


def editorial_policy(request):
    return render(request, 'en/editorial_policy.html')


def contact(request):
    """نفس فورم حجز الحلقة التجريبية (TrialBookingForm) - رسائل الأخطاء بالإنجليزي"""
    from accounts.forms import TrialBookingForm
    with translation.override('en'):
        if request.method == 'POST':
            form = TrialBookingForm(request.POST)
            if form.is_valid():
                # علامة [EN site] للإدارة إن الحجز جه من النسخة الإنجليزي (الأغلب محتاج معلم بيتكلم إنجليزي)
                from accounts.views import save_booking
                save_booking(request, form, en=True)
                return redirect('en_thank_you')
        else:
            initial = {}
            slug = request.GET.get('program', '')
            prog = next((p for p in en.PROGRAMS if p['slug'] == slug), None)
            if prog:
                initial['notes'] = f"Interested in: {prog['name']}"
            form = TrialBookingForm(initial=initial)
        return render(request, 'en/contact.html', {'form': form})


def thank_you(request):
    return render(request, 'en/thank_you.html')


def quran_index(request):
    from learning import quran
    surahs = []
    for s, (tr, meaning) in zip(quran.index(), en.SURAH_EN):
        surahs.append({**s, 'en': tr, 'meaning': meaning})
    return render(request, 'en/quran_index.html', {'surahs': surahs})


def en_kids_slugs():
    """{رقم السورة: slug مقال الأطفال الإنجليزي}"""
    from blog.models import Post
    from learning import quran
    from core.templatetags.content_tags import translation_of
    kids_ar = quran.kids_articles()
    live = set(Post.objects.indexable().filter(slug__endswith='-for-kids-english').values_list('slug', flat=True))
    out = {}
    for s, (tr, meaning) in zip(quran.index(), en.SURAH_EN):
        art = kids_ar.get(s['id'])
        en_slug = ''
        if art and '#' not in art[0]:
            en_slug = translation_of(art[0].strip('/').split('/')[-1])
        if en_slug not in live:  # مقالات جزء عمّ الإنجليزي مالهاش مقابل عربي مستقل: نطابق بالـ slug
            guess = 'surah-' + tr.lower().replace("'", '').replace(' ', '-') + '-for-kids-english'
            en_slug = guess if guess in live else ''
        if en_slug:
            out[s['id']] = en_slug
    return out


def quran_kids(request):
    """Surahs explained for kids in English: every surah with an English kids article, in mushaf order."""
    from learning import quran
    slugs = en_kids_slugs()
    rows = []
    for s, (tr, meaning) in zip(quran.index(), en.SURAH_EN):
        rows.append({**s, 'en': tr, 'meaning': meaning, 'en_slug': slugs.get(s['id'], '')})
    with_article = [r for r in rows if r['en_slug']]
    return render(request, 'en/quran_kids.html', {'rows': rows, 'with_article': with_article,
                                                  'count': len(with_article), 'ALT_URL': '/quran/for-kids/'})


def blog_list(request):
    posts = Paginator(_english_posts(), 12).get_page(request.GET.get('page'))
    return render(request, 'en/blog_list.html', {'posts': posts})


def countries(request):
    from core.countries import EN, BY_SLUG
    from core.pricing import CURRENCIES, package_price
    rows = [(slug, e, CURRENCIES[BY_SLUG[slug]['currency']]['en'], None) for slug, e in EN.items()]
    return render(request, 'en/countries.html', {'rows': rows, 'ALT_URL': '/online-quran/'})


def country(request, slug):
    from django.http import Http404
    from core.countries import EN, context_en
    if slug not in EN:
        raise Http404
    from core import geo
    from core.countries import BY_SLUG
    mine = None if geo.is_bot(request) else geo.visitor_country_slug(request)
    if mine and mine != slug and mine in EN:
        return geo.private(redirect(f'/en/online-quran-classes/{mine}/'))
    ctx = context_en(slug)
    code = geo.price_code(request, BY_SLUG[slug]['currency'])
    if code != BY_SLUG[slug]['currency']:
        from core.pricing import context as pricing_ctx
        ctx.update(pricing_ctx(code, en=True))
    ctx.update({'programs': en.PROGRAMS, 'others': [(s2, e) for s2, e in EN.items() if s2 != slug],
                'ALT_URL': f'/online-quran/{slug}/'})
    return geo.private(render(request, 'en/country.html', ctx))


def juz_amma_challenge(request):
    """Juz Amma in 30 days, English version of /quran/juz-amma-challenge/."""
    from learning import quran
    from learning.challenge import RAMADAN_START, plan
    slugs = en_kids_slugs()
    names = [tr for tr, _ in en.SURAH_EN]
    days = []
    for d in plan():
        items = []
        for it in d['items']:
            tr = names[it['surah'] - 1]
            items.append({**it, 'name': tr, 'label': f'Surah {tr}' + ('' if it['full'] else f' (verses {it["from"]}–{it["to"]})'),
                          'kids_url': f'/blog/{slugs[it["surah"]]}/' if it['surah'] in slugs and it['from'] == 1 else ''})
        title = ''
        if d['kind'] == 'review':
            title = ('Review: from An-Nas to ' + names[plan()[len(plan()) // 2 - 2]['items'][-1]['surah'] - 1]
                     if d['n'] == len(plan()) - 1 else 'Review the whole of Juz Amma, recite it to the family, and celebrate 🎉')
        days.append({**d, 'items': items, 'title': title})
    return render(request, 'en/juz_amma_challenge.html', {
        'days': days, 'total_ayat': sum(d['ayat'] for d in days), 'ramadan_start': RAMADAN_START,
        'en': True, 'ALT_URL': '/quran/juz-amma-challenge/'})


def quran_certificate(request):
    from learning import quran
    return render(request, 'en/quran_certificate.html', {
        'surahs': [(s['id'], tr) for s, (tr, _) in zip(quran.index(), en.SURAH_EN)],
        'pre_surah': request.GET.get('surah', ''), 'pre_name': (request.GET.get('name') or '')[:40],
        'ALT_URL': '/quran/certificate/'})


def ramadan(request):
    from blog.models import Post
    live = set(Post.objects.indexable().filter(slug__regex=r'^juz-[0-9]+-of-the-quran-summary-english$')
               .values_list('slug', flat=True))
    juz = [(n, f'/blog/juz-{n}-of-the-quran-summary-english/' if f'juz-{n}-of-the-quran-summary-english' in live else '')
           for n in range(1, 31)]
    return render(request, 'en/ramadan.html', {'ALT_URL': '/ramadan/', 'juz': juz})
