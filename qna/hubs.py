"""صفحات «الأسئلة الشائعة» المجمعة لكل تصنيف.

الأسئلة الفردية إجاباتها قصيرة (حوالي 100 كلمة)، فلو اتفهرست كل واحدة لوحدها جوجل بيشوف
الموقع «محتوى منخفض القيمة» (سبب رفض أدسنس). الحل: كل تصنيف ليه صفحات كبيرة فيها الأسئلة
بإجاباتها كاملة (25 سؤال في الصفحة)، ودي اللي بتتفهرس وتظهر في السايت ماب، وصفحة السؤال
الفردية تفضل موجودة للزوار لكن noindex وبتشاور على مكانها في الصفحة المجمعة.

الترتيب من الأقدم للأحدث عشان السؤال الجديد يروح آخر صفحة، وروابط الصفحات القديمة تفضل ثابتة.
"""
from django.urls import reverse

from .models import PublicQuestion, QuestionCategory

PER_PAGE = 25


def hub_questions(category):
    return (PublicQuestion.objects
            .filter(status='approved', category=category, official_answer__isnull=False)
            .exclude(slug='').exclude(slug__isnull=True)
            .select_related('official_answer')
            .order_by('created_at', 'id'))


def hub_url(category, page=1):
    slug = category.slug if hasattr(category, 'slug') else category
    if page <= 1:
        return reverse('qna:topic_hub', args=[slug])
    return reverse('qna:topic_hub_page', args=[slug, page])


def num_pages(count):
    return max(1, -(-count // PER_PAGE))


def hub_pages():
    """كل صفحات التجميع اللي فيها أسئلة: [(category, page_number, last_modified)]"""
    out = []
    for cat in QuestionCategory.objects.order_by('order', 'name'):
        qs = list(hub_questions(cat).values_list('created_at', flat=True))
        for p in range(1, num_pages(len(qs)) + 1 if qs else 1):
            chunk = qs[(p - 1) * PER_PAGE:p * PER_PAGE]
            out.append((cat, p, max(chunk)))
    return out


def question_hub_url(question):
    """رابط السؤال جوه صفحة التجميع بتاعته (مع #anchor)، أو None لو مش هيظهر فيها."""
    if not question.category_id or not question.slug or question.status != 'approved':
        return None
    ids = list(hub_questions(question.category).values_list('id', flat=True))
    if question.id not in ids:
        return None
    page = ids.index(question.id) // PER_PAGE + 1
    return f'{hub_url(question.category, page)}#q-{question.id}'
