"""دوال الإضافة اللي بتستخدمها الـ data migrations. كلها آمنة تتنفذ أكتر من مرة:
أي مقال أو سؤال موجود (بنفس الرابط أو العنوان) مبيتلمسش."""
import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def _author(apps):
    User = apps.get_model('accounts', 'User')
    author = User.objects.filter(is_superuser=True).order_by('id').first()
    if author is None:
        author, _ = User.objects.get_or_create(
            username='alagme_team', defaults={'first_name': 'فريق مؤسسة العجمي', 'is_active': False, 'password': '!'})
    return author


def seed_articles(apps, schema_editor=None):
    from content_seed import BLOG_CATEGORIES, load_articles
    Category = apps.get_model('blog', 'Category')
    Post = apps.get_model('blog', 'Post')
    author = _author(apps)
    cats = {}
    for slug, (name, icon, desc) in BLOG_CATEGORIES.items():
        cats[slug], _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'description': desc})
    base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    now = timezone.now()
    articles = load_articles()
    existing = set(Post.objects.filter(slug__in=[a['slug'] for a in articles]).values_list('slug', flat=True))
    new = [a for a in articles if a['slug'] not in existing]
    for i, a in enumerate(new):
        Post.objects.create(
            slug=a['slug'], title=a['title'][:200], author=author, category=cats.get(a['category']),
            excerpt=a['excerpt'][:300], content=a['body'], status='published',
            published_at=now - timedelta(minutes=(len(new) - i) * 7),
            reading_time=int(a.get('reading', 5)), meta_description=a['meta'][:160],
            keywords=a['keywords'][:200], is_featured=a.get('featured') == '1',
            cloud_url=f"{base}/static/images/blog/{a['slug']}.jpg", image_alt=a['title'][:200],
        )


def refresh_articles(apps, slugs):
    """تحديث محتوى مقالات موجودة من ملفاتها (للتصحيحات)، بدون تغيير العنوان أو الرابط أو التاريخ."""
    from content_seed import load_articles
    Post = apps.get_model('blog', 'Post')
    by_slug = {a['slug']: a for a in load_articles()}
    for slug in slugs:
        a = by_slug.get(slug)
        if not a:
            continue
        Post.objects.filter(slug=slug).update(
            content=a['body'], excerpt=a['excerpt'][:300],
            meta_description=a['meta'][:160], keywords=a['keywords'][:200],
        )


def _plain(text, limit=155):
    t = re.sub(r'^\s*(#{2,3}|[-•*>]|\d+[.)])\s+', '', text, flags=re.M)
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'^\|.*$', '', t, flags=re.M)
    t = re.sub(r'\s+', ' ', t).strip()
    return t if len(t) <= limit else t[:limit - 1].rsplit(' ', 1)[0] + '…'


def _slugify(title):
    if re.search(r'[A-Za-z]', title) and not re.search(r'[؀-ۿ]', title):
        s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    else:
        s = re.sub(r'[^\w\-]', '', title.strip().replace(' ', '-'))
    return s[:240]


def seed_questions(apps, schema_editor=None):
    from content_seed.questions import ASKER, QNA_CATEGORIES, QUESTIONS
    Cat = apps.get_model('qna', 'QuestionCategory')
    Q = apps.get_model('qna', 'PublicQuestion')
    A = apps.get_model('qna', 'QuestionAnswer')
    team = apps.get_model('accounts', 'User').objects.filter(is_superuser=True).order_by('id').first()
    cats = {}
    for slug, (name, icon, desc, order) in QNA_CATEGORIES.items():
        cats[slug], _ = Cat.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'description': desc, 'order': order})
    titles = set(Q.objects.filter(title__in=[q[1] for q in QUESTIONS]).values_list('title', flat=True))
    new = [q for q in QUESTIONS if q[1] not in titles]
    now = timezone.now()
    for i, (cat, title, question, answer) in enumerate(new):
        slug = base = _slugify(title)
        n = 1
        while Q.objects.filter(slug=slug).exists():
            slug, n = f'{base}-{n}', n + 1
        q = Q.objects.create(
            visitor_name=ASKER.get(cat, 'زوار الموقع'), title=title, question_text=question,
            category=cats[cat], status='approved', is_frequent=True, slug=slug, meta_description=_plain(answer))
        Q.objects.filter(pk=q.pk).update(created_at=now - timedelta(minutes=(len(new) - i) * 3))
        A.objects.create(question=q, answer_text=answer, answered_by=team, is_featured=True)
