"""تحدي 30 يوم لحفظ جزء عمّ: 28 يوم حفظ (من الناس لحد النبأ، السور الصغيرة الأول) + يومين مراجعة.
الخطة متحسوبة من عدد الآيات (حد أقصى 27 آية في اليوم، والسور الطويلة بتتقسم)."""
from functools import lru_cache

from . import quran

CAP = 27
RAMADAN_START = '2027-02-08'  # 1 رمضان 1448 حسب الحسابات الفلكية (زر «ابدأ مع أول رمضان»)
FIRST, LAST = 78, 114


@lru_cache(maxsize=1)
def plan():
    days, cur, n = [], [], 0
    for s in range(LAST, FIRST - 1, -1):
        c = quran.ayah_count(s)
        if c > CAP:
            if cur:
                days.append(cur)
                cur, n = [], 0
            k = -(-c // CAP)
            size = -(-c // k)
            for i in range(k):
                days.append([(s, i * size + 1, min(c, (i + 1) * size))])
            continue
        if n + c > CAP and cur:
            days.append(cur)
            cur, n = [], 0
        cur.append((s, 1, c))
        n += c
    if cur:
        days.append(cur)
    out = []
    for i, parts in enumerate(days, start=1):
        items = []
        for s, a, b in parts:
            full = a == 1 and b == quran.ayah_count(s)
            items.append({'surah': s, 'name': quran.surah_name(s), 'from': a, 'to': b, 'full': full,
                          'label': f'سورة {quran.surah_name(s)}' + ('' if full else f' (الآيات {a}–{b})'),
                          'url': f'/quran/{s}/' + ('' if a == 1 else f'#a{a}')})
        done = [it for it in items if it['to'] == quran.ayah_count(it['surah'])]
        out.append({'n': i, 'kind': 'new', 'items': items, 'ayat': sum(b - a + 1 for _, a, b in parts),
                    'completes': [it['surah'] for it in done]})
    first_half = [d for d in out[:len(out) // 2]]
    out.append({'n': len(out) + 1, 'kind': 'review', 'title': 'مراجعة: من الناس لحد ' + quran.surah_name(first_half[-1]['items'][-1]['surah']),
                'items': [], 'ayat': 0, 'completes': []})
    out.append({'n': len(out) + 1, 'kind': 'review', 'title': 'مراجعة جزء عمّ كامل وتسميع، وشهادة الختام 🎉',
                'items': [], 'ayat': 0, 'completes': []})
    return out
