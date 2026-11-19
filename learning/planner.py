"""أداة «خطة الختمة» و«خطة حفظ القرآن» (عربي + إنجليزي).

الحسابات كلها على مصحف المدينة (604 صفحة). نفس المنطق موجود في static/js/planner.js للحاسبة التفاعلية؛
هنا بنحسب الجدول الافتراضي لكل صفحة جاهزة (preset) عشان يظهر في HTML لمحركات البحث من غير JavaScript.
"""
import math

from . import quran
from .mushaf import JUZ_FIRST, JUZ_START, PAGE_START, TOTAL_PAGES

MIN_PER_PAGE = 2  # تقدير تقريبي لقراءة صفحة بتأنٍّ للقارئ المتوسط

# ---------------------------------------------------------------- بيانات مساعدة


def juz_of_page(p):
    j = 1
    for i, start in enumerate(JUZ_START, 1):
        if start <= p:
            j = i
    return j


def page_end(p):
    """آخر آية في الصفحة p = اللي قبل أول آية في الصفحة اللي بعدها"""
    if p >= TOTAL_PAGES:
        return (114, 6)
    s, a = PAGE_START[p]  # بداية الصفحة p+1
    if a > 1:
        return (s, a - 1)
    return (s - 1, quran.ayah_count(s - 1))


def surah_label(s, en=False):
    if en:
        from core.en_content import SURAH_EN
        return SURAH_EN[s - 1][0]
    return quran.surah_name(s)


def ref(sa, en=False):
    s, a = sa
    return f'{surah_label(s, en)} {a}' if en else f'{surah_label(s)} {a}'


def js_data(en=False):
    """البيانات اللي الحاسبة التفاعلية محتاجاها (بتتبعت json_script في الصفحة)"""
    return {
        'pages': PAGE_START,
        'juz': JUZ_START,
        'names': [surah_label(i, en) for i in range(1, 115)],
        'counts': [quran.ayah_count(i) for i in range(1, 115)],
        'jf': JUZ_FIRST,
    }


# ---------------------------------------------------------------- خطة الختمة (قراءة)


def prev_ayah(sa):
    s, a = sa
    return (s, a - 1) if a > 1 else (s - 1, quran.ayah_count(s - 1))


def juz_aligned(days, khatmas=1, start_page=1):
    """لو عدد الأيام بيقسم الأجزاء بالظبط (30 يوم = جزء يوميًا، 15 = جزأين…) نمشي على حدود الأجزاء الحقيقية"""
    return start_page == 1 and days <= 30 * khatmas and (30 * khatmas) % days == 0


def _juz_rows(days, khatmas):
    per = 30 * khatmas // days
    rows = []
    for d in range(days):
        ja = (d * per) % 30 + 1
        jb = ((d + 1) * per - 1) % 30 + 1
        p1 = JUZ_START[ja - 1]
        if jb < 30:
            nxt = JUZ_FIRST[jb]  # أول آية في الجزء اللي بعده
            p2 = JUZ_START[jb] if PAGE_START[JUZ_START[jb] - 1] != nxt else JUZ_START[jb] - 1
            to = prev_ayah(nxt)
        else:
            p2, to = TOTAL_PAGES, (114, 6)
        rows.append({'day': d + 1, 'from_page': p1, 'to_page': p2, 'pages': p2 - p1 + 1,
                     'from': JUZ_FIRST[ja - 1], 'to': to, 'juz_from': ja, 'juz_to': jb, 'khatma_done': jb == 30})
    return rows


def khatma_rows(days, khatmas=1, start_page=1):
    """جدول يومي: من صفحة لصفحة. لو الخطة طويلة (> 60 يوم) بنجمّعها أسابيع."""
    if juz_aligned(days, khatmas, start_page):
        return _juz_rows(days, khatmas), False
    total = TOTAL_PAGES * khatmas
    bounds = [round(i * total / days) for i in range(days + 1)]
    rows = []
    for d in range(days):
        a, b = bounds[d], bounds[d + 1]
        if b <= a:
            continue
        p1 = (start_page - 1 + a) % TOTAL_PAGES + 1
        p2 = (start_page - 1 + b - 1) % TOTAL_PAGES + 1
        rows.append({'day': d + 1, 'from_page': p1, 'to_page': p2, 'pages': b - a,
                     'from': PAGE_START[p1 - 1], 'to': page_end(p2),
                     'juz_from': juz_of_page(p1), 'juz_to': juz_of_page(p2),
                     'khatma_done': b % TOTAL_PAGES == 0})
    if days > 60:
        weeks = []
        for i in range(0, len(rows), 7):
            chunk = rows[i:i + 7]
            label = f'{chunk[0]["day"]}–{chunk[-1]["day"]}' if len(chunk) > 1 else str(chunk[0]['day'])
            weeks.append({'day': label, 'week': i // 7 + 1,
                          'from_page': chunk[0]['from_page'], 'to_page': chunk[-1]['to_page'],
                          'pages': sum(c['pages'] for c in chunk), 'from': chunk[0]['from'], 'to': chunk[-1]['to'],
                          'juz_from': chunk[0]['juz_from'], 'juz_to': chunk[-1]['juz_to'],
                          'khatma_done': any(c['khatma_done'] for c in chunk)})
        return weeks, True
    return rows, False


def khatma_stats(days, khatmas=1):
    ppd = TOTAL_PAGES * khatmas / days
    return {
        'days': days, 'khatmas': khatmas,
        'pages_per_day': ppd,
        'pages_per_day_txt': _num(ppd),
        'juz_per_day_txt': _num(30 * khatmas / days),
        'minutes': int(math.ceil(ppd * MIN_PER_PAGE / 5.0) * 5) if ppd * MIN_PER_PAGE > 10 else int(math.ceil(ppd * MIN_PER_PAGE)),
        'per_prayer_txt': _num(ppd / 5),
    }


def _num(x):
    if abs(x - round(x)) < 0.15 and x >= 1:
        return str(int(round(x)))
    return f'{x:.1f}'


# الصفحات الجاهزة (كل واحدة بتستهدف بحث مشهور). slug -> (أيام، عدد الختمات)
KHATMA_PRESETS = {
    'ramadan': (30, 1),
    'ramadan-2-khatmas': (30, 2),
    'ramadan-3-khatmas': (30, 3),
    '3-days': (3, 1),
    '7-days': (7, 1),
    '10-days': (10, 1),
    '15-days': (15, 1),
    '20-days': (20, 1),
    '30-days': (30, 1),
    '40-days': (40, 1),
    '60-days': (60, 1),
    '90-days': (90, 1),
    '1-year': (365, 1),
}

AR_DAYS = {3: '3 أيام', 7: 'أسبوع (7 أيام)', 10: '10 أيام', 15: '15 يوم', 20: '20 يوم', 30: 'شهر (30 يوم)',
           40: '40 يوم', 60: 'شهرين (60 يوم)', 90: '3 شهور (90 يوم)', 365: 'سنة'}
EN_DAYS = {3: '3 Days', 7: '7 Days (One Week)', 10: '10 Days', 15: '15 Days', 20: '20 Days', 30: '30 Days',
           40: '40 Days', 60: '60 Days', 90: '90 Days', 365: 'One Year'}
AR_KH = {1: 'ختمة', 2: 'ختمتين', 3: '3 ختمات'}
EN_KH = {1: 'one khatam', 2: 'two khatams', 3: 'three khatams'}


def khatma_title(slug, en=False):
    days, kh = KHATMA_PRESETS[slug]
    if slug.startswith('ramadan'):
        if en:
            return 'Ramadan Quran Khatam Plan' if kh == 1 else f'Ramadan Plan for {EN_KH[kh].title()}'
        return 'جدول ختم القرآن في رمضان' if kh == 1 else f'جدول {AR_KH[kh]} في رمضان'
    if en:
        return f'Finish the Quran in {EN_DAYS[days]}'
    return f'ختم القرآن في {AR_DAYS[days]}'


def khatma_links(en=False):
    return [(slug, khatma_title(slug, en)) for slug in KHATMA_PRESETS]


# ---------------------------------------------------------------- خطة الحفظ


HIFZ_PRESETS = {1: 'سنة', 2: 'سنتين', 3: '3 سنوات', 4: '4 سنوات', 5: '5 سنوات'}
HIFZ_PRESETS_EN = {1: '1 Year', 2: '2 Years', 3: '3 Years', 4: '4 Years', 5: '5 Years'}


def hifz_order(direction='end'):
    """ترتيب صفحات الحفظ: من آخر المصحف (جزء عمّ ثم تبارك…) أو من أوله"""
    if direction == 'start':
        return list(range(1, TOTAL_PAGES + 1))
    order = []
    for j in range(30, 0, -1):
        a = JUZ_START[j - 1]
        b = JUZ_START[j] - 1 if j < 30 else TOTAL_PAGES
        order += list(range(a, b + 1))
    return order


def hifz_stats(years, days_per_week=5):
    weeks = years * 52
    mem_days = weeks * days_per_week
    ppd = TOTAL_PAGES / mem_days
    return {'years': years, 'days_per_week': days_per_week, 'mem_days': mem_days,
            'pages_per_day_txt': _num(ppd), 'lines_per_day': int(round(ppd * 15)),
            'pages_per_week_txt': _num(ppd * days_per_week),
            'minutes': int(min(90, max(20, round(ppd * 25 / 5) * 5)))}


def hifz_rows(years, direction='end'):
    """جدول شهري: كل شهر هتحفظ من فين لفين (مجموعات متصلة من الصفحات)"""
    months = years * 12
    order = hifz_order(direction)
    bounds = [round(i * TOTAL_PAGES / months) for i in range(months + 1)]
    rows = []
    for m in range(months):
        seg = order[bounds[m]:bounds[m + 1]]
        if not seg:
            continue
        # أجزاء الصفحات المتصلة جوه الشهر (من آخر المصحف ممكن الشهر يعدّي من جزء لجزء قبله)
        runs, cur = [], [seg[0]]
        for p in seg[1:]:
            if p == cur[-1] + 1:
                cur.append(p)
            else:
                runs.append(cur)
                cur = [p]
        runs.append(cur)
        rows.append({'month': m + 1, 'pages': len(seg),
                     'runs': [{'from_page': r[0], 'to_page': r[-1], 'from': PAGE_START[r[0] - 1], 'to': page_end(r[-1]),
                               'juz': juz_of_page(r[0]), 'juz_to': juz_of_page(r[-1])} for r in runs],
                     'done_pct': round(100 * bounds[m + 1] / TOTAL_PAGES)})
    return rows
