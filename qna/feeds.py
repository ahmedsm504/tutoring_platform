from django.contrib.syndication.views import Feed

from .models import PublicQuestion


class LatestQuestionsFeed(Feed):
    title = 'أسئلة وأجوبة مؤسسة العجمي'
    link = '/questions/'
    description = 'أحدث الأسئلة المجاب عنها في تحفيظ القرآن والتجويد وتعليم الأطفال.'
    language = 'ar'

    def items(self):
        return (PublicQuestion.objects.filter(status='approved', official_answer__isnull=False)
                .order_by('-created_at')[:80])

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.meta_description or item.question_text[:200]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created_at

    def item_updateddate(self, item):
        return item.updated_at
