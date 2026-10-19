"""يضيف مقالات المدونة الجاهزة من content_seed/articles (مرة واحدة).
أي مقال بنفس الرابط موجود أصلًا مبيتلمسش، فتعديلاتك من لوحة التحكم بتفضل زي ما هي."""
from datetime import timedelta

from django.conf import settings
from django.db import migrations
from django.utils import timezone


def seed(apps, schema_editor):
    from content_seed import BLOG_CATEGORIES, load_articles

    User = apps.get_model('accounts', 'User')
    Category = apps.get_model('blog', 'Category')
    Post = apps.get_model('blog', 'Post')

    author = User.objects.filter(is_superuser=True).order_by('id').first()
    if author is None:
        author, _ = User.objects.get_or_create(
            username='alagme_team',
            defaults={'first_name': 'فريق مؤسسة العجمي', 'is_active': False, 'password': '!'},
        )

    cats = {}
    for slug, (name, icon, desc) in BLOG_CATEGORIES.items():
        cats[slug], _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'description': desc})

    base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    now = timezone.now()
    articles = load_articles()[:17]  # الدفعة الأولى بس (الباقي في 0004)
    for i, a in enumerate(articles):
        if Post.objects.filter(slug=a['slug']).exists():
            continue
        Post.objects.create(
            slug=a['slug'], title=a['title'][:200], author=author, category=cats.get(a['category']),
            excerpt=a['excerpt'][:300], content=a['body'], status='published',
            published_at=now - timedelta(hours=len(articles) - i),
            reading_time=int(a.get('reading', 5)), meta_description=a['meta'][:160],
            keywords=a['keywords'][:200], is_featured=a.get('featured') == '1',
            cloud_url=f"{base}/static/images/blog/{a['slug']}.jpg", image_alt=a['title'][:200],
        )


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0002_post_image_alt_postimage_postvideo'),
        ('accounts', '0004_fcmtoken_user'),
    ]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
