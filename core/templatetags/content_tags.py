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

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_BOLD = re.compile(r'\*\*(.+?)\*\*')
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
                toc.append((sid, title))
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
    t = _LINK.sub(r'\1', t)
    t = re.sub(r'^\|.*\|\s*$', '', t, flags=re.M)
    return re.sub(r'\n{2,}', '\n', t).strip()
