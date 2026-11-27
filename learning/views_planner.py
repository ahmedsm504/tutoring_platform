"""صفحات «حاسبة ختم القرآن» و«خطة حفظ القرآن» بالعربي والإنجليزي (سيو + أداة تفاعلية)."""
import json

from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.urls import reverse

from . import planner as P
from . import planner_content as C

HIFZ_SLUGS = {'1-year': 1, '2-years': 2, '3-years': 3, '4-years': 4, '5-years': 5}
HIFZ_SLUG_OF = {v: k for k, v in HIFZ_SLUGS.items()}
# صفحات جاهزة كانت نسخة طبق الأصل من الصفحة الرئيسية (نفس المدة الافتراضية): بتتحول للرئيسية (301) عشان ميبقاش فيه محتوى مكرر
KHATMA_SAME_AS_HUB = {'30-days'}
HIFZ_SAME_AS_HUB = {'3-years'}


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')


def _crumbs(site, items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': n, 'item': site + u} for i, (n, u) in enumerate(items, 1)]}


def _app_ld(site, url, name, desc, en):
    return {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': name, 'url': site + url,
            'description': desc, 'applicationCategory': 'EducationalApplication', 'operatingSystem': 'Any',
            'inLanguage': 'en' if en else 'ar', 'isAccessibleForFree': True,
            'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
            'publisher': {'@type': 'Organization', 'name': 'Al-Agmi Quran Academy' if en else 'مؤسسة العجمي',
                          'url': site + ('/en/' if en else '/')}}


def _render(request, *, mode, en, slug, content, url, alt_url, crumbs):
    from django.conf import settings
    site = settings.CANONICAL_URL.rstrip('/')
    if mode == 'khatma':
        rows, weekly = P.khatma_rows(content['days'], content['khatmas'])
        presets = [(s, t, reverse(('en_' if en else '') + 'khatma_preset', args=[s])) for s, t in P.khatma_links(en)
                   if s not in KHATMA_SAME_AS_HUB]
        hub = reverse(('en_' if en else '') + 'khatma_planner')
        other_hub = reverse(('en_' if en else '') + 'hifz_planner')
    else:
        rows, weekly = P.hifz_rows(content['years']), False
        names = P.HIFZ_PRESETS_EN if en else P.HIFZ_PRESETS
        presets = [(HIFZ_SLUG_OF[y], (f'Memorize the Quran in {n}' if en else f'حفظ القرآن في {n}'),
                    (reverse(('en_' if en else '') + 'hifz_planner') if HIFZ_SLUG_OF[y] in HIFZ_SAME_AS_HUB
                     else reverse(('en_' if en else '') + 'hifz_preset', args=[HIFZ_SLUG_OF[y]]))) for y, n in names.items()]
        hub = reverse(('en_' if en else '') + 'hifz_planner')
        other_hub = reverse(('en_' if en else '') + 'khatma_planner')
    for r in rows:
        if mode == 'khatma':
            r['from_txt'], r['to_txt'] = P.ref(r['from'], en), P.ref(r['to'], en)
        else:
            for run in r['runs']:
                run['from_txt'], run['to_txt'] = P.ref(run['from'], en), P.ref(run['to'], en)
    from . import planner_unique as U
    unique = None
    if slug:
        unique = U.for_khatma(slug, en) if mode == 'khatma' else U.for_hifz(content.get('years'), en)
    if mode == 'khatma' and cfg_ramadan(slug):
        names = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'] if en else ['الفجر', 'الظهر', 'العصر', 'المغرب', 'العشاء']
        for r in rows:
            a, b = r['from_page'], r['to_page']
            n = b - a + 1
            parts, start = [], a
            for i in range(5):
                end = a + round(n * (i + 1) / 5) - 1
                if end >= start:
                    parts.append(f'{start}–{end}' if end > start else f'{start}')
                start = end + 1
            r['prayers'] = list(zip(names, parts))
    cfg = {'mode': mode, 'lang': 'en' if en else 'ar', 'data': P.js_data(en),
           'days': content.get('days'), 'khatmas': content.get('khatmas'), 'years': content.get('years'),
           'ramadan': bool(slug and str(slug).startswith('ramadan')), 'key': f'{mode}:{slug or "custom"}'}
    lds = [_app_ld(site, url, content['h1'], content['meta'], en), _crumbs(site, crumbs), content['faq_ld']]
    return render(request, 'learning/planner.html', {
        'c': content, 'mode': mode, 'en': en, 'slug': slug, 'rows': rows, 'weekly': weekly,
        'unique': unique,
        'presets': presets, 'hub_url': hub, 'other_hub': other_hub, 'is_hub': not slug,
        'cfg': cfg, 'ldjson': [_ld(x) for x in lds], 'crumbs': crumbs,
        'canonical_path': url, 'LANG': 'en' if en else 'ar', 'ALT_URL': alt_url,
        'og_image': f'images/planner-{mode}-{"en" if en else "ar"}.jpg',
    })


def cfg_ramadan(slug):
    return bool(slug and str(slug).startswith('ramadan'))


def khatma(request, slug=None, en=False):
    if slug and slug not in P.KHATMA_PRESETS:
        raise Http404
    if slug in KHATMA_SAME_AS_HUB:
        return HttpResponsePermanentRedirect(reverse(('en_' if en else '') + 'khatma_planner'))
    content = (C.khatma_en if en else C.khatma_ar)(slug)
    name = 'khatma_preset' if slug else 'khatma_planner'
    args = [slug] if slug else []
    url = reverse(('en_' if en else '') + name, args=args)
    alt = reverse(('' if en else 'en_') + name, args=args)
    if en:
        crumbs = [('Home', '/en/'), ('The Holy Quran', '/en/quran/'), ('Khatam Planner', reverse('en_khatma_planner'))]
    else:
        crumbs = [('الرئيسية', '/'), ('القرآن الكريم', '/quran/'), ('حاسبة ختم القرآن', reverse('khatma_planner'))]
    if slug:
        crumbs.append((content['h1'], url))
    return _render(request, mode='khatma', en=en, slug=slug, content=content, url=url, alt_url=alt, crumbs=crumbs)


def hifz(request, slug=None, en=False):
    if slug and slug not in HIFZ_SLUGS:
        raise Http404
    if slug in HIFZ_SAME_AS_HUB:
        return HttpResponsePermanentRedirect(reverse(('en_' if en else '') + 'hifz_planner'))
    years = HIFZ_SLUGS.get(slug)
    content = (C.hifz_en if en else C.hifz_ar)(years)
    name = 'hifz_preset' if slug else 'hifz_planner'
    args = [slug] if slug else []
    url = reverse(('en_' if en else '') + name, args=args)
    alt = reverse(('' if en else 'en_') + name, args=args)
    if en:
        crumbs = [('Home', '/en/'), ('The Holy Quran', '/en/quran/'), ('Memorization Planner', reverse('en_hifz_planner'))]
    else:
        crumbs = [('الرئيسية', '/'), ('القرآن الكريم', '/quran/'), ('خطة حفظ القرآن', reverse('hifz_planner'))]
    if slug:
        crumbs.append((content['h1'], url))
    return _render(request, mode='hifz', en=en, slug=slug, content=content, url=url, alt_url=alt, crumbs=crumbs)


def khatma_en(request, slug=None):
    return khatma(request, slug, en=True)


def hifz_en(request, slug=None):
    return hifz(request, slug, en=True)


def all_urls():
    """كل روابط الأداة (للسايت ماب)"""
    out = []
    for pre in ('', 'en_'):
        out.append(reverse(pre + 'khatma_planner'))
        out += [reverse(pre + 'khatma_preset', args=[s]) for s in P.KHATMA_PRESETS if s not in KHATMA_SAME_AS_HUB]
        out.append(reverse(pre + 'hifz_planner'))
        out += [reverse(pre + 'hifz_preset', args=[s]) for s in HIFZ_SLUGS if s not in HIFZ_SAME_AS_HUB]
    return out
