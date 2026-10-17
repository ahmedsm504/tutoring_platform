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
        cls.qcat = QuestionCategory.objects.create(name='التجويد', slug='tajweed')
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
