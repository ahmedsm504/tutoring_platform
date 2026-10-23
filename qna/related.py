"""أسئلة ذات صلة متوزعة: بدل أكثر 5 أسئلة مشاهدة في التصنيف (نفس الـ5 لكل الأسئلة)،
بنختار حسب تشابه العنوان ونكمّل بجيران السؤال في نفس التصنيف."""
from django.core.cache import cache

from blog.related import _tokens

from .models import PublicQuestion


def related_question_ids(question, limit=5):
    key = f'qna:related:v1:{question.pk}'
    ids = cache.get(key)
    if ids is not None:
        return ids
    qs = PublicQuestion.objects.filter(status='approved').exclude(pk=question.pk)
    if question.category_id:
        qs = qs.filter(category_id=question.category_id)
    rows = list(qs.values_list('pk', 'title'))
    mine = _tokens(question.title, '')
    scored = sorted(((len(mine & _tokens(t, '')), pk) for pk, t in rows), reverse=True)
    ids = [pk for s, pk in scored if s >= 2][:limit]
    if len(ids) < limit:
        before = sorted((pk for pk, _ in rows if pk < question.pk and pk not in ids), reverse=True)
        after = sorted(pk for pk, _ in rows if pk > question.pk and pk not in ids)
        for a, b in zip(before + [None] * len(after), after + [None] * len(before)):
            for pk in (a, b):
                if pk and len(ids) < limit and pk not in ids:
                    ids.append(pk)
            if len(ids) >= limit:
                break
    cache.set(key, ids, 6 * 3600)
    return ids
