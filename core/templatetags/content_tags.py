"""تنسيق المقالات والإجابات بشكل آمن.

الأدمن بيكتب نص عادي، وممكن يستخدم علامات بسيطة:
  ## عنوان رئيسي        ### عنوان فرعي
  - عنصر في قائمة       1. عنصر مرقّم
  > اقتباس أو تنبيه     **كلام بخط عريض**
  [نص اللينك](/quran/18/)    ﴿آية﴾ بتتكتب بخط المصحف
  | عمود | عمود |  (جدول، أول صف هو العناوين)
وأي HTML بيتكتب بيظهر نص عادي (escape)، فمفيش خطر من الكود.
المقالات القديمة المكتوبة نص عادي بتظهر زي ما هي (فقرات)."""
import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_BOLD = re.compile(r'\*\*(.+?)\*\*')
_ITAL = re.compile(r'(?<![*\w])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*\w])')
_LINK = re.compile(r'\[([^\]\n]+)\]\(((?:/|https://)[^\s)]*)\)')
_AYAH = re.compile(r'﴿([^﴾\n]+)﴾')
_OL = re.compile(r'^\d+[.)]\s+')


def _slug(text, used):
    base = re.sub(r'[^\w؀-ۿ]+', '-', text).strip('-')[:60] or 'section'
    s, i = base, 2
    while s in used:
        s, i = f'{base}-{i}', i + 1
    used.add(s)
    return s


def _inline(text):
    t = escape(text)
    t = _BOLD.sub(r'<strong>\1</strong>', t)
    t = _ITAL.sub(r'<em>\1</em>', t)

    def link(m):
        url = m.group(2)
        ext = url.startswith('https://') and 'alagme.com' not in url
        rel = ' rel="noopener" target="_blank"' if ext else ''
        return f'<a href="{url}"{rel}>{m.group(1)}</a>'
    t = _LINK.sub(link, t)
    t = _AYAH.sub(r'<span class="qv">﴿\1﴾</span>', t)
    return t


def _parse(text):
    lines = (text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out, toc, used = [], [], set()
    para, lst, table, quote = [], None, [], []

    def flush_para():
        if para:
            out.append('<p>' + '<br>'.join(_inline(x) for x in para) + '</p>')
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append(f'<{tag}>' + ''.join(f'<li>{_inline(i)}</li>' for i in items) + f'</{tag}>')
            lst = None

    def flush_table():
        if table:
            rows = [r for r in table if not re.fullmatch(r'[\s|:\-]+', r)]
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
            if cells:
                head = ''.join(f'<th scope="col">{_inline(c)}</th>' for c in cells[0])
                body = ''.join('<tr>' + ''.join(f'<td>{_inline(c)}</td>' for c in r) + '</tr>' for r in cells[1:])
                out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            table.clear()

    def flush_quote():
        if quote:
            out.append('<blockquote>' + '<br>'.join(_inline(q) for q in quote) + '</blockquote>')
            quote.clear()

    def flush_all():
        flush_para(); flush_list(); flush_table(); flush_quote()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_all()
            continue
        if line.startswith('### ') or line.startswith('## '):
            flush_all()
            level = 3 if line.startswith('### ') else 2
            title = line[level + 1:].strip()
            sid = _slug(title, used)
            if level == 2:
                toc.append((sid, re.sub(r'^\d+[.)]\s*', '', title)))
            out.append(f'<h{level} id="{sid}">{_inline(title)}</h{level}>')
            continue
        if line.startswith('|'):
            flush_para(); flush_list(); flush_quote()
            table.append(line)
            continue
        if line.startswith('> ') or line == '>':
            flush_para(); flush_list(); flush_table()
            quote.append(line[2:])
            continue
        if line.startswith(('- ', '• ', '* ')) or _OL.match(line):
            flush_para(); flush_table(); flush_quote()
            tag = 'ol' if _OL.match(line) else 'ul'
            item = _OL.sub('', line) if tag == 'ol' else line[2:]
            if lst and lst[0] != tag:
                flush_list()
            if not lst:
                lst = (tag, [])
            lst[1].append(item)
            continue
        flush_list(); flush_table(); flush_quote()
        para.append(line)
    flush_all()
    return '\n'.join(out), toc


@register.filter
def rich(text):
    return mark_safe(_parse(text)[0])


@register.filter
def toc(text):
    """قائمة [(id, عنوان)] بعناوين ## عشان فهرس المقال"""
    return _parse(text)[1]


@register.filter
def plain(text):
    """نص من غير علامات التنسيق (للوصف وschema)"""
    t = re.sub(r'^\s*(#{2,3}|[-•*>]|\d+[.)])\s+', '', text or '', flags=re.M)
    t = _BOLD.sub(r'\1', t)
    t = _ITAL.sub(r'\1', t)
    t = _LINK.sub(r'\1', t)
    # الجداول: صف الفاصل (|---|) بيتشال، وباقي الصفوف بتتحول لسطر "خلية - خلية" بدل ما تضيع
    # (قبل كده كانت بتتمسح كلها، فإجابات زي "أمثلة:" كانت بتظهر في Schema من غير الأمثلة)
    t = re.sub(r'^[ \t]*\|[ \t|:\-]+\|[ \t]*$', '', t, flags=re.M)
    t = re.sub(r'^[ \t]*\|(.*)\|[ \t]*$', lambda m: ' - '.join(c.strip() for c in m.group(1).split('|') if c.strip()),
               t, flags=re.M)
    t = _AYAH.sub(r'﴿\1﴾', t)
    return re.sub(r'\n{2,}', '\n', t).strip()


_LATIN = re.compile(r'[A-Za-z]')
_ARABIC = re.compile(r'[\u0600-\u06FF]')


@register.filter
def is_latin(text):
    """True لو النص إنجليزي في الغالب (عشان نظبط lang و dir للصفحة)"""
    t = text or ''
    return len(_LATIN.findall(t)) > len(_ARABIC.findall(t))


@register.filter
def translation_of(slug):
    """رابط المقال المترجم (عربي ⇄ إنجليزي) لو موجود في content_seed"""
    try:
        from content_seed import translation_pairs
        return translation_pairs().get(slug, '')
    except Exception:
        return ''


@register.filter
def seo_title(title, suffix=''):
    """يضيف اسم الموقع للعنوان بس لو فيه مكان (جوجل بيقص العناوين بعد ~60 حرف)."""
    title = (title or '').strip()
    if suffix and len(title) + len(suffix) + 3 <= 60:
        return f'{title} | {suffix}'
    return title


_COVER_RE = re.compile(r'/static/images/blog/([\w-]+)\.jpg$')


@lru_cache(maxsize=1024)
def _thumb_exists(stem):
    from django.conf import settings
    return (Path(settings.BASE_DIR) / 'static' / 'images' / 'blog' / 'thumbs' / f'{stem}.webp').exists()


@register.filter
def card_img(url):
    """نسخة WebP خفيفة (640px) من غلاف المقال للكروت، لو موجودة."""
    m = _COVER_RE.search(url or '')
    if m and _thumb_exists(m.group(1)):
        return url[:m.start()] + f'/static/images/blog/thumbs/{m.group(1)}.webp'
    return url


TITLE_MAX = 60
DESC_MIN, DESC_MAX = 120, 160
_DESC_TAIL = ' مؤسسة العجمي لتحفيظ القرآن الكريم وتعليم التجويد أونلاين للأطفال والكبار.'


_DANGLING = {'في', 'من', 'على', 'عن', 'إلى', 'الى', 'أن', 'و', 'أو', 'ثم', 'مع', 'بين', 'التي', 'الذي', 'لا',
             'and', 'or', 'to', 'the', 'of', 'a', 'an', 'in', 'for', 'with', 'how', 'why', 'what'}


def _clip_words(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    sp = cut.rfind(' ')
    out = (cut[:sp] if sp > limit * 0.6 else text[:limit])
    if out.count('(') > out.count(')'):
        out = out[:out.rfind('(')]
    words = out.split()
    while len(words) > 3 and (words[-1].lower() in _DANGLING or words[-1].startswith('و') and len(words[-1]) <= 2):
        words.pop()
    return ' '.join(words).rstrip(' ،,:-–|')


def _unesc(v):
    import html as _h
    return _h.unescape(str(v or ''))


@register.filter
def seo_clip_title(title):
    """عنوان الصفحة في <title> مايزيدش عن 60 حرف (Bing وجوجل بيعلموا على الأطول ويقصّوه).
    بنشيل اسم الموقع الأول، وبعدين ناخد الجزء اللي قبل «:» لو كافي، وإلا نقص على كلمة."""
    return mark_safe(escape(_clip_title(_unesc(title))))


def _clip_title(title):
    t = ' '.join(title.split())
    if len(t) <= TITLE_MAX:
        return t
    if ' | ' in t:
        t = t.rsplit(' | ', 1)[0].strip()
        if len(t) <= TITLE_MAX:
            return t
    for sep in (':', '؟', '?', ' - ', '،'):
        if sep in t:
            head, rest = t.split(sep, 1)
            head = head.strip() + (sep if sep in '؟?' else '')
            if 20 <= len(head) <= TITLE_MAX:
                if len(head) < 35 and sep == ':':
                    # نحاول نحتفظ بجزء من العنوان الفرعي لحد أول «،» أو «(» لو يدخل في 60
                    sub = re.split(r'[،(]', rest.strip(), 1)[0].strip()
                    if sub and len(head) + 2 + len(sub) <= TITLE_MAX:
                        return f'{head}: {sub}'
                return head
    return _clip_words(t, TITLE_MAX)


@register.filter
def seo_fill_desc(desc):
    """الوصف بين 120 و160 حرف: لو قصير نكمّله بتعريف الموقع، ولو طويل نقصه على كلمة."""
    return mark_safe(escape(_fill_desc(_unesc(desc))))


def _fill_desc(desc):
    d = ' '.join(desc.split())
    if len(d) < DESC_MIN:
        if d and d[-1] not in '.!؟?':
            d += '.'
        d = (d + _DESC_TAIL).strip()
        if len(d) < DESC_MIN:
            d += ' احجز حلقة تجريبية مجانية الآن.'
    return _clip_words(d, DESC_MAX)
