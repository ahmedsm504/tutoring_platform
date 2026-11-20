from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from core.models import GscUrlStatus
from core.tests import TEST_SETTINGS

from .models import Category, Post
from .related import discover_posts


@override_settings(**TEST_SETTINGS)
class DiscoverPostsTests(TestCase):
    """لينكات «جديد في المدونة» بتشاور على المقالات اللي جوجل لسه مفهرسهاش بس، وبنفس لغة المقال."""

    def setUp(self):
        cache.clear()
        Post.objects.all().delete()  # مقالات البذرة
        u = get_user_model().objects.create_user('blog_author', 'ba@example.com', 'x-Pass-12345')
        tj, _ = Category.objects.get_or_create(slug='tajweed', defaults={'name': 'تجويد'})
        en, _ = Category.objects.get_or_create(slug='english', defaults={'name': 'English'})
        now = timezone.now()
        body = 'هذا نص طويل عن أحكام التلاوة. ' * 400

        def mk(slug, cat, days=90):
            return Post.objects.create(title=f'مقال {slug}', slug=slug, author=u, category=cat, content=body,
                                       status='published', published_at=now - timezone.timedelta(days=days))
        self.page = mk('indexed-page', tj)
        self.bad = mk('not-indexed', tj)
        self.ok = mk('indexed-other', tj)
        self.fresh = mk('fresh-unchecked', tj, days=3)
        self.old = mk('old-unchecked', tj)
        self.en_bad = mk('english-not-indexed', en)
        for p, v in ((self.page, 'PASS'), (self.ok, 'PASS'), (self.bad, 'NEUTRAL'), (self.en_bad, 'NEUTRAL')):
            GscUrlStatus.objects.create(url=f'https://alagme.com/blog/{p.slug}/', verdict=v)

    def test_links_only_unindexed_same_language(self):
        mine = {'not-indexed', 'fresh-unchecked', 'old-unchecked', 'indexed-other', 'english-not-indexed'}
        slugs = {p.slug for p in discover_posts(self.page, limit=50)} & mine
        self.assertEqual(slugs, {'not-indexed', 'fresh-unchecked'})

    def test_rendered_on_article_page(self):
        # المقالات ذات الصلة (4) بتاخد أول المرشحين، فنزود مقالات جديدة عشان يفضل منها لـ«جديد في المدونة»
        for i in range(6):
            Post.objects.create(title=f'مقال جديد {i}', slug=f'brand-new-{i}', author=self.page.author,
                                category=self.page.category, content=self.page.content, status='published',
                                published_at=timezone.now())
        r = self.client.get('/blog/indexed-page/', HTTP_HOST='alagme.com', secure=True)
        self.assertContains(r, 'new-posts-title')
        self.assertContains(r, '/blog/brand-new-')
