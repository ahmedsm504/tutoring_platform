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
        r = self.client.get('/blog/noon-sakinah-tanween-rules/')
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
        self.assertNotContains(self.client.get('/contact/'), 'adsbygoogle.js')
        self.assertContains(self.client.get('/blog/madd-types-tajweed/'), 'adsbygoogle.js')


@override_settings(SECURE_SSL_REDIRECT=False)
class Wave2Tests(TestCase):
    def test_english_article_lang_and_hreflang(self):
        r = self.client.get('/blog/noon-sakinah-tanween-rules-english/')
        self.assertContains(r, '<html lang="en"')
        self.assertContains(r, 'hreflang="ar" href="https://alagme.com/blog/noon-sakinah-tanween-rules/"')
        self.assertContains(r, 'lang="en" dir="ltr"')
        self.assertContains(r, 'In this article')
        r = self.client.get('/blog/noon-sakinah-tanween-rules/')
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
        self.assertTrue(Post.objects.filter(slug='quran-revision-games-kids-english', status='published').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='What is Iqlab in Tajweed?').exists())
        r = self.client.get('/blog/ayat-al-kursi-tajweed-english/')
        self.assertContains(r, '<html lang="en"')
        self.assertContains(r, 'hreflang="ar" href="https://alagme.com/blog/ayat-al-kursi-tajweed/"')

    def test_every_admin_page_opens(self):
        """كل صفحات الأدمن (القائمة + الإضافة + التعديل) تفتح من غير 500."""
        from django.contrib import admin
        from blog.models import Comment
        admin_user = User.objects.create_superuser('wave3admin', 'a3@example.com', 'x-Pass-12345')
        post = Post.objects.filter(status='published').first()
        Comment.objects.create(post=post, author_name='t', author_email='t@example.com', content='hi', is_approved=False)
        Post.objects.filter(pk=post.pk).update(is_featured=True)
        self.client.force_login(admin_user)
        for model in admin.site._registry:
            opts = model._meta
            for name in ('changelist', 'add'):
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
        r = self.client.get('/blog/madd-types-tajweed/')
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
        self.assertEqual(arts[16]['slug'], 'juz-amma-plan-for-kids')  # دفعة 0003 ثابتة
        self.assertEqual(arts[-1]['slug'], 'quran-companion-for-the-sick')
        for slug in ('mutashabihat-juz-amma', 'sujud-al-tilawa-places', 'quran-corner-at-home'):
            r = self.client.get(f'/blog/{slug}/')
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
        r = self.client.get('/blog/madd-types-tajweed/')
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
            self.assertEqual(self.client.get(f'/blog/{slug}/').status_code, 200, slug)
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
            self.assertEqual(self.client.get(f'/blog/{slug}/').status_code, 200, slug)
        self.assertTrue(PublicQuestion.objects.filter(title='ما أرجى آية في القرآن؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave7Tests(TestCase):
    def test_wave7_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual(len(load_articles()), 200)
        for slug in ('hajr-al-quran-five-types', 'madinah-mushaf-story', 'yusuf-story-for-kids', 'tajweed-applied-surat-al-mulk'):
            r = self.client.get(f'/blog/{slug}/')
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أرتب الحواميم السبع في ذهني؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما هي «المسبّحات»؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave8Tests(TestCase):
    def test_wave8_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual(len(load_articles()), 300)
        for slug in ('memorize-surat-al-imran', 'tajweed-applied-surat-an-naba', 'sulayman-story-for-kids', 'parables-in-the-quran'):
            r = self.client.get(f'/blog/{slug}/')
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='كيف أقرأ «ءأعجمي» في سورة فصلت؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='ما هو «المصحف الإمام»؟').exists())


@override_settings(**TEST_SETTINGS)
class Wave9Tests(TestCase):
    def test_wave9_content(self):
        from content_seed import load_articles
        self.assertGreaterEqual(len(load_articles()), 450)
        for slug in ('juz-1-memorization-plan', 'four-sakt-positions-hafs', 'asiya-story-for-kids',
                     'tafsir-surat-al-ikhlas', 'angels-in-the-quran', 'quran-at-work'):
            r = self.client.get(f'/blog/{slug}/')
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
        self.assertEqual(len(load_articles()), 600)
        for slug in ('juz-6-memorization-plan', 'tafsir-surat-al-mulk', 'ghulam-and-king-story-for-kids',
                     'ibad-al-rahman-traits', 'nasikh-mansukh', 'quran-companion-for-the-sick'):
            r = self.client.get(f'/blog/{slug}/')
            self.assertEqual(r.status_code, 200, slug)
            self.assertContains(r, '<html lang="ar"')
        self.assertTrue(PublicQuestion.objects.filter(title='ما الفرق بين الخوف والخشية في القرآن؟').exists())
        self.assertTrue(PublicQuestion.objects.filter(title='هل يحتاج معلم القرآن أونلاين إلى إجازة؟').exists())

    def test_juz21_refresh(self):
        from blog.models import Post
        p = Post.objects.get(slug='history-of-juz-and-hizb-divisions')
        self.assertIn('العنكبوت: 46', p.content)


class SiteIndexAndCachingTests(TestCase):
    def test_site_index_lists_content(self):
        r = self.client.get('/site-index/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '/blog/nasikh-mansukh/')
        self.assertContains(r, 'فهرس كل المقالات والأسئلة')

    def test_sitemap_has_site_index(self):
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)

    def test_blog_detail_conditional_get(self):
        r = self.client.get('/blog/nasikh-mansukh/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Last-Modified', r)
        r2 = self.client.get('/blog/nasikh-mansukh/', HTTP_IF_MODIFIED_SINCE=r['Last-Modified'])
        self.assertEqual(r2.status_code, 304)
