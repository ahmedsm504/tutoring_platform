"""خلاصة RSS للمقالات: جوجل بيزور الـ feeds أسرع من السايت ماب، وتتضاف في Search Console كـ sitemap."""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from .models import Post


class LatestPostsFeed(Feed):
    feed_type = Rss201rev2Feed
    title = 'مدونة مؤسسة العجمي لتحفيظ القرآن الكريم'
    link = '/blog/'
    description = 'مقالات في أحكام التجويد وطرق حفظ القرآن ومراجعته وتحفيظ الأطفال.'
    language = 'ar'

    def items(self):
        return Post.objects.filter(status='published').order_by('-published_at')[:60]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.meta_description or item.excerpt

    def item_link(self, item):
        return f'/blog/{item.slug}/'

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [item.category.name] if item.category else []
