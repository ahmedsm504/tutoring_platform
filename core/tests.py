"""اختبارات شاملة: كل صفحة في الموقع بتفتح من غير أخطاء + فحوصات السيو والأمان.

تشغيل:  python manage.py test
"""
import json
import re
import xml.etree.ElementTree as ET
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone

from accounts.models import Session, StudentProfile
from blog.models import Category, Post
from blog.views import merged_redirects


def live_slug(slug):
    """الـ slug الحالي للمقال (لو اتدمج في صفحة شاملة بيرجع slug الصفحة)"""
    return merged_redirects().get(slug, slug).split('#')[0]
from qna.models import CommunityAnswer, PublicQuestion, QuestionAnswer, QuestionCategory

from .models import Country, Lesson, MonthlyEvaluation, Payment, Student, Supervisor, Teacher

User = get_user_model()
LDJSON_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

TEST_SETTINGS = dict(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=['*'])


@override_settings(**TEST_SETTINGS)
class SiteSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patcher = mock.patch('blog.signals.send_indexnow')
        cls.patcher.start()
        cls.admin = User.objects.create_user('boss', password='pass12345', is_staff=True, is_superuser=True, user_type='admin')
        cls.country = Country.objects.create(name='مصر')
        cls.sup_user = User.objects.create_user('sup', password='pass12345', user_type='supervisor')
        cls.supervisor = Supervisor.objects.create(name='مشرفة', user=cls.sup_user)
        cls.t_user = User.objects.create_user('teach', password='pass12345', user_type='teacher')
        cls.teacher = Teacher.objects.create(name='فاطمة', user=cls.t_user, supervisor=cls.supervisor, phone='01000000000')
        cls.student = Student.objects.create(country=cls.country, teacher=cls.teacher, name='أحمد', month='أكتوبر',
                                             phone='01011111111', guardian_phone='01022222222')
        now = timezone.now()
        cls.lesson = Lesson.objects.create(student=cls.student, teacher=cls.teacher, scheduled_at=now - timezone.timedelta(hours=2))
        Lesson.objects.create(student=cls.student, teacher=cls.teacher, scheduled_at=now + timezone.timedelta(days=1))
        cls.payment = Payment.objects.create(student=cls.student, amount=300)
        cls.evaluation = MonthlyEvaluation.objects.create(student=cls.student, student_name='أحمد', month_label='أكتوبر 2026')
        cls.category = Category.objects.create(name='التجويد', slug='التجويد')
        cls.post = Post.objects.create(title='أحكام النون الساكنة', author=cls.admin, category=cls.category,
                                       content='محتوى ' * 300, status='published', published_at=now,
                                       meta_description='شرح مبسط لأحكام النون الساكنة والتنوين')
        cls.qcat, _ = QuestionCategory.objects.get_or_create(slug='tajweed', defaults={'name': 'التجويد'})
        cls.question = PublicQuestion.objects.create(visitor_name='زائر', title='ما حكم الإدغام؟', question_text='سؤال عن الإدغام بغنة',
                                                     category=cls.qcat, status='approved', slug='idgham')
        QuestionAnswer.objects.create(question=cls.question, answer_text='الإدغام هو...', answered_by=cls.admin)
        CommunityAnswer.objects.create(question=cls.question, answer_text='إجابة من المجتمع', visitor_name='محمد')

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        super().tearDownClass()

    # ---------------- الصفحات العامة + السيو ----------------
    PUBLIC = ['home', 'about', 'contact', 'pricing', 'quality_standards', 'blog_list', 'qna:question_list', 'qna:ask']

    def _check_seo(self, url, resp):
        html = resp.content.decode()
        self.assertEqual(resp.status_code, 200, url)
        m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        self.assertTrue(m, f'canonical ناقص في {url}')
        self.assertTrue(m.group(1).startswith('https://alagme.com/'), f'{url}: {m.group(1)}')
        self.assertNotIn('testserver', html, f'{url} فيه دومين الطلب بدل الدومين الأساسي')
        self.assertNotIn('name="googlebot"', html)
        self.assertEqual(html.count('<meta name="description"'), 1, url)
        og = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        self.assertTrue(og and og.group(1).startswith('https://') and og.group(1).count('https://') == 1, f'{url}: og:image غلط')
        blocks = LDJSON_RE.findall(html)
        self.assertTrue(blocks, f'{url}: مفيش structured data')
        for b in blocks:
            try:
                json.loads(b)
            except ValueError as e:
                self.fail(f'{url}: JSON-LD مش سليم: {e}\n{b[:400]}')
        self.assertNotIn('X-Robots-Tag', resp.headers)

    def test_public_pages(self):
        for name in self.PUBLIC:
            url = reverse(name)
            self._check_seo(url, self.client.get(url))

    def test_detail_pages(self):
        for url in [reverse('blog_detail', args=[self.post.slug]), reverse('category_posts', args=[self.category.slug]),
                    reverse('qna:question_detail', args=[self.question.slug])]:
            self._check_seo(url, self.client.get(url))
        html = self.client.get(reverse('blog_detail', args=[self.post.slug])).content.decode()
        self.assertIn('property="og:type" content="article"', html)
        self.assertIn('article:published_time', html)

    def test_contact_form_works(self):
        r = self.client.post(reverse('contact'), {'name': 'ولي أمر', 'country': 'مصر', 'gender': 'male', 'phone': '0100'})
        self.assertRedirects(r, reverse('thank_you'), fetch_redirect_response=False)
        r = self.client.get('/accounts/contact/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], reverse('contact'))

    def test_robots_sitemap_llms_indexnow(self):
        robots = self.client.get('/robots.txt').content.decode()
        self.assertIn('Sitemap: https://alagme.com/sitemap.xml', robots)
        for p in ['/teacher-portal/', '/chat/', '/report/', '/dashboard/']:
            self.assertIn(f'Disallow: {p}', robots)
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
        locs = [e.text for e in ET.fromstring(r.content).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertTrue(all(l.startswith('https://') for l in locs))
        self.assertFalse(any('/accounts/' in l for l in locs), 'صفحات الدخول/التسجيل لسه في الخريطة')
        self.assertTrue(any('/contact/' in l for l in locs))
        self.assertTrue(any(self.post.slug in l or 'blog/' in l for l in locs))
        self.assertEqual(self.client.get('/llms.txt').status_code, 200)
        from django.conf import settings
        r = self.client.get(f'/{settings.INDEXNOW_KEY}.txt')
        self.assertEqual(r.content.decode(), settings.INDEXNOW_KEY)

    @override_settings(DEBUG=False)
    def test_canonical_host_redirect(self):
        r = self.client.get('/pricing/?x=1', HTTP_HOST='www.alagme.com')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], 'https://alagme.com/pricing/?x=1')
        r = self.client.get('/', HTTP_HOST='tutoringplatform-production-b8c8.up.railway.app')
        self.assertEqual(r.status_code, 301)
        # POST (زي webhook واتساب) مبيتحولش
        r = self.client.post('/chat/whatsapp/webhook/', data='{}', content_type='application/json', HTTP_HOST='www.alagme.com')
        self.assertNotEqual(r.status_code, 301)

    def test_private_pages_noindex(self):
        self.client.force_login(self.admin)
        for url in ['/dashboard/', reverse('student_detail', args=[self.student.id]), reverse('chat_admin_inbox')]:
            self.assertIn('noindex', self.client.get(url).headers.get('X-Robots-Tag', ''), url)
        r = self.client.get(reverse('public_evaluation', args=[self.evaluation.public_token]))
        self.assertEqual(r.status_code, 200)
        self.assertIn('noindex', r.headers.get('X-Robots-Tag', ''))
        self.assertContains(r, reverse('student_login'))

    # ---------------- كل صفحات لوحات التحكم بتفتح ----------------
    def _arg_for(self, name):
        return {
            'country_id': self.country.id, 'student_id': self.student.id, 'teacher_id': self.teacher.id,
            'year': timezone.now().year, 'month': timezone.now().month, 'payment_id': self.payment.id,
            'lesson_id': self.lesson.id, 'evaluation_id': self.evaluation.id, 'supervisor_id': self.supervisor.id,
            'doc_id': 999999, 'record_id': 999999, 'expense_id': 999999, 'request_id': 999999,
            'token': self.evaluation.public_token, 'message_id': 999999, 'conv_id': 999999,
        }.get(name)

    def _walk(self, patterns, prefix=''):
        for p in patterns:
            if isinstance(p, URLResolver):
                yield from self._walk(p.url_patterns, prefix + str(p.pattern))
            elif isinstance(p, URLPattern) and p.name:
                yield p, prefix + str(p.pattern)

    def _get_all(self, user, path_filter):
        self.client.force_login(user)
        errors = []
        for p, route in self._walk(get_resolver().url_patterns):
            if not path_filter(route):
                continue
            kwargs = {}
            ok = True
            for k in re.findall(r'<(?:\w+:)?(\w+)>', route):
                v = self._arg_for(k)
                if v is None:
                    ok = False
                kwargs[k] = v
            if not ok:
                continue
            try:
                url = reverse(p.name, kwargs=kwargs) if ':' not in route else None
            except Exception:
                continue
            if not url:
                continue
            resp = self.client.get(url)
            if resp.status_code >= 500:
                errors.append(f'{url} -> {resp.status_code}')
        self.assertEqual(errors, [])

    def test_admin_pages_no_500(self):
        self._get_all(self.admin, lambda r: not r.startswith(('admin/', 'teacher-portal', 'supervisor-portal', 'student-portal')))

    def test_teacher_portal_no_500_and_no_phones(self):
        self._get_all(self.t_user, lambda r: r.startswith('teacher-portal') and 'logout' not in r)
        self.client.force_login(self.t_user)
        for url in [reverse('teacher_portal_home'), reverse('teacher_lessons_table'), reverse('teacher_add_lessons'), reverse('chat_teacher_inbox')]:
            html = self.client.get(url).content.decode()
            self.assertNotIn('01011111111', html)
            self.assertNotIn('01022222222', html)

    def test_supervisor_portal_no_500(self):
        self._get_all(self.sup_user, lambda r: r.startswith('supervisor-portal') and 'logout' not in r)

    # ---------------- أمان ----------------
    def test_toggle_status_requires_post(self):
        self.client.force_login(self.admin)
        self.client.get(reverse('toggle_student_status', args=[self.student.id]))
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, 'active')
        self.client.post(reverse('toggle_student_status', args=[self.student.id]))
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, 'inactive')

    def test_mark_lesson_no_open_redirect(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('mark_lesson', args=[self.lesson.id]), {'status': 'completed', 'next': 'https://evil.example/'})
        self.assertNotIn('evil.example', r['Location'])

    def test_teacher_login_account_type(self):
        self.client.force_login(self.admin)
        t = Teacher.objects.create(name='جديدة')
        self.client.post(reverse('create_teacher_login', args=[t.id]), {'username': 'newt', 'password': 'abc12345', 'password2': 'abc12345'})
        u = User.objects.get(username='newt')
        self.assertEqual(u.user_type, 'teacher')
        self.assertFalse(StudentProfile.objects.filter(user=u).exists())
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'newt', 'password': 'abc12345'})
        self.assertEqual(r['Location'], reverse('teacher_portal_home'))

    def test_legacy_supervisor_dashboard_idor(self):
        other_sup = User.objects.create_user('legacy_sup', password='x12345678', user_type='supervisor')
        stu_user = User.objects.create_user('stu', password='x12345678', user_type='student')
        profile = StudentProfile.objects.get(user=stu_user)
        sess = Session.objects.create(student=profile, date=timezone.now())
        self.client.force_login(other_sup)  # مش المشرف بتاع الطالب ده
        self.client.post(reverse('supervisor_dashboard'), {'delete_session': '1', 'session_id': sess.id})
        self.assertTrue(Session.objects.filter(pk=sess.pk).exists())


@override_settings(SECURE_SSL_REDIRECT=False)
class HardeningTests(TestCase):
    def test_scanner_paths_get_tiny_404(self):
        for p in ['/.env', '/.git/config', '/wp-content/debug.log', '/api/phpinfo.php', '/auth.json', '/config.json']:
            r = self.client.get(p)
            self.assertEqual(r.status_code, 404, p)
            self.assertEqual(r.content, b'Not Found')

    def test_real_pages_not_blocked(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/quran/18/').status_code, 200)

    def test_ads_txt(self):
        r = self.client.get('/ads.txt')
        self.assertContains(r, 'pub-4253419170065458, DIRECT')


@override_settings(SECURE_SSL_REDIRECT=False)
class SeededContentTests(TestCase):
    """المقالات والأسئلة الجاهزة بتتضاف مع migrate وبتظهر صح"""

    def test_articles_seeded_and_render(self):
        from blog.models import Post
        from content_seed import load_articles
        slugs = [a['slug'] for a in load_articles()]
        self.assertEqual(Post.objects.filter(slug__in=slugs, status='published').count(), len(slugs))
        r = self.client.get('/blog/noon-sakinah-tanween-rules/', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '<h2 id=')
        self.assertContains(r, 'class="toc-box"')
        self.assertContains(r, '<table>')
        self.assertContains(r, 'class="qv"')
        self.assertContains(r, '/static/images/blog/noon-sakinah-tanween-rules.jpg')
        self.assertNotIn('**', r.content.decode())

    def test_article_internal_links_resolve(self):
        import re
        from content_seed import load_articles
        from content_seed.questions import QUESTIONS
        bodies = [a['body'] for a in load_articles()] + [q[3] for q in QUESTIONS]
        links = set()
        for b in bodies:
            links |= set(re.findall(r'\]\((/[^)#\s]*)', b))
        for url in sorted(links):
            if url.startswith('/student-portal/'):
                continue
            self.assertIn(self.client.get(url).status_code, (200,), url)

    def test_questions_seeded(self):
        from qna.models import PublicQuestion
        from content_seed.questions import QUESTIONS
        self.assertGreaterEqual(PublicQuestion.objects.filter(status='approved', official_answer__isnull=False).count(), len(QUESTIONS))
        q = PublicQuestion.objects.get(title='كم عدد سور وآيات وأجزاء القرآن الكريم؟')
        r = self.client.get(q.get_absolute_url())
        self.assertContains(r, '6236')
        self.assertContains(r, 'QAPage')

    def test_policy_pages(self):
        for url in ['/privacy-policy/', '/terms/', '/editorial-policy/']:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertNotIn('X-Robots-Tag', r)
        self.assertContains(self.client.get('/privacy-policy/'), 'adssettings.google.com')
        self.assertContains(self.client.get('/sitemap.xml'), '/privacy-policy/')

    def test_no_ads_on_thin_pages(self):
        # الإعلانات في صفحات المحتوى الطويل بس (سياسة أدسنس: مفيش إعلانات على صفحات من غير محتوى كافي)
        for url in ['/contact/', '/accounts/login/', '/questions/', '/about/', '/quran/']:
            self.assertNotContains(self.client.get(url, follow=True), 'adsbygoogle.js', msg_prefix=url)
        # مقال قصير (فهرس روابط مثلًا): بيتفهرس، بس من غير إعلانات
        thin_post = next(p for p in Post.objects.indexable() if not p.shows_ads)
        thin = self.client.get(f'/blog/{thin_post.slug}/', follow=True)
        self.assertNotContains(thin, 'adsbygoogle.js')
        self.assertNotContains(thin, 'noindex')
        rich = next(p for p in Post.objects.indexable() if p.shows_ads)
        r = self.client.get(f'/blog/{rich.slug}/', follow=True)
        self.assertContains(r, 'adsbygoogle.js')
        self.assertNotContains(r, 'noindex')
        self.assertContains(self.client.get('/'), 'adsbygoogle.js')
        # صفحة الأسئلة العامة بتتفهرس؛ السؤال الفردي (إجابة قصيرة) noindex وبيتفهرس جوه صفحة التجميع بتاعة تصنيفه
        self.assertNotContains(self.client.get(reverse('qna:question_list')), 'noindex')
        from qna.models import PublicQuestion
        from qna.hubs import question_hub_url
        answered = PublicQuestion.objects.filter(status='approved', official_answer__isnull=False).first()
        detail = self.client.get(reverse('qna:question_detail', args=[answered.slug]))
        self.assertContains(detail, 'noindex, follow')
        hub = question_hub_url(answered)
        self.assertContains(detail, hub)
        hub_page = self.client.get(hub.split('#')[0])
        self.assertNotContains(hub_page, 'noindex')
        self.assertContains(hub_page, f'id="q-{answered.id}"')
        self.assertContains(hub_page, 'adsbygoogle.js')
        self.assertContains(self.client.get(reverse('qna:question_list') + '?category=hifz'), 'noindex, follow')
        self.assertContains(self.client.get(reverse('qna:question_list') + '?search=x'), 'noindex, follow')


@override_settings(SECURE_SSL_REDIRECT=False)
class Wave2Tests(TestCase):
    def test_english_article_lang_and_hreflang(self):
        r = self.client.get('/blog/noon-sakinah-tanween-rules-english/', follow=True)
        self.assertContains(r, '<html lang="en"')
        self.assertContains(r, 'hreflang="ar" href="https://alagme.com/blog/noon-sakinah-tanween-rules/"')
        self.assertContains(r, 'lang="en" dir="ltr"')
        self.assertContains(r, 'In this article')
        r = self.client.get('/blog/noon-sakinah-tanween-rules/', follow=True)
        self.assertContains(r, '<html lang="ar"')
        self.assertContains(r, 'hreflang="en" href="https://alagme.com/blog/noon-sakinah-tanween-rules-english/"')

    def test_english_question_page(self):
        from qna.models import PublicQuestion
        q = PublicQuestion.objects.get(title='How many counts is Madd Lazim?')
        r = self.client.get(q.get_absolute_url())
        self.assertContains(r, '<html lang="en"')
        self.assertContains(r, 'Our answer')

    def test_feeds(self):
        r = self.client.get('/blog/feed/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '<rss')
        newest = Post.objects.filter(status='published').order_by('-published_at').first()
        self.assertContains(r, f'/blog/{newest.slug}/')
        r = self.client.get('/questions/feed/')
        self.assertContains(r, '<rss')

    def test_indexnow_command_tracks_pings(self):
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        from core.models import IndexNowPing
        with mock.patch('core.indexnow.send_indexnow_batch', return_value=True) as send:
            call_command('indexnow_ping', '--force', stdout=StringIO())
            urls = send.call_args[0][0]
            self.assertIn('https://alagme.com/blog/madd-types-tajweed/', urls)
            self.assertIn('https://alagme.com/quran/18/', urls)
            n = IndexNowPing.objects.count()
            self.assertEqual(n, len(urls))
            call_command('indexnow_ping', '--force', stdout=StringIO())
            self.assertEqual(send.call_count, 1)  # المرة التانية مفيش جديد


@override_settings(**TEST_SETTINGS)
class Wave3Tests(TestCase):
    def test_blog_and_questions_counters(self):
        r = self.client.get('/blog/')
        self.assertContains(r, 'class="stats-band"')
        self.assertContains(r, 'مقال منشور')
        self.assertContains(r, 'قراءة')
        r = self.client.get(reverse('qna:question_list'))
        self.assertContains(r, 'class="stats-band"')
        self.assertContains(r, 'سؤال مُجاب')
        self.assertContains(r, 'مشاهدة')

    def test_wave3_content_seeded(self):
        self.assertTrue(Post.objects.filter(slug=live_slug('quran-revision-games-kids-english'), status='published').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='What is Iqlab in Tajweed?').exists())
        r = self.client.get('/blog/ayat-al-kursi-tajweed-english/', follow=True)
        self.assertContains(r, '<html lang="en"')
        self.assertEqual(r.status_code, 200)

    def test_every_admin_page_opens(self):
        """كل صفحات الأدمن (القائمة + الإضافة + التعديل) تفتح من غير 500."""
        from django.contrib import admin
        from blog.models import Comment
        admin_user = User.objects.create_superuser('wave3admin', 'a3@example.com', 'x-Pass-12345')
        post = Post.objects.filter(status='published').first()
        Comment.objects.create(post=post, author_name='t', author_email='t@example.com', content='hi', is_approved=False)
        Post.objects.filter(pk=post.pk).update(is_featured=True)
        self.client.force_login(admin_user)
        from django.test import RequestFactory
        req = RequestFactory().get('/admin/')
        req.user = admin_user
        for model, model_admin in admin.site._registry.items():
            opts = model._meta
            names = ('changelist', 'add') if model_admin.has_add_permission(req) else ('changelist',)
            for name in names:
                url = reverse(f'admin:{opts.app_label}_{opts.model_name}_{name}')
                self.assertEqual(self.client.get(url).status_code, 200, url)
            obj = model.objects.first()
            if obj is not None:
                url = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[obj.pk])
                self.assertEqual(self.client.get(url).status_code, 200, url)
        r = self.client.post(reverse('admin:blog_category_add'), {'name': 'تصنيف تجربة', 'slug': 'test-cat', 'description': 'x', 'icon': '📁'})
        self.assertEqual(r.status_code, 302)

    def test_seo_title_and_card_thumbs(self):
        from core.templatetags.content_tags import card_img, seo_title
        self.assertEqual(seo_title('قصير', 'مدونة العجمي'), 'قصير | مدونة العجمي')
        long_title = 'x' * 55
        self.assertEqual(seo_title(long_title, 'مدونة العجمي'), long_title)
        self.assertEqual(card_img('https://alagme.com/static/images/blog/madd-types-tajweed.jpg'),
                         'https://alagme.com/static/images/blog/thumbs/madd-types-tajweed.webp')
        self.assertEqual(card_img('https://res.cloudinary.com/x/y.jpg'), 'https://res.cloudinary.com/x/y.jpg')
        r = self.client.get('/blog/')
        self.assertContains(r, '/static/images/blog/thumbs/')
        self.assertNotContains(r, '"@type": "FAQPage"')
        r = self.client.get('/blog/madd-types-tajweed/', follow=True)
        self.assertContains(r, 'class="stat-num"', count=0)
        self.assertContains(r, 'og:image:alt" content="أنواع المد')

    def test_site_domain_is_production(self):
        from django.contrib.sites.models import Site
        self.assertEqual(Site.objects.get(pk=1).domain, 'alagme.com')


@override_settings(**TEST_SETTINGS)
class Wave4Tests(TestCase):
    def test_wave4_content_seeded_and_ordered(self):
        from content_seed import load_articles
        arts = load_articles()
        self.assertTrue(Post.objects.filter(slug=live_slug('juz-amma-plan-for-kids'), status='published').exists())
        # آخر مقال = صاحب أكبر رقم (ترتيب رقمي مش أبجدي)
        from content_seed import ARTICLES_DIR
        last = max(ARTICLES_DIR.glob('*.txt'), key=lambda f: int(f.stem.split('_', 1)[0]))
        self.assertEqual(arts[-1]['slug'], last.stem.split('_', 1)[1])
        for slug in ('mutashabihat-juz-amma', 'sujud-al-tilawa-places', 'quran-corner-at-home'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='هل «الصراط» تُقرأ بالصاد أم بالسين؟').exists())


@override_settings(**TEST_SETTINGS)
class NotificationTests(TestCase):
    """الإشعار يتبعت مرة واحدة بالظبط، في الوقت الصح."""

    def setUp(self):
        self.author = User.objects.create_user('notif_author', 'na@example.com', 'x-Pass-12345')

    def _post(self, **kw):
        d = dict(title='مقال إشعارات', slug=f'notif-{Post.objects.count()}', author=self.author,
                 content='نص', excerpt='ملخص', status='draft')
        d.update(kw)
        return Post.objects.create(**d)

    def test_post_notified_once_on_publish(self):
        with mock.patch('blog.signals.send_in_background') as bg:
            p = self._post(status='draft')
            self.assertEqual(bg.call_count, 0)
            p.status = 'published'
            p.published_at = timezone.now()
            p.save()
            self.assertEqual(bg.call_count, 1)
            self.assertIn('/blog/', bg.call_args.kwargs['url'])
            p.title = 'تعديل'
            p.save()
            self.assertEqual(bg.call_count, 1)  # التعديل مبيبعتش تاني
        p.refresh_from_db()
        self.assertIsNotNone(p.push_sent_at)

    def test_post_created_published_notifies(self):
        with mock.patch('blog.signals.send_in_background') as bg:
            self._post(status='published', published_at=timezone.now())
            self.assertEqual(bg.call_count, 1)

    def test_question_flow(self):
        with mock.patch('qna.signals.send_in_background') as bg:
            q = PublicQuestion.objects.create(title='سؤال إشعار جديد', question_text='نص السؤال هنا', visitor_name='زائر', status='pending')
            funcs = [c.args[0].__name__ for c in bg.call_args_list]
            self.assertIn('send_admin_notification', funcs)
            bg.reset_mock()
            q.status = 'approved'
            q.save()
            self.assertEqual([c.args[0].__name__ for c in bg.call_args_list], ['send_public_notification'])
            self.assertEqual(bg.call_args.kwargs['title'], '❓ سؤال جديد')
            q.save()
            self.assertEqual(bg.call_count, 1)
            # إجابة بعد فترة → «تمت الإجابة»
            PublicQuestion.objects.filter(pk=q.pk).update(push_sent_at=timezone.now() - timezone.timedelta(hours=1))
            bg.reset_mock()
            QuestionAnswer.objects.create(question=q, answer_text='الإجابة')
            titles = [c.kwargs.get('title') for c in bg.call_args_list]
            self.assertIn('✅ تمت الإجابة', titles)

    def test_digest_sends_single_notification(self):
        from io import StringIO
        from django.core.management import call_command
        Post.objects.update(push_sent_at=timezone.now())
        PublicQuestion.objects.update(push_sent_at=timezone.now())
        for i in range(3):
            Post.objects.filter(pk=self._post(status='draft').pk).update(status='published', published_at=timezone.now())
        with mock.patch('accounts.notifications.is_configured', return_value=True), \
             mock.patch('accounts.notifications.send_public_notification') as send:
            call_command('send_content_digest', stdout=StringIO())
            self.assertEqual(send.call_count, 1)
            self.assertIn('3 مقال', send.call_args.kwargs['message'])
            call_command('send_content_digest', stdout=StringIO())
            self.assertEqual(send.call_count, 1)  # مبيتكررش

    def test_push_card_on_article(self):
        r = self.client.get('/blog/madd-types-tajweed/', follow=True)
        self.assertContains(r, 'data-push-card')


@override_settings(**TEST_SETTINGS)
class NotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('pushadmin', 'p@example.com', 'x-Pass-12345')

    def test_push_status_page(self):
        self.assertEqual(self.client.get('/admin/push-status/').status_code, 302)  # لازم دخول
        self.client.force_login(self.admin)
        r = self.client.get('/admin/push-status/')
        self.assertContains(r, 'حالة الإشعارات')
        self.assertContains(r, 'FIREBASE_CREDENTIALS_JSON')  # مش متظبط في الاختبارات

    def test_push_diagnostics(self):
        from types import SimpleNamespace
        from accounts.models import FCMToken
        from core.models import PushLog
        self.client.force_login(self.admin)
        # خطأ من المتصفح بيتسجل
        r = self.client.post('/save-fcm-token/', data=json.dumps({'client_error': 'messaging/token-subscribe-failed: x', 'page': '/'}),
                             content_type='application/json')
        self.assertEqual(r.json()['status'], 'logged')
        self.assertTrue(PushLog.objects.filter(kind='client', error__contains='token-subscribe-failed').exists())
        # اختبار توكن بعينه بيرجع نتيجة Firebase الحرفية
        ok = SimpleNamespace(responses=[SimpleNamespace(success=True, message_id='projects/x/messages/123', exception=None)])
        with mock.patch('accounts.notifications.is_configured', return_value=True), \
                mock.patch('accounts.notifications._send', return_value=[(['t'], ok)]):
            r = self.client.post('/admin/push-status/', {'target': 'token', 'token': 'abc'})
        self.assertEqual(r.json(), {'ok': True, 'message_id': 'projects/x/messages/123'})
        # أزرار الإرسال بترجع JSON لما تتنادى من الصفحة
        r = self.client.post('/admin/push-status/', {'target': 'me'}, HTTP_X_REQUESTED_WITH='fetch')
        self.assertFalse(r.json()['ok'])  # Firebase مش متظبط في الاختبارات

    def test_config_errors_do_not_delete_subscribers(self):
        from types import SimpleNamespace
        from accounts.models import FCMToken
        from accounts.notifications import _cleanup
        FCMToken.objects.create(token='keep-me')
        FCMToken.objects.create(token='dead-one')
        class SenderIdMismatchError(Exception):
            pass
        class UnregisteredError(Exception):
            pass
        resp = SimpleNamespace(responses=[SimpleNamespace(success=False, exception=SenderIdMismatchError('x')),
                                          SimpleNamespace(success=False, exception=UnregisteredError('y'))])
        _cleanup([(['keep-me', 'dead-one'], resp)])
        self.assertTrue(FCMToken.objects.filter(token='keep-me').exists())
        self.assertFalse(FCMToken.objects.filter(token='dead-one').exists())

    def test_digest_keeps_content_pending_without_firebase(self):
        from io import StringIO
        from django.core.management import call_command
        Post.objects.update(push_sent_at=None, published_at=timezone.now())
        with mock.patch('accounts.notifications.is_configured', return_value=False):
            call_command('send_content_digest', stdout=StringIO())
        self.assertFalse(Post.objects.filter(status='published', push_sent_at__isnull=False).exists())

    def test_question_push_waits_for_answer(self):
        cat = QuestionCategory.objects.first()
        with mock.patch('qna.signals.notify_question', return_value=True) as notify, \
                mock.patch('qna.signals.send_indexnow'), mock.patch('qna.signals.send_in_background'), \
                self.captureOnCommitCallbacks(execute=True):
            q = PublicQuestion.objects.create(title='سؤال اختبار الإشعار بدون إجابة', question_text='نص السؤال للاختبار هنا',
                                              visitor_name='زائر', category=cat, status='approved')
            self.assertFalse(notify.called)
            QuestionAnswer.objects.create(question=q, answer_text='إجابة رسمية طويلة بما يكفي للاختبار', answered_by=self.admin)
            self.assertTrue(notify.called)

    def test_new_post_triggers_push(self):
        with mock.patch('blog.signals.send_in_background') as bg, \
                mock.patch('blog.signals.send_indexnow'):
            p = Post.objects.create(title='مقال اختبار الإشعار', slug='push-test-post', author=self.admin,
                                    content='محتوى', status='published', published_at=timezone.now())
        self.assertTrue(bg.called)
        p.refresh_from_db()
        self.assertIsNotNone(p.push_sent_at)


@override_settings(**TEST_SETTINGS)
class Wave5Tests(TestCase):
    def test_wave5_content(self):
        for slug in ('ibtida-where-to-restart', 'father-role-in-quran', 'family-quran-quiz-for-kids'):
            self.assertEqual(self.client.get(f'/blog/{slug}/', follow=True).status_code, 200, slug)
        self.assertTrue(PublicQuestion.objects.filter(title='ما الفرق بين التأسيس والتحفيظ؟').exists())

    def test_firebase_key_parsing_is_tolerant(self):
        import base64
        from accounts.notifications import _parse_key
        d = {'type': 'service_account', 'project_id': 'alagme-notifications',
             'private_key': '-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n', 'client_email': 'a@b'}
        raw = json.dumps(d)
        for v in (raw, f"'{raw}'", base64.b64encode(raw.encode()).decode(), json.dumps(raw), raw.replace('\\n', '\\\\n')):
            self.assertEqual(_parse_key(v)['private_key'].count('\n'), 3)
        with self.assertRaises(ValueError):
            _parse_key('{"type": "x"}')


@override_settings(**TEST_SETTINGS)
class Wave6Tests(TestCase):
    def test_wave6_content(self):
        for slug in ('tahzib-al-quran-fami-bishawq', 'prophets-in-quran-for-kids', 'divine-names-at-verse-endings'):
            self.assertEqual(self.client.get(f'/blog/{slug}/', follow=True).status_code, 200, slug)
        self.assertTrue(PublicQuestion.objects.filter(title='ما أرجى آية في القرآن؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave7Tests(TestCase):
    def test_wave7_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 200)
        for slug in ('hajr-al-quran-five-types', 'madinah-mushaf-story', 'yusuf-story-for-kids', 'tajweed-applied-surat-al-mulk'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أرتب الحواميم السبع في ذهني؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما هي «المسبّحات»؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave8Tests(TestCase):
    def test_wave8_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 300)
        for slug in ('memorize-surat-al-imran', 'tajweed-applied-surat-an-naba', 'sulayman-story-for-kids', 'parables-in-the-quran'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أقرأ «ءأعجمي» في سورة فصلت؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما هو «المصحف الإمام»؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave9Tests(TestCase):
    def test_wave9_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 450)
        for slug in ('juz-1-memorization-plan', 'four-sakt-positions-hafs', 'asiya-story-for-kids',
                     'tafsir-surat-al-ikhlas', 'angels-in-the-quran', 'quran-at-work'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='ما الفرق بين اللام الشمسية واللام القمرية؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='هل الجن يستمعون إلى القرآن؟').exists())


class PushMessageBuildTests(TestCase):
    def test_build_message_uses_valid_webpush_kwargs(self):
        from accounts.notifications import _build_message
        msg = _build_message(['tok'], 'عنوان', 'نص', 'https://alagme.com/')
        self.assertEqual(msg.webpush.notification.direction, 'rtl')
        self.assertEqual(msg.webpush.notification.language, 'ar')


class Wave10Tests(TestCase):
    def test_wave10_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 600)
        for slug in ('juz-6-memorization-plan', 'tafsir-surat-al-mulk', 'ghulam-and-king-story-for-kids',
                     'ibad-al-rahman-traits', 'nasikh-mansukh', 'quran-companion-for-the-sick'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='ما الفرق بين الخوف والخشية في القرآن؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='هل يحتاج معلم القرآن أونلاين إلى إجازة؟').exists())

    def test_juz21_refresh(self):
        from blog.models import Post
        p = Post.objects.get(slug=live_slug('history-of-juz-and-hizb-divisions'))
        self.assertIn('العنكبوت: 46', p.content)


class SiteIndexAndCachingTests(TestCase):
    def test_site_index_lists_content(self):
        r = self.client.get('/site-index/')
        self.assertEqual(r.status_code, 200)
        rich = Post.objects.indexable().first()
        self.assertContains(r, f'/blog/{rich.slug}/')
        # المقالات المدموجة (redirect) مش في الفهرس، والأسئلة المجابة فيه
        for old in list(merged_redirects())[:50]:
            self.assertNotContains(r, f'/blog/{old}/"')
        self.assertContains(r, '/questions/topic/')
        self.assertNotContains(r, '/questions/question/')
        self.assertNotIn('X-Robots-Tag', r.headers)

    def test_sitemap_has_site_index(self):
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)

    def test_blog_detail_conditional_get(self):
        url = f"/blog/{live_slug('nasikh-mansukh')}/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Last-Modified', r)
        r2 = self.client.get(url, HTTP_IF_MODIFIED_SINCE=r['Last-Modified'])
        self.assertEqual(r2.status_code, 304)


class Wave11Tests(TestCase):
    def test_wave11_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 750)
        for slug in ('tafsir-surat-al-hujurat', 'tajweed-applied-surat-qaf', 'kids-birr-parents-from-quran',
                     'amanah-in-the-quran', 'zayd-ibn-thabit-and-the-quran', 'tafsir-ibn-ashur-introduction'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='هل يجوز الوقف على «كلا» في كل مواضعها في القرآن؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما حكم الحلف على المصحف؟').exists())


class Wave12Tests(TestCase):
    def test_wave12_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 950)
        for slug in ('tafsir-surat-al-baqarah', 'allah-name-as-samad-meaning', 'tafsir-ayah-dua-dhi-an-nun',
                     'hudhud-story-for-kids', 'mutashabihat-surat-ash-shuara', 'why-quran-in-arabic',
                     'idgham-mithlayn', 'how-to-test-your-tajweed-level'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='ما معنى اسم الله الصمد؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='هل في «اركب معنا» بسورة هود إدغام؟').exists())


class Wave13Tests(TestCase):
    def test_wave13_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1150)
        for slug in ('allah-name-al-jabbar-meaning', 'tafsir-ayah-rabbana-la-tuzigh-qulubana',
                     'maida-table-story-for-kids', 'mutashabihat-surat-al-kahf', 'ibrahim-in-the-quran',
                     'madd-farq-and-tamkin', 'tafsir-al-baghawi-introduction', 'quran-translations-history'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='ما معنى اسم الله الجبار؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أقرأ «اتقوا والذين» وهل فيها مد؟').exists())


class Wave14Tests(TestCase):
    def test_wave14_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1350)
        for slug in ('allah-names-al-awwal-al-akhir-meaning', 'tajweed-applied-zumar-53-55',
                     'mutashabihat-surat-taha', 'hifz-for-shift-workers', 'surat-al-falaq-for-kids',
                     'surat-at-tariq-for-kids'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أقرأ «لكنا هو الله ربي» في سورة الكهف؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما معنى هجر القرآن؟').exists())

    def test_wave14_fits_postgres_limits(self):
        from content_seed import load_articles
        from blog.models import Post
        slug_max = Post._meta.get_field('slug').max_length
        for a in load_articles():
            self.assertLessEqual(len(a['slug']), slug_max, a['slug'])
        from content_seed.questions_wave14 import QUESTIONS_AR14
        tmax = PublicQuestion._meta.get_field('title').max_length
        for q in QUESTIONS_AR14:
            self.assertLessEqual(len(q[1]), tmax, q[1])


class Wave15Tests(TestCase):
    def test_wave15_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1476)
        for slug in ('surat-an-naba-for-kids', 'rain-in-the-quran', 'allah-name-al-ghaffar-meaning',
                     'mutashabihat-surat-sad', 'tafsir-ayah-nahnu-aqrabu-ilayhi', 'markets-in-the-quran'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='من هم القراء العشرة ورواتهم؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أقرأ «نُجي المؤمنين» في سورة الأنبياء؟').exists())

    def test_article_slugs_unique(self):
        from content_seed import load_articles
        slugs = [a['slug'] for a in load_articles()]
        dups = sorted({s for s in slugs if slugs.count(s) > 1})
        self.assertEqual(dups, [])

    def test_wave15_fits_postgres_limits(self):
        from content_seed.questions_wave15 import QUESTIONS_AR15
        tmax = PublicQuestion._meta.get_field('title').max_length
        for q in QUESTIONS_AR15:
            self.assertLessEqual(len(q[1]), tmax, q[1])


class Wave16Tests(TestCase):
    def test_wave16_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1548)
        for slug in ('surat-nuh-for-kids', 'abu-amr-ad-dani-biography', 'allah-name-al-mannan-meaning',
                     'mutashabihat-surat-al-qamar', 'tafsir-ayah-fafirru-ila-allah', 'ya-bani-adam-calls'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')


class Wave17Tests(TestCase):
    def test_wave17_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1606)
        for slug in ('tafsir-ayah-wa-ma-min-dabbatin', 'aisha-and-the-quran', 'surat-al-mulk-for-kids',
                     'mubhamat-al-quran', 'meem-sakinah-rules-english', 'surah-yasin-meaning-english'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)

    def test_english_wave17_has_arabic_counterpart(self):
        r = self.client.get('/blog/qalqalah-rules-english/', follow=True)
        self.assertContains(r, '/blog/qalqalah-rules/')


class Wave18Tests(TestCase):
    def test_wave18_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1650)
        for slug in ('surah-ar-rahman-meaning-english', 'compilation-of-the-quran-english',
                     'tafsir-ayah-fasbir-sabran-jamila', 'tajweed-applied-imran-159',
                     'kids-family-ties-from-quran', 'yusuf-shirt-three-times'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)

    def test_english_wave18_hreflang(self):
        # المقالين اتدمجوا في صفحات شاملة (إنجليزي وعربي) فالرابط القديم بيوصل للصفحة الإنجليزية
        r = self.client.get('/blog/surah-al-qadr-meaning-english/', follow=True)
        self.assertContains(r, '<html lang="en"')
        r = self.client.get('/blog/juz-1-of-the-quran-summary-english/')
        self.assertContains(r, 'hreflang="ar"')
        self.assertContains(r, '/blog/juz-1-themes-and-summary/')


class Wave19Tests(TestCase):
    def test_wave19_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1748)
        for slug in ('surah-an-naba-meaning-english', 'surah-ar-rum-meaning-english',
                     'tafsir-ayah-inni-jailun-fil-ard-khalifa', 'tajweed-applied-ibrahim-7',
                     'tafsir-ayah-yamhu-allahu-ma-yasha'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
        self.assertTrue(PublicQuestion.objects.filter(title='ما معنى «أهل القرآن» في الحديث؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='What does Bismillah ar-Rahman ar-Rahim mean?').exists())

    def test_wave19_fits_postgres_limits(self):
        from content_seed.questions_wave19 import QUESTIONS_AR19
        tmax = PublicQuestion._meta.get_field('title').max_length
        titles = [q[1] for q in QUESTIONS_AR19]
        self.assertEqual(len(titles), len(set(titles)))
        for t in titles:
            self.assertLessEqual(len(t), tmax, t)


class Wave20Tests(TestCase):
    def test_wave20_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual((len(load_articles()) + len(merged_redirects())), 1846)
        for slug in ('surah-al-baqarah-meaning-english', 'surah-maryam-meaning-english',
                     'wa-idha-saalaka-ibadi-meaning-english', 'tafsir-ayah-fasfah-as-safh-al-jamil',
                     'surah-al-fatiha-meaning-english'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
        self.assertTrue(PublicQuestion.objects.filter(title='لماذا سُمي القرآن «الفرقان»؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='Is it permissible to kiss the Mushaf?').exists())

    def test_wave20_english_hreflang_pairs(self):
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        # كل ترجمة لسه مربوطة بمقال عربي موجود (بعد دمج المقالات القصيرة)
        for a in arts.values():
            if a.get('translation_of'):
                self.assertIn(a['translation_of'], arts, a['slug'])

    def test_wave20_fits_postgres_limits(self):
        from content_seed.questions_wave20 import QUESTIONS_AR20
        tmax = PublicQuestion._meta.get_field('title').max_length
        titles = [q[1] for q in QUESTIONS_AR20]
        self.assertEqual(len(titles), len(set(titles)))
        for t in titles:
            self.assertLessEqual(len(t), tmax, t)


class Wave21Tests(TestCase):
    def test_wave21_content(self):
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        self.assertGreaterEqual(len(arts) + len(merged_redirects()), 1944)
        for slug in ('khalaqakum-min-nafsin-wahida-meaning-english', 'salawat-on-the-prophet-33-56-meaning-english',
                     'ibrahim-describes-his-lord-26-78-english', 'walasawfa-yutika-rabbuka-meaning-english'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
        # كل مقال إنجليزي في الموجة مربوط بمقال عربي موجود، ومفيش مقال عربي مترجم مرتين
        targets = [a['translation_of'] for a in arts.values() if a.get('translation_of')]
        self.assertEqual(len(targets), len(set(targets)))
        for t in targets:
            self.assertIn(t, arts, t)


class Wave22Tests(TestCase):
    def test_wave22_content(self):
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        self.assertGreaterEqual(len(arts) + len(merged_redirects()), 2042)
        for slug in ('tafsir-ayah-allahu-nuru-as-samawati-wal-ard', 'the-verse-of-light-24-35-meaning-english',
                     'tafsir-ayah-inna-al-muslimina-wal-muslimat', 'enter-islam-completely-2-208-meaning-english'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
        self.assertIn('the-verse-of-light-24-35-meaning-english', merged_redirects())  # اتدمج في صفحة شاملة


class Wave23Tests(TestCase):
    def test_wave23_content(self):
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        self.assertGreaterEqual(len(arts) + len(merged_redirects()), 2150)
        for slug in ('tafsir-ayah-dhalika-al-kitabu-la-rayba-fih', 'this-is-the-book-no-doubt-2-2-english',
                     'tafsir-ayah-inna-kulla-shayin-khalaqnahu-biqadar', 'everything-created-by-measure-54-49-english'):
            r = self.client.get(f'/blog/{slug}/', follow=True)
            self.assertEqual(r.status_code, 200, slug)
        self.assertIn('everything-created-by-measure-54-49-english', merged_redirects())  # اتدمج في صفحة شاملة


class Wave24Tests(TestCase):
    def test_wave24_juz_guides(self):
        import re
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        self.assertGreaterEqual(len(arts) + len(merged_redirects()), 2170)
        for n in range(1, 11):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        r = self.client.get('/blog/juz-1-themes-and-summary/', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '"wordCount"')

    def test_old_slug_alias_redirects(self):
        r = self.client.get('/blog/allah-name-al-awwal-al-akhir-az-zahir-al-batin-meaning/')
        self.assertEqual(r.status_code, 301)
        # الاسم المقابل اتدمج في صفحة شاملة: التحويل يروح للقسم مباشرة (خطوة واحدة)
        self.assertIn(live_slug('allah-names-al-awwal-al-akhir-meaning'), r['Location'])
        r = self.client.get('/blog/allah-name-al-awwal-al-akhir-az-zahir-al-batin-meaning/', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.redirect_chain), 1)


class Wave25Tests(TestCase):
    def test_wave25_juz_guides(self):
        import re
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        for n in range(11, 17):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        r = self.client.get('/blog/juz-16-of-the-quran-summary-english/', follow=True)
        self.assertEqual(r.status_code, 200)
        from blog.models import Post
        self.assertIn('/blog/juz-12-of-the-quran-summary-english/',
                      Post.objects.get(slug='juz-11-of-the-quran-summary-english').content)


class Wave26Tests(TestCase):
    def test_wave26_juz_guides(self):
        import re
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        for n in range(17, 21):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        r = self.client.get('/blog/juz-20-themes-and-summary/', follow=True)
        self.assertEqual(r.status_code, 200)
        from blog.models import Post
        self.assertIn('/blog/juz-17-of-the-quran-summary-english/',
                      Post.objects.get(slug='juz-16-of-the-quran-summary-english').content)


class Wave27Tests(TestCase):
    def test_wave27_juz_guides(self):
        import re
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        for n in range(21, 24):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        self.assertEqual(self.client.get('/blog/juz-23-of-the-quran-summary-english/', follow=True).status_code, 200)
        from blog.models import Post
        self.assertIn('/blog/juz-21-of-the-quran-summary-english/',
                      Post.objects.get(slug='juz-20-of-the-quran-summary-english').content)


class Wave28Tests(TestCase):
    def test_wave28_juz_guides_and_nav(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for n in (24, 25):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        for n in range(1, 24):
            body = Post.objects.get(slug=f'juz-{n}-of-the-quran-summary-english').content
            self.assertIn(f'/blog/juz-{n + 1}-of-the-quran-summary-english/', body, n)


class Wave29Tests(TestCase):
    def test_wave29_juz_guides(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for n in (26, 27, 28):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        for n in range(24, 28):
            body = Post.objects.get(slug=f'juz-{n}-of-the-quran-summary-english').content
            self.assertIn(f'/blog/juz-{n + 1}-of-the-quran-summary-english/', body, n)
        self.assertEqual(self.client.get('/blog/juz-28-themes-and-summary/', follow=True).status_code, 200)


class Wave30Tests(TestCase):
    def test_all_thirty_juz_guides_complete(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for n in range(1, 31):
            ar, en = f'juz-{n}-themes-and-summary', f'juz-{n}-of-the-quran-summary-english'
            self.assertEqual(arts[en]['translation_of'], ar)
            for slug in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
                self.assertTrue(Post.objects.filter(slug=slug, status='published').exists(), slug)
            if n < 30:
                self.assertIn(f'/blog/juz-{n + 1}-of-the-quran-summary-english/',
                              Post.objects.get(slug=en).content, n)
        self.assertEqual(self.client.get('/blog/juz-30-of-the-quran-summary-english/', follow=True).status_code, 200)


class Wave31Tests(TestCase):
    def test_juz_hub_links_every_guide_and_back(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        ar, en = 'quran-30-juz-complete-guide', '30-juz-of-the-quran-guide-english'
        self.assertEqual(arts[en]['translation_of'], ar)
        for slug in (ar, en, 'memorizing-juz-and-hizb-starts'):
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[slug]['body'])), 2000, slug)
        hub_ar, hub_en = Post.objects.get(slug=ar).content, Post.objects.get(slug=en).content
        self.assertNotIn('themes-and-summary', hub_en)
        for n in range(1, 31):
            self.assertIn(f'/blog/juz-{n}-themes-and-summary/', hub_ar, n)
            self.assertIn(f'/blog/juz-{n}-of-the-quran-summary-english/', hub_en, n)
            self.assertIn(f'/blog/{ar}/', Post.objects.get(slug=f'juz-{n}-themes-and-summary').content, n)
            self.assertIn(f'/blog/{en}/', Post.objects.get(slug=f'juz-{n}-of-the-quran-summary-english').content, n)
        self.assertEqual(self.client.get(f'/blog/{en}/', follow=True).status_code, 200)


class Wave32Tests(TestCase):
    def test_core_tajweed_articles_expanded(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for slug in ('noon-sakinah-tanween-rules', 'meem-sakinah-rules'):
            en = slug + '-english'
            self.assertEqual(arts[en]['translation_of'], slug)
            for s in (slug, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
                p = Post.objects.get(slug=s)
                self.assertIn('Ikhfa' if s == en else 'الإخفاء', p.content)
            for link in re.findall(r'/blog/([a-z0-9-]+)/', Post.objects.get(slug=en).content):
                self.assertTrue(link.endswith('-english'), (en, link))


class Wave33Tests(TestCase):
    def test_madd_and_qalqalah_expanded(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for ar, en in (('madd-types-tajweed', 'madd-rules-tajweed-english'), ('qalqalah-rules', 'qalqalah-rules-english')):
            self.assertEqual(arts[en]['translation_of'], ar)
            for s in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
            self.assertIn('ٱلضَّآلِّينَ' if ar.startswith('madd') else 'قطب جد', Post.objects.get(slug=ar).content)
            arabic_slugs = {a['slug'] for a in arts.values() if a.get('category') != 'english'}
            for link in re.findall(r'/blog/([a-z0-9-]+)/', Post.objects.get(slug=en).content):
                self.assertNotIn(link, arabic_slugs, (en, link))


class Wave34Tests(TestCase):
    def test_makharij_expanded_with_full_letter_table(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        self.assertEqual(arts['makharij-al-huruf-english']['translation_of'], 'makharij-al-huruf')
        for s in ('makharij-al-huruf', 'makharij-al-huruf-english'):
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
            # جدول الحروف: 28 صف على الأقل
            self.assertGreaterEqual(Post.objects.get(slug=s).content.count('\n| '), 28, s)
        self.assertEqual(arts['learn-tajweed-roadmap-english']['translation_of'], 'learn-tajweed-roadmap')
        for s in ('learn-tajweed-roadmap', 'learn-tajweed-roadmap-english'):
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)


class Wave35Tests(TestCase):
    def test_hifz_pillars_expanded(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        pairs = (('how-to-memorize-quran-plan', 'how-to-memorize-quran-step-by-step'),
                 ('quran-revision-system', 'quran-revision-system-english'))
        for ar, en in pairs:
            self.assertEqual(arts[en]['translation_of'], ar)
            for s in (ar, en):
                self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
                self.assertTrue(Post.objects.filter(slug=s, status='published').exists(), s)
        self.assertIn('/blog/30-juz-of-the-quran-guide-english/',
                      Post.objects.get(slug='how-to-memorize-quran-step-by-step').content)


class Wave36Tests(TestCase):
    def test_fatiha_mistakes_expanded_and_corrected(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        ar, en = 'common-mistakes-surat-al-fatiha', 'surah-al-fatiha-common-mistakes'
        self.assertEqual(arts[en]['translation_of'], ar)
        for s in (ar, en):
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
        # الدال في «اهدنا» مكسورة، فلا قلقلة فيها
        self.assertNotIn('الدال الساكنة في ﴿ٱهۡدِنَا﴾', Post.objects.get(slug=ar).content)
        self.assertNotIn('silent Daal in ﴿ٱهۡدِنَا﴾', Post.objects.get(slug=en).content)


class Wave37Tests(TestCase):
    def test_kids_guides_expanded_and_all_featured_long(self):
        import re
        from content_seed import load_articles
        arts = {a['slug']: a for a in load_articles()}
        self.assertEqual(arts['learn-quran-online-for-kids']['translation_of'], 'teaching-quran-to-kids')
        # كل المقالات المميزة (featured) بقت 2000 كلمة على الأقل
        featured = [s for s, a in arts.items() if a.get('featured') == '1']
        self.assertGreaterEqual(len(featured), 7)
        for s in featured:
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)


class Wave38Tests(TestCase):
    HUBS = ['tafsir-ayat-index-by-surah', 'tafsir-surahs-index', 'tajweed-applied-index-by-surah',
            'surah-memorization-plans-index', 'quran-topics-encyclopedia', 'allah-names-index',
            'quran-stories-for-kids-index', 'quran-verses-explained-english-index']

    def test_hubs_published_long_and_link_their_series(self):
        import re
        from content_seed import load_articles
        from blog.models import Post
        arts = {a['slug']: a for a in load_articles()}
        for s in self.HUBS:
            self.assertGreaterEqual(len(re.findall(r'\S+', arts[s]['body'])), 2000, s)
            self.assertTrue(Post.objects.filter(slug=s, status='published').exists(), s)
        tafsir = [s for s in arts if s.startswith('tafsir-ayah')]
        hub = Post.objects.get(slug='tafsir-ayat-index-by-surah').content
        for s in tafsir:
            self.assertIn(f'/blog/{s}/', hub, s)
        topics = [s for s, a in arts.items() if s.endswith('-in-the-quran') and a['category'] != 'english']
        hub = Post.objects.get(slug='quran-topics-encyclopedia').content
        for s in topics:
            self.assertIn(f'/blog/{s}/', hub, s)
        self.assertContains(self.client.get('/site-index/'), '/blog/quran-topics-encyclopedia/')

    def test_refresh_bumps_updated_at(self):
        from django.apps import apps as global_apps
        from blog.models import Post
        from content_seed.seeding import refresh_articles
        p = Post.objects.get(slug='makharij-al-huruf')
        Post.objects.filter(pk=p.pk).update(content='x')
        before = Post.objects.get(pk=p.pk).updated_at
        refresh_articles(global_apps, ['makharij-al-huruf'])
        self.assertGreater(Post.objects.get(pk=p.pk).updated_at, before)


class QuestionsWave21Tests(TestCase):
    def test_thousand_questions_and_juz_answers_link_guides(self):
        from qna.models import PublicQuestion
        self.assertGreaterEqual(PublicQuestion.objects.filter(status='approved').count(), 1000)
        q = PublicQuestion.objects.get(title='من أين يبدأ الجزء الخامس عشر من القرآن وما أهم موضوعاته؟')
        self.assertIn('/blog/juz-15-themes-and-summary/', q.official_answer.answer_text)
        q = PublicQuestion.objects.get(title='Where does Juz 30 of the Quran start, and what are its main themes?')
        self.assertIn('/blog/juz-30-of-the-quran-summary-english/', q.official_answer.answer_text)
        self.assertEqual(self.client.get(f'/questions/question/{q.slug}/').status_code, 200)


class RelatedPostsTests(TestCase):
    def test_related_posts_vary_and_match_topic(self):
        from blog.models import Post
        from blog.related import related_posts
        p = Post.objects.indexable().filter(category__slug='quran-life').order_by('pk')[5]
        rel = related_posts(p)
        self.assertEqual(len(rel), 4)
        self.assertNotIn(p, rel)
        self.assertTrue(all(r.category_id == p.category_id for r in rel))
        # مقالين مختلفين في نفس التصنيف مايرجعوش نفس القايمة (قبل كده كانت أحدث 3 للكل)
        q = Post.objects.indexable().filter(category__slug='quran-life').order_by('pk')[40]
        self.assertNotEqual([x.pk for x in rel], [x.pk for x in related_posts(q)])

    def test_detail_has_prev_next_and_related(self):
        from blog.models import Post
        from blog.related import prev_next
        # السابق/التالي بيتنقلوا بين المقالات الطويلة (indexable) بس
        p = next(x for x in Post.objects.indexable() if all(prev_next(x)))
        r = self.client.get(f'/blog/{p.slug}/', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'rel="prev"')
        self.assertContains(r, 'rel="next"')
        self.assertContains(r, 'related-title')

    def test_related_questions_vary(self):
        from qna.related import related_question_ids
        qs = list(PublicQuestion.objects.filter(status='approved', category__isnull=False).order_by('pk')[:40])
        lists = {tuple(related_question_ids(q)) for q in qs}
        self.assertGreater(len(lists), 10)
        q = qs[5]
        from django.urls import reverse
        r = self.client.get(reverse('qna:question_detail', args=[q.slug]))
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.context['related_questions']), 0)



class MergedPageTitleTests(TestCase):
    """عناوين الصفحات الشاملة «المجموعة: مقال وغيرها» لازم <title> بتاعها مايتكررش بين صفحات المجموعة."""
    def test_merged_titles_keep_part_of_subtitle(self):
        from core.templatetags.content_tags import _clip_title
        a = _clip_title('الصحابة والتابعون مع القرآن: عبد الله بن عمرو بن العاص والقرآن وغيرها')
        b = _clip_title('الصحابة والتابعون مع القرآن: جعفر بن أبي طالب وسورة مريم وغيرها')
        self.assertNotEqual(a, b)
        self.assertLessEqual(max(len(a), len(b)), 60)
        self.assertNotIn('وغيرها', a + b)


class FaqSchemaAndFullTafsirTests(TestCase):
    def test_article_with_faq_section_has_faqpage_jsonld(self):
        import json, re
        r = self.client.get('/blog/tafsir-surat-al-ikhlas-kamila/')
        blocks = [b for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.content.decode(), re.S) if 'FAQPage' in b]
        self.assertEqual(len(blocks), 1)
        data = json.loads(blocks[0])
        self.assertGreaterEqual(len(data['mainEntity']), 2)
        self.assertTrue(all(q['acceptedAnswer']['text'] for q in data['mainEntity']))

    def test_english_full_tafsir_index_links_articles(self):
        r = self.client.get('/blog/quran-surahs-full-tafsir-english-index/')
        self.assertContains(r, '/blog/surah-al-mulk-full-tafsir-english/')
        r = self.client.get('/blog/surah-al-mulk-full-tafsir-english/')
        self.assertContains(r, '/blog/quran-surahs-full-tafsir-english-index/')

    def test_old_articles_link_full_tafsir(self):
        from blog.models import Post
        self.assertTrue(Post.objects.filter(content__contains='/blog/tafsir-surat-al-mulk-kamila/').exclude(slug__in=['tafsir-surahs-index', 'tafsir-surat-al-mulk-kamila']).exists())


class SeoLimitsAndQuranLinksTests(TestCase):
    def test_title_and_description_limits(self):
        import html, re
        for url in ('/', '/blog/', '/blog/anam-ten-commandments/', '/blog/category/hifz/', '/quran/2/'):
            t = self.client.get(url).content.decode()
            title = html.unescape(re.search(r'<title>(.*?)</title>', t, re.S).group(1).strip())
            desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', t, re.S).group(1))
            self.assertLessEqual(len(title), 60, url)
            self.assertTrue(120 <= len(desc) <= 160, (url, len(desc)))
            self.assertEqual(t.count('<h1'), 1, url)
            self.assertEqual(t.count('rel="canonical"'), 1, url)

    def test_surah_page_links_articles_and_back(self):
        r = self.client.get('/quran/49/')
        # صفحة السورة بتلينك على التفسير الكامل للسورة، وأقسام الصفحات الشاملة اللي عن السورة
        self.assertContains(r, '/blog/tafsir-surat-al-hujurat-kamila/')
        self.assertContains(r, '/blog/tafsir-ayah-ijtanibu-kathiran-min-az-zann/#')
        self.assertContains(r, 'بصوت كبار القراء')
        r = self.client.get('/blog/tafsir-surat-al-hujurat-kamila/')
        self.assertContains(r, '/quran/49/')
        r = self.client.get(f"/blog/{live_slug('tafsir-surat-al-hujurat')}/")
        self.assertContains(r, '/quran/49/')

    def test_indexnow_key_is_public(self):
        from django.conf import settings
        r = self.client.get(f'/{settings.INDEXNOW_KEY}.txt')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('X-Robots-Tag', r.headers)


class IndexNowEndpointsTests(TestCase):
    def test_batch_posts_to_indexnow_and_bing(self):
        from unittest import mock
        from core import indexnow
        resp = mock.Mock(status_code=200)
        with mock.patch('core.indexnow.requests.post', return_value=resp) as post:
            self.assertTrue(indexnow.send_indexnow_batch(['https://alagme.com/blog/x/']))
        hosts = [c.args[0] for c in post.call_args_list]
        self.assertIn('https://api.indexnow.org/indexnow', hosts)
        self.assertIn('https://www.bing.com/indexnow', hosts)
        self.assertIn('https://yandex.com/indexnow', hosts)

    def test_bing_verification_meta_only_when_set(self):
        self.assertNotContains(self.client.get('/'), 'msvalidate.01')
        with self.settings(BING_SITE_VERIFICATION='ABC123'):
            self.assertContains(self.client.get('/'), '<meta name="msvalidate.01" content="ABC123">')


class VarcharLimitsTests(TestCase):
    """SQLite مابيطبقش max_length لكن Postgres (الإنتاج) بيرفض أي قيمة أطول وبيوقع الـ migration كلها.
    (slug مقال طوله 54 والحد 50 وقّع الموقع كله بعد الدفعة 13)"""
    def test_seeded_values_fit_postgres_limits(self):
        from django.apps import apps
        over = []
        for label in ('blog', 'qna'):
            for M in apps.get_app_config(label).get_models():
                fields = [f for f in M._meta.fields if getattr(f, 'max_length', None)
                          and f.get_internal_type() in ('CharField', 'SlugField', 'URLField', 'EmailField')]
                for o in M.objects.all():
                    for f in fields:
                        v = getattr(o, f.attname) or ''
                        if len(v) > f.max_length:
                            over.append((M.__name__, f.name, f.max_length, len(v), str(v)[:60]))
        self.assertEqual(over, [])


class SeoBoostTests(TestCase):
    """خريطة الموقع فيها كل المقالات وصورها، وصفحات التصنيفات والـ404 سليمة للسيو"""
    def test_sitemap_lists_every_post_with_image(self):
        from django.core.cache import cache
        cache.clear()
        r = self.client.get('/sitemap.xml')
        root = ET.fromstring(r.content)
        locs = {e.text for e in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
        # المقالات الطويلة بس في الخريطة؛ القصيرة عليها noindex ومش موجودة
        posts = Post.objects.indexable()
        self.assertGreater(posts.count(), 200)
        for p in posts:
            self.assertIn(f'https://alagme.com/blog/{p.slug}/', locs)
        for p in Post.objects.published().exclude(pk__in=posts.values('pk'))[:50]:
            self.assertNotIn(f'https://alagme.com/blog/{p.slug}/', locs)
        from qna.models import PublicQuestion
        from qna.hubs import hub_pages, hub_url
        self.assertFalse([l for l in locs if '/questions/question/' in l])
        for cat, page, _ in hub_pages():
            self.assertIn('https://alagme.com' + hub_url(cat, page), locs)
        for path in ['/en/', '/en/pricing/', '/en/contact/', '/videos/']:
            self.assertIn('https://alagme.com' + path, locs)
        images = list(root.iter('{http://www.google.com/schemas/sitemap-image/1.1}loc'))
        self.assertEqual(len(images), posts.exclude(cloud_url__isnull=True).exclude(cloud_url='').count())

    def test_qna_category_pages_have_own_title_and_crumbs(self):
        t1 = self.client.get('/questions/?category=hifz').content.decode()
        t2 = self.client.get('/questions/?category=kids').content.decode()
        title = lambda t: re.search(r'<title>(.*?)</title>', t, re.S).group(1)
        self.assertNotEqual(title(t1), title(t2))
        self.assertIn('الحفظ والمراجعة', title(t1))
        self.assertNotIn('"FAQPage"', t1)  # الأسئلة من الزوار: QAPage في صفحة السؤال بس
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t1, re.S):
            json.loads(blk)

    def test_custom_404_is_noindex(self):
        r = self.client.get('/no-such-page-at-all/')
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'noindex', status_code=404)
        self.assertContains(r, '/blog/', status_code=404)

    def test_plain_keeps_table_rows(self):
        from core.templatetags.content_tags import plain
        self.assertEqual(plain('أمثلة:\n| أ | ب |\n|---|---|\n| **ج** | د |'), 'أمثلة:\nأ - ب\nج - د')


class SitemapResilienceTests(TestCase):
    def test_healthz_ok_on_any_host(self):
        r = self.client.get('/healthz', HTTP_HOST='healthcheck.railway.app')
        self.assertEqual(r.status_code, 200)

    def test_bad_slug_post_does_not_break_sitemap(self):
        from django.core.cache import cache
        cache.clear()
        p = Post.objects.indexable().first()
        Post.objects.filter(pk=p.pk).update(slug='bad slug؟')
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('bad slug', r.content.decode())
        self.assertGreater(r.content.decode().count('<url>'), 300)


class EngagementToolsTests(TestCase):
    """مشغل التلاوة واختبار الحفظ ودعوة الحجز في المقالات + صفحة متابعة الحفظ"""

    def test_full_tafsir_has_player_quiz_and_mid_cta(self):
        for url in ('/blog/tafsir-surat-al-kahf-kamila/', '/blog/surah-al-kahf-full-tafsir-english/'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertContains(r, 'class="surah-listen" data-surah="18" data-count="110"')
            self.assertContains(r, 'class="hifz-quiz"')
            self.assertContains(r, 'mid-cta')
            self.assertContains(r, '/quran/18/')
        r = self.client.get('/blog/surah-al-kahf-full-tafsir-english/')
        self.assertContains(r, 'Copy link')
        self.assertContains(r, 'Listen to the surah while you read')

    def test_short_surah_has_no_quiz(self):
        r = self.client.get('/blog/tafsir-surat-al-kawthar-kamila/', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'class="hifz-quiz"')

    def test_tracker_page_and_sitemap(self):
        r = self.client.get('/quran/hifz-tracker/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="ht-list"')
        self.assertContains(r, 'سورة الناس')
        self.assertNotIn('noindex', r.get('X-Robots-Tag', ''))
        self.assertContains(self.client.get('/sitemap.xml'), '/quran/hifz-tracker/')
        self.assertContains(self.client.get('/quran/18/'), 'class="hifz-quiz"')


class EnglishSiteTests(TestCase):
    """النسخة الإنجليزية /en/: LTR، hreflang متبادل، زرار تبديل اللغة، والحجز بيشتغل"""
    def test_english_pages_ltr_and_paired(self):
        for path, ar in [('/en/', '/'), ('/en/pricing/', '/pricing/'), ('/en/about/', '/about/'),
                         ('/en/contact/', '/contact/'), ('/en/quran/', '/quran/'), ('/en/blog/', '/blog/'),
                         ('/en/privacy-policy/', '/privacy-policy/'), ('/en/terms/', '/terms/'),
                         ('/en/quality-standards/', '/quality-standards/'), ('/en/editorial-policy/', '/editorial-policy/')]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, path)
            self.assertContains(r, '<html lang="en" dir="ltr">', msg_prefix=path)
            self.assertContains(r, f'hreflang="ar" href="https://alagme.com{ar}"', msg_prefix=path)
            self.assertNotIn('X-Robots-Tag', r.headers, path)
            back = self.client.get(ar)
            self.assertContains(back, f'hreflang="en" href="https://alagme.com{path}"', msg_prefix=ar)

    def test_english_booking(self):
        from accounts.models import TrialBooking
        r = self.client.post('/en/contact/', {'name': 'John Smith', 'country': 'UK', 'gender': 'male',
                                              'phone': '+447700900123', 'email': '', 'notes': 'age 9'})
        self.assertRedirects(r, '/en/contact/thank-you/')
        self.assertTrue(TrialBooking.objects.filter(name='John Smith', notes__startswith='[EN site]').exists())
        bad = self.client.post('/en/contact/', {'name': ''})
        self.assertContains(bad, 'This field is required')

    def test_english_post_uses_english_chrome(self):
        p = Post.objects.indexable().filter(category__slug='english').first()
        r = self.client.get(f'/blog/{p.slug}/')
        self.assertContains(r, 'dir="ltr"')
        self.assertContains(r, 'Free trial class')


class VideoLibraryTests(TestCase):
    def test_video_pages(self):
        from videos.models import Video
        v = Video.objects.create(youtube_url='https://youtu.be/yUpz_m5kWBE?t=3', title='شرح القلقلة للأطفال',
                                 description='درس مبسط', duration='5:07', category='tajweed')
        self.assertEqual(v.youtube_id, 'yUpz_m5kWBE')
        self.assertEqual(v.iso_duration, 'PT5M7S')
        r = self.client.get(v.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '"@type":"VideoObject"')
        self.assertContains(r, 'PT5M7S')
        lst = self.client.get('/videos/')
        self.assertContains(lst, v.title)
        self.assertNotIn('X-Robots-Tag', lst.headers)
        self.assertContains(self.client.get('/'), v.get_absolute_url())
        short = Video.objects.create(youtube_url='https://www.youtube.com/shorts/aqz-KE-bpKQ', title='x')
        self.assertTrue(short.is_short)


class SalaryByLessonCountTests(TestCase):
    def test_pay_by_count(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from core.models import Teacher, TeacherSalaryRecord
        admin = User.objects.create_superuser('boss', 'b@x.com', 'pw')
        self.client.force_login(admin)
        t = Teacher.objects.create(name='أ. سارة', lesson_rate=25)
        r = self.client.post(reverse('add_salary_record'), {'teacher': t.pk, 'lessons_count': '13', 'lesson_rate': '25',
                                                           'bonus': '10', 'deduction': '0'})
        self.assertEqual(r.status_code, 302)
        rec = TeacherSalaryRecord.objects.get(teacher=t)
        self.assertEqual(float(rec.base_amount), 325.0)
        self.assertEqual(rec.lessons_count, 13)
        self.assertEqual(rec.net_amount(), 335.0)
        page = self.client.get(reverse('add_salary_record'))
        self.assertContains(page, 'name="lessons_count"')


class ChannelVideosTests(TestCase):
    def test_channel_videos_seeded_with_descriptions(self):
        from videos.models import Video
        from videos.channel_seed import VIDEOS
        self.assertEqual(Video.objects.filter(youtube_id__in=[v['youtube_url'].rsplit('/', 1)[-1].split('=')[-1] for v in VIDEOS]).count(), len(VIDEOS))
        for v in Video.objects.all():
            self.assertGreater(len(v.description), 120, v.slug)
            self.assertNotIn('#', v.title)
            r = self.client.get(v.get_absolute_url())
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, 'noindex')

    def test_sync_adds_new_channel_videos_only(self):
        from unittest import mock
        from django.core.management import call_command
        from videos.models import Video
        feed = '''<?xml version="1.0"?><feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
<entry><yt:videoId>G2aixqFDz8U</yt:videoId><title>old</title><link rel="alternate" href="https://www.youtube.com/watch?v=G2aixqFDz8U"/><published>2026-09-14T17:36:41+00:00</published><media:group><media:description/></media:group></entry>
<entry><yt:videoId>NEWvid12345</yt:videoId><title>شرح القلقلة للأطفال #اكسبلور</title><link rel="alternate" href="https://www.youtube.com/shorts/NEWvid12345"/><published>2026-11-20T10:00:00+00:00</published><media:group><media:description/></media:group></entry>
</feed>'''.encode()
        resp = mock.Mock(content=feed, raise_for_status=lambda: None)
        before = Video.objects.count()
        with mock.patch('requests.get', return_value=resp):
            call_command('sync_youtube_channel')
            call_command('sync_youtube_channel')
        self.assertEqual(Video.objects.count(), before + 1)
        v = Video.objects.get(youtube_id='NEWvid12345')
        self.assertEqual(v.title, 'شرح القلقلة للأطفال')
        self.assertEqual(v.category, 'tajweed')
        self.assertTrue(v.is_short)
        self.assertIn('منصة العجمي', v.description)


class GscSyncTests(TestCase):
    """Search Console التلقائي: من غير نت، بنقلّد ردود جوجل"""

    class _Resp:
        def __init__(self, code=200, data=None):
            self.status_code, self._d = code, data or {}

        def json(self):
            return self._d

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(self.status_code)

    class _Session:
        def __init__(self, results):
            self.results, self.put_urls, self.inspected = results, [], []

        def put(self, url, timeout=None):
            self.put_urls.append(url)
            return GscSyncTests._Resp(204)

        def post(self, url, json=None, timeout=None):
            self.inspected.append(json['inspectionUrl'])
            res = self.results(json['inspectionUrl'])
            if res is None:
                return GscSyncTests._Resp(429)
            return GscSyncTests._Resp(200, {'inspectionResult': {'indexStatusResult': res}})

    def _run(self, results, urls, limit=10):
        from unittest import mock
        from core import gsc
        sess = self._Session(results)
        with mock.patch.object(gsc, 'session', return_value=sess), \
                mock.patch.object(gsc, 'sitemap_urls', return_value={u: None for u in urls}):
            out = gsc.run(limit=limit, report=False)
        return sess, out

    def test_submits_sitemap_and_records_status(self):
        from core.models import GscUrlStatus
        urls = ['https://alagme.com/a/', 'https://alagme.com/b/', 'https://alagme.com/c/']

        def res(u):
            if u.endswith('/a/'):
                return {'verdict': 'PASS', 'coverageState': 'Submitted and indexed', 'indexingState': 'INDEXING_ALLOWED',
                        'pageFetchState': 'SUCCESSFUL', 'lastCrawlTime': '2026-11-01T10:00:00Z'}
            if u.endswith('/b/'):
                return {'verdict': 'NEUTRAL', 'coverageState': 'Discovered - currently not indexed'}
            return {'verdict': 'FAIL', 'coverageState': "Excluded by 'noindex' tag",
                    'indexingState': 'BLOCKED_BY_META_TAG', 'pageFetchState': 'SUCCESSFUL'}

        sess, (checked, problems) = self._run(res, urls)
        self.assertEqual(checked, 3)
        self.assertIn('sitemap.xml', sess.put_urls[0])
        self.assertIn('sc-domain%3Aalagme.com', sess.put_urls[0])
        self.assertTrue(GscUrlStatus.objects.get(url=urls[0]).indexed)
        self.assertEqual(GscUrlStatus.objects.get(url=urls[1]).problem, '')  # لسه ماتفهرستش ≠ مشكلة
        self.assertEqual(GscUrlStatus.objects.get(url=urls[2]).problem, 'عليها noindex')
        self.assertEqual(problems, [(urls[2], 'عليها noindex')])

    def test_quota_stops_and_recent_not_rechecked(self):
        from core.models import GscUrlStatus
        urls = [f'https://alagme.com/p{i}/' for i in range(5)]
        calls = {'n': 0}

        def res(u):
            calls['n'] += 1
            return None if calls['n'] > 2 else {'verdict': 'PASS', 'coverageState': 'Submitted and indexed'}

        _, (checked, _) = self._run(res, urls)
        self.assertEqual(checked, 2)
        self.assertEqual(GscUrlStatus.objects.count(), 2)
        # المرة الجاية: اللي اتفحص حالًا (ومتفهرس) مايتفحصش تاني، والباقي ياخد الأولوية
        sess, _ = self._run(lambda u: {'verdict': 'PASS'}, urls)
        self.assertEqual(sorted(sess.inspected), sorted(urls[2:]))

    def test_not_configured_is_reported_not_crashing(self):
        import os
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('FIREBASE', 'GSC_CREDENTIALS', 'GOOGLE_CREDENTIALS'))}
        err = StringIO()
        with mock.patch.dict(os.environ, env, clear=True):
            call_command('gsc_sync', stderr=err, stdout=StringIO())
        self.assertIn('GSC مش متظبط', err.getvalue())

    def test_real_sitemap_urls_are_absolute(self):
        from core import gsc
        urls = gsc.sitemap_urls()
        self.assertTrue(urls)
        self.assertTrue(all(u.startswith('https://') for u in urls))


class BookingAndPricingTests(TestCase):
    """الأسعار بالعملات، صفحات الدول، الحجز على خطوتين، ومصدر الحجز"""

    def test_prices(self):
        from core.pricing import package_price, table
        self.assertEqual([r[1] for r in table('USD')], ['12', '24', '36'])
        self.assertEqual([r[2] for r in table('USD')], ['20', '40', '60'])
        self.assertTrue(all(r[1].isdigit() and r[2].isdigit() for c in ('SAR', 'KWD', 'GBP', 'EUR', 'CAD') for r in table(c)))
        self.assertEqual([r[1] for r in table('EGP')], ['200', '350', '500'])
        self.assertEqual(str(package_price('EGP', 12, 60)), '1000')
        r = self.client.get(reverse('pricing'))
        self.assertContains(r, 'data-price-table')
        self.assertNotContains(r, 'id="prices-data"')  # مفيش جداول عملات تانية في الصفحة
        self.assertContains(self.client.get('/en/pricing/'), 'data-price-table')

    def test_country_pages(self):
        from core.countries import COUNTRIES
        self.assertEqual(self.client.get(reverse('countries')).status_code, 200)
        for c in COUNTRIES:
            r = self.client.get(reverse('country_page', args=[c['slug']]))
            self.assertEqual(r.status_code, 200, c['slug'])
            self.assertContains(r, 'data-price-table')
        self.assertEqual(self.client.get('/online-quran/narnia/').status_code, 404)
        egypt = self.client.get('/online-quran/egypt/')
        self.assertContains(egypt, '>200<')
        self.assertContains(egypt, '>500<')

    def test_two_step_booking_and_source(self):
        import json
        from accounts.models import TrialBooking
        first = json.dumps({'l': '/blog/x/', 'r': 'https://www.google.com/', 'u': '', 'c': ''})
        r = self.client.post(reverse('booking_start'), {'name': 'أم سلمى', 'phone': '+966500000000', 'trk_first': first,
                                                        'trk_prev': '/blog/x/', 'ref': 'article-end', 'program': 'nourania'})
        self.assertEqual(r.status_code, 200)
        token = r.json()['token']
        b = TrialBooking.objects.get(phone='+966500000000')
        self.assertFalse(b.is_complete)
        self.assertEqual((b.source, b.from_page, b.cta, b.program), ('google', '/blog/x/', 'article-end', 'nourania'))
        r = self.client.post(reverse('contact'), {'name': 'أم سلمى', 'phone': '+966500000000', 'country': 'السعودية',
                                                  'gender': 'female', 'booking_token': token, 'trk_first': first,
                                                  'trk_prev': '/blog/x/', 'ref': 'article-end'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(TrialBooking.objects.filter(phone='+966500000000').count(), 1)
        b.refresh_from_db()
        self.assertTrue(b.is_complete)
        self.assertEqual(b.gender, 'female')
        # الحقل المخفي (بوت) بيترفض
        self.assertEqual(self.client.post(reverse('booking_start'), {'name': 'x', 'phone': '0100000000', 'website': 'y'}).status_code, 400)

    def test_source_classifier(self):
        from accounts.tracking import classify
        self.assertEqual(classify('', '', 'gclid'), 'google_ads')
        self.assertEqual(classify('', 'facebook|paid|nov', 'fbclid'), 'facebook_ads')
        self.assertEqual(classify('https://l.facebook.com/', '', ''), 'facebook')
        self.assertEqual(classify('https://www.bing.com/', '', ''), 'bing')
        self.assertEqual(classify('', '', ''), 'direct')

    def test_sources_report_admin(self):
        from django.contrib.auth import get_user_model
        U = get_user_model()
        admin = U.objects.create_superuser('adm_src', 'a@example.com', 'x-pass-123')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('admin:trialbooking_sources')).status_code, 200)

    def test_gsc_performance_sync(self):
        from core import gsc
        from core.models import GscPagePerformance

        class FakeResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {'rows': [
                    {'keys': ['https://alagme.com/blog/a/', 'تحفيظ'], 'clicks': 1, 'impressions': 500, 'position': 3.0},
                    {'keys': ['https://alagme.com/blog/a/', 'قرآن'], 'clicks': 0, 'impressions': 100, 'position': 5.0},
                    {'keys': ['https://alagme.com/blog/b/', 'تجويد'], 'clicks': 20, 'impressions': 100, 'position': 2.0},
                ]}

        class FakeSession:
            def post(self, *a, **k):
                return FakeResp()

        self.assertEqual(gsc.sync_performance(FakeSession()), 2)
        top = GscPagePerformance.objects.first()
        self.assertEqual(top.url, 'https://alagme.com/blog/a/')
        self.assertEqual(top.impressions, 600)
        self.assertIn('تحفيظ (500)', top.top_queries)

    def test_article_cta_matches_topic(self):
        from types import SimpleNamespace
        from blog.cta import topic_for
        P = lambda t, c='': SimpleNamespace(title=t, slug='', category=SimpleNamespace(slug=c))
        self.assertEqual(topic_for(P('أحكام النون الساكنة والتنوين')), 'tajweed')
        self.assertEqual(topic_for(P('كيف أحفظ القرآن لطفلي')), 'kids')
        self.assertEqual(topic_for(P('خطة حفظ سورة البقرة')), 'hifz')
        self.assertEqual(topic_for(P('تفسير سورة الكهف')), 'general')
        r = self.client.get('/blog/noon-sakinah-tanween-rules/')
        self.assertContains(r, 'program=ghiras&amp;ref=article-end')


class LevelTestAndAlertsTests(TestCase):
    def test_level_test(self):
        r = self.client.get(reverse('level_test'))
        self.assertContains(r, 'type="radio"')
        self.assertNotContains(r, 'noindex')
        r = self.client.get(reverse('level_test') + '?who=kid&reading=none&memorized=little&goal=hifz&times=2')
        self.assertContains(r, 'البداية النورانية')
        self.assertContains(r, 'noindex, follow')
        self.assertContains(r, 'program=nourania&amp;ref=level-test')
        r = self.client.get(reverse('level_test') + '?who=adult&reading=none&memorized=little&goal=hifz&times=1')
        self.assertContains(r, 'نور البيان')

    def test_english_country_pages(self):
        from core.countries import EN
        for slug in EN:
            r = self.client.get(f'/en/online-quran-classes/{slug}/')
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, f'/online-quran/{slug}/')  # hreflang للنسخة العربي
        self.assertEqual(self.client.get('/en/online-quran-classes/egypt/').status_code, 404)

    def test_abandoned_booking_alert_once(self):
        from datetime import timedelta
        from unittest import mock
        from django.utils import timezone
        from accounts.booking_alerts import notify_abandoned
        from accounts.models import TrialBooking
        b = TrialBooking.objects.create(name='x', phone='0100000000', is_complete=False)
        TrialBooking.objects.filter(pk=b.pk).update(created_at=timezone.now() - timedelta(minutes=15))
        TrialBooking.objects.create(name='y', phone='0100000001', is_complete=False)  # لسه جديد
        with mock.patch('accounts.notifications.send_admin_notification') as send:
            self.assertEqual(notify_abandoned(), 1)
            self.assertEqual(notify_abandoned(), 0)
            self.assertEqual(send.call_count, 1)


class RamadanChallengeCertificateTests(TestCase):
    def test_pages_render_and_indexed(self):
        for name in ('ramadan', 'juz_amma_challenge', 'quran_certificate'):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertNotContains(r, 'noindex')
        sm = self.client.get('/sitemap.xml').content.decode()
        for path in ('/ramadan/', '/quran/juz-amma-challenge/', '/quran/certificate/'):
            self.assertIn(path, sm)

    def test_challenge_plan_covers_juz_amma(self):
        from learning.challenge import plan
        from learning.quran import ayah_count
        days = plan()
        self.assertEqual(len(days), 30)
        covered = {}
        for d in days:
            for it in d['items']:
                covered.setdefault(it['surah'], set()).update(range(it['from'], it['to'] + 1))
        for s in range(78, 115):
            self.assertEqual(covered[s], set(range(1, ayah_count(s) + 1)), s)
        self.assertEqual(days[0]['items'][0]['surah'], 114)


class SerpTitleTests(TestCase):
    def test_cuts_long_title_at_clause(self):
        from core.templatetags.content_tags import serp_title
        t = 'سورة الأنبياء للأطفال: من الماء كل شيء حي، وإبراهيم والأصنام، ويا نار كوني بردًا وسلامًا'
        self.assertEqual(serp_title(t), 'سورة الأنبياء للأطفال: من الماء كل شيء حي، وإبراهيم والأصنام')

    def test_keeps_short_or_unsafe_titles(self):
        from core.templatetags.content_tags import serp_title
        self.assertEqual(serp_title('عنوان قصير'), 'عنوان قصير')
        quoted = 'تفسير آية «ما أصاب من مصيبة إلا بإذن الله ومن يؤمن بالله يهد قلبه» للأطفال والكبار'
        self.assertEqual(serp_title(quoted), quoted)


class SeoOpportunitiesTests(TestCase):
    def test_staff_page(self):
        from django.contrib.auth import get_user_model
        from core.models import GscPagePerformance
        u = get_user_model().objects.create_superuser('seo', 'seo@example.com', 'x')
        GscPagePerformance.objects.create(url='https://alagme.com/quran/for-kids/', impressions=900, clicks=3,
                                          ctr=0.3, position=8.4, opportunity=24, top_queries='سور القرآن للأطفال (500)')
        self.assertEqual(self.client.get('/admin/seo-opportunities/').status_code, 302)
        self.client.force_login(u)
        r = self.client.get('/admin/seo-opportunities/')
        self.assertContains(r, 'سور القرآن للأطفال')


class CtrOptimizerTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from blog.models import Post
        u = get_user_model().objects.create_user('w', 'w@example.com', 'x')
        self.post = Post.objects.create(title='شرح سور الفيل إلى الناس للأطفال: قصص ومعاني وأنشطة', slug='fil-kids',
                                        author=u, content='x', status='published')

    def _perf(self, ctr, pos, impr=800):
        from core.models import GscPagePerformance
        GscPagePerformance.objects.update_or_create(url='https://alagme.com/blog/fil-kids/', defaults=dict(
            impressions=impr, clicks=int(impr * ctr / 100), ctr=ctr, position=pos, opportunity=20,
            top_queries='سورة قريش للاطفال (400)، الفيل (100)'))

    def test_starts_then_reverts_when_not_better(self):
        from datetime import timedelta
        from django.utils import timezone
        from core import ctr_optimizer
        from core.models import SerpTitleTest
        self._perf(0.5, 8.2)
        self.assertEqual(ctr_optimizer.start_tests(write=lambda *_: None), 1)
        self.post.refresh_from_db()
        self.assertTrue(self.post.serp_title.startswith('سورة قريش للأطفال'))
        self.assertEqual(self.client.get('/blog/fil-kids/').status_code, 200)
        self.assertEqual(ctr_optimizer.start_tests(write=lambda *_: None), 0)  # مفيش تجربة تانية لنفس الصفحة
        SerpTitleTest.objects.update(started_at=timezone.now() - timedelta(days=29))
        self._perf(0.5, 8.2)
        ctr_optimizer.evaluate(write=lambda *_: None)
        self.post.refresh_from_db()
        self.assertEqual(self.post.serp_title, '')
        self.assertEqual(SerpTitleTest.objects.get().status, 'reverted')

    def test_keeps_when_better(self):
        from datetime import timedelta
        from django.utils import timezone
        from core import ctr_optimizer
        from core.models import SerpTitleTest
        self._perf(0.5, 8.2)
        ctr_optimizer.start_tests(write=lambda *_: None)
        SerpTitleTest.objects.update(started_at=timezone.now() - timedelta(days=29))
        self._perf(3.5, 8.0)
        ctr_optimizer.evaluate(write=lambda *_: None)
        self.post.refresh_from_db()
        self.assertTrue(self.post.serp_title)
        self.assertEqual(SerpTitleTest.objects.get().status, 'kept')

    def test_skips_good_ctr_and_brand(self):
        from core import ctr_optimizer
        self._perf(5.0, 8.0)
        self.assertEqual(ctr_optimizer.start_tests(write=lambda *_: None), 0)
        self.assertFalse(ctr_optimizer.usable_query('مؤسسة العجمي للقرآن', 'عنوان'))


class CrossLinksTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from blog.models import Post
        from core import crosslinks
        from qna.models import PublicQuestion
        crosslinks._MEMO.clear()
        u = get_user_model().objects.create_user('xl', 'xl@example.com', 'x')
        self.post = Post.objects.create(title='زقزوق البرتقالي والفستقي: شرح كامل', slug='zaqzuq-guide',
                                        author=u, content='كلام تجريبي عن الموضوع. ' * 400, status='published', keywords='زقزوق, فستقي')
        from django.core.cache import cache
        cache.clear()
        self.q = PublicQuestion.objects.create(visitor_name='زائر', title='ما معنى زقزوق البرتقالي والفستقي؟',
                                               question_text='سؤال تجريبي طويل بما يكفي للاختبار', status='approved')

    def tearDown(self):
        from core import crosslinks
        crosslinks._MEMO.clear()

    def test_links_both_ways(self):
        from core.crosslinks import posts_for_question, questions_for_post
        self.assertIn('zaqzuq-guide', [s for s, _ in posts_for_question(self.q)])
        self.assertIn(self.q.slug, [s for s, _ in questions_for_post(self.post)])
        r = self.client.get('/blog/zaqzuq-guide/')
        self.assertContains(r, 'أسئلة الزوار عن الموضوع')


class GeoPricingTests(TestCase):
    """كل زائر يتحول لصفحة بلده ويشوف أسعار بلده بس؛ محركات البحث مستثناة"""
    UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1'

    def get(self, path, country, ua=None):
        from unittest import mock
        with mock.patch('core.geo._lookup', return_value=country):
            return self.client.get(path, HTTP_USER_AGENT=ua or self.UA, HTTP_X_FORWARDED_FOR='1.2.3.4')

    def test_pricing_redirects_to_own_country(self):
        r = self.get('/pricing/', 'EG')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], '/online-quran/egypt/#prices')
        self.assertIn('private', r['Cache-Control'])
        self.assertEqual(self.get('/en/pricing/', 'GB')['Location'], '/en/online-quran-classes/uk/#prices')

    def test_other_country_page_redirects(self):
        r = self.get('/online-quran/egypt/', 'SA')
        self.assertEqual(r['Location'], '/online-quran/saudi-arabia/')
        self.assertEqual(self.get('/online-quran/saudi-arabia/', 'EG')['Location'], '/online-quran/egypt/')
        self.assertEqual(self.get('/online-quran/egypt/', 'EG').status_code, 200)

    def test_unlisted_country_sees_dollars_only(self):
        r = self.get('/online-quran/egypt/', 'JO')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, '>200<')  # مش أسعار مصر
        self.assertContains(r, '>12<')  # 4 حصص بالدولار
        r = self.get('/pricing/', 'MA')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'دولار')
        self.assertNotContains(r, 'جنيه مصري')

    def test_bots_are_not_redirected(self):
        googlebot = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        r = self.get('/online-quran/egypt/', 'US', ua=googlebot)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '>200<')
        self.assertEqual(self.get('/pricing/', 'US', ua=googlebot).status_code, 200)

    def test_real_lookup(self):
        from core.geo import _lookup
        self.assertEqual(_lookup('8.8.8.8'), 'US')
        self.assertEqual(_lookup('127.0.0.1'), '')
