from django.test import TestCase

# Create your tests here.


class TopicHubTests(TestCase):
    """صفحات الأسئلة المجمعة: كل التصنيفات، 25 سؤال في الصفحة، مفهرسة، وصفحة السؤال noindex بتشاور عليها."""

    def test_hubs_cover_every_answered_question_once(self):
        from django.test import Client
        from .hubs import PER_PAGE, hub_pages, hub_questions, hub_url
        from .models import PublicQuestion, QuestionCategory
        c = Client()
        seen = 0
        for cat, page, _ in hub_pages():
            r = c.get(hub_url(cat, page))
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, 'index, follow')
            self.assertNotContains(r, 'noindex')
            seen += r.content.decode().count('class="answer official" id="q-')
        total = sum(hub_questions(cat).count() for cat in QuestionCategory.objects.all())
        self.assertEqual(seen, total)
        if total:
            cat = next(cat for cat, _, _ in hub_pages())
            self.assertEqual(c.get(hub_url(cat) + '1/').status_code, 301)
            self.assertEqual(c.get(hub_url(cat, 999)).status_code, 404)
