import json
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Country, Student, Teacher, TeacherActivity

from . import quran, services
from .models import Homework, StudentActivity, Submission

User = get_user_model()
MEDIA = tempfile.mkdtemp()
SETTINGS = dict(SECURE_SSL_REDIRECT=False, CHAT_PUSH_SYNC=True, MEDIA_ROOT=MEDIA)


def audio(name='r.webm', size=4000, mime='audio/webm'):
    return SimpleUploadedFile(name, b'\x1aE\xdf\xa3' + b'0' * size, content_type=mime)


class QuranDataTests(TestCase):
    def test_index_and_counts(self):
        idx = quran.index()
        self.assertEqual(len(idx), 114)
        self.assertEqual(sum(s['count'] for s in idx), 6236)
        self.assertEqual(quran.surah_name(112), 'الإخلاص')
        self.assertEqual(len(quran.verses(2, 1, 5)), 5)
        self.assertEqual(quran.audio_url('Husary_128kbps', 18, 10), 'https://everyayah.com/data/Husary_128kbps/018010.mp3')

    def test_range_label(self):
        self.assertEqual(quran.range_label(78, 1, 40), 'سورة النبأ كاملة')
        self.assertIn('من الآية 1 إلى 5', quran.range_label(78, 1, 5))


@override_settings(**SETTINGS)
class PublicQuranTests(TestCase):
    def test_pages_public_and_indexed(self):
        r = self.client.get('/quran/')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('X-Robots-Tag', r)
        self.assertContains(r, 'سورة الكهف')
        r = self.client.get('/quran/18/')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('X-Robots-Tag', r)
        self.assertContains(r, 'data-a="110"')
        self.assertContains(r, 'rel="canonical" href="https://alagme.com/quran/18/"')
        self.assertContains(r, 'BreadcrumbList')
        self.assertEqual(self.client.get('/quran/115/').status_code, 404)

    def test_sitemap_has_surahs(self):
        r = self.client.get('/sitemap.xml')
        self.assertContains(r, '/quran/114/')


@override_settings(**SETTINGS)
class HomeworkTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        c = Country.objects.create(name='مصر')
        self.t_user = User.objects.create_user('t1', password='pass12345', user_type='teacher')
        self.teacher = Teacher.objects.create(name='فاطمة', user=self.t_user)
        self.t2_user = User.objects.create_user('t2', password='pass12345', user_type='teacher')
        self.teacher2 = Teacher.objects.create(name='مريم', user=self.t2_user)
        u = User(username='st1', user_type='student'); u._skip_student_profile = True; u.set_password('pass12345'); u.save()
        self.s_user = u
        self.student = Student.objects.create(country=c, teacher=self.teacher, name='أحمد', month='أكتوبر', user=u)
        u2 = User(username='st2', user_type='student'); u2._skip_student_profile = True; u2.set_password('pass12345'); u2.save()
        self.s2_user = u2
        self.student2 = Student.objects.create(country=c, teacher=self.teacher2, name='سارة', month='أكتوبر', user=u2)
        self.admin = User.objects.create_user('admin', password='pass12345', is_staff=True, is_superuser=True)

    def login(self, user):
        self.client.force_login(user)

    def make_hw(self, **kw):
        self.login(self.t_user)
        data = {'students': [self.student.pk], 'kind': 'memorize', 'surah': '78', 'ayah_from': '1', 'ayah_to': '5',
                'instructions': 'اسمع 3 مرات وسجّل', 'due_date': ''}
        data.update(kw)
        with mock.patch('accounts.notifications.send_user_notification') as push:
            r = self.client.post(reverse('learning_teacher_new'), data)
        self.push = push
        return r

    def test_teacher_creates_homework_and_student_notified(self):
        r = self.make_hw()
        hw = Homework.objects.get()
        self.assertRedirects(r, reverse('learning_teacher_detail', args=[hw.pk]), fetch_redirect_response=False)
        self.assertEqual(hw.title, 'حفظ جديد - سورة النبأ من الآية 1 إلى 5')
        self.assertEqual(len(hw.verses()), 5)
        self.push.assert_called_once()
        self.assertEqual(self.push.call_args[0][0], [self.s_user])

    def test_teacher_cannot_assign_other_teachers_student(self):
        self.make_hw(students=[self.student2.pk])
        self.assertFalse(Homework.objects.exists())

    def test_contact_info_in_instructions_blocked(self):
        self.make_hw(instructions='كلمني على 01012345678')
        self.assertFalse(Homework.objects.exists())
        self.assertTrue(TeacherActivity.objects.filter(kind='chat_flag').exists())

    def test_full_cycle_submit_review_points(self):
        self.make_hw()
        hw = Homework.objects.get()
        self.login(self.s_user)
        r = self.client.get(reverse('learning_student_homework', args=[hw.pk]))
        self.assertContains(r, 'سجّل بصوتك')
        self.assertContains(r, 'data-a="5"')
        # من غير صوت = مرفوض
        self.client.post(reverse('learning_student_homework', args=[hw.pk]), {'note': 'تمام'})
        self.assertFalse(Submission.objects.exists())
        # ملف مش صوت = مرفوض
        self.client.post(reverse('learning_student_homework', args=[hw.pk]),
                         {'audio': SimpleUploadedFile('x.exe', b'0' * 5000, content_type='application/octet-stream')})
        self.assertFalse(Submission.objects.exists())
        with mock.patch('accounts.notifications.send_user_notification') as push:
            self.client.post(reverse('learning_student_homework', args=[hw.pk]), {'audio': audio(), 'note': 'الآية الأخيرة صعبة'})
        sub = Submission.objects.get()
        self.assertEqual(push.call_args[0][0], [self.t_user])
        self.assertEqual(hw.status(), 'submitted')
        self.assertEqual(StudentActivity.total_points(self.student), services.POINTS_SUBMIT)
        # مينفعش يسلّم تاني وهو مستني
        self.client.post(reverse('learning_student_homework', args=[hw.pk]), {'audio': audio()})
        self.assertEqual(Submission.objects.count(), 1)
        # الملف محمي
        self.assertEqual(self.client.get(reverse('learning_audio', args=['sub', sub.pk])).status_code, 200)
        self.login(self.s2_user)
        self.assertEqual(self.client.get(reverse('learning_audio', args=['sub', sub.pk])).status_code, 404)
        self.login(self.t2_user)
        self.assertEqual(self.client.get(reverse('learning_teacher_detail', args=[hw.pk])).status_code, 404)
        # المعلمة: إعادة
        self.login(self.t_user)
        self.assertEqual(self.client.get(reverse('learning_audio', args=['sub', sub.pk])).status_code, 200)
        self.client.post(reverse('learning_teacher_detail', args=[hw.pk]), {'status': 'redo', 'stars': '5', 'feedback': 'انتبه للمد'})
        sub.refresh_from_db()
        self.assertEqual((sub.status, sub.stars), ('redo', None))
        self.assertEqual(Homework.objects.get().status(), 'redo')
        # الطالب يسلّم تاني والمعلمة تقبل بـ 4 نجوم
        self.login(self.s_user)
        self.client.post(reverse('learning_student_homework', args=[hw.pk]), {'audio': audio('r2.m4a', mime='audio/mp4')})
        self.login(self.t_user)
        with mock.patch('accounts.notifications.send_user_notification'):
            self.client.post(reverse('learning_teacher_detail', args=[hw.pk]), {'status': 'approved', 'stars': '4', 'feedback': 'ممتاز'})
        self.assertEqual(Homework.objects.get().status(), 'approved')
        self.assertEqual(StudentActivity.total_points(self.student), services.POINTS_SUBMIT + 4 * services.POINTS_PER_STAR)
        # الإدارة شايفة كل حاجة
        self.login(self.admin)
        self.assertContains(self.client.get(reverse('learning_admin_list')), 'أحمد')
        self.assertContains(self.client.get(reverse('learning_admin_detail', args=[hw.pk])), 'ممتاز')
        self.assertEqual(self.client.get(reverse('learning_audio', args=['sub', sub.pk])).status_code, 200)

    def test_teacher_feedback_with_phone_blocked(self):
        self.make_hw()
        hw = Homework.objects.get()
        Submission.objects.create(homework=hw, audio=audio(), audio_mime='audio/webm')
        self.login(self.t_user)
        self.client.post(reverse('learning_teacher_detail', args=[hw.pk]), {'status': 'approved', 'stars': '5', 'feedback': 'واتساب 0101 234 5678'})
        self.assertEqual(Submission.objects.get().status, 'submitted')

    def test_game_points_capped_daily(self):
        self.login(self.s_user)
        url = reverse('learning_api_score')
        total = 0
        for _ in range(10):
            r = self.client.post(url, json.dumps({'kind': 'game', 'points': 999, 'detail': 'arrange'}), content_type='application/json')
            total += r.json()['added']
        self.assertEqual(total, services.GAME_DAILY_CAP)
        r = self.client.post(url, json.dumps({'kind': 'listen', 'detail': '1:1:7'}), content_type='application/json')
        self.assertEqual(r.json()['added'], services.LISTEN_POINTS)
        self.assertEqual(StudentActivity.streak(self.student), 1)

    def test_student_pages_render(self):
        self.make_hw()
        self.login(self.s_user)
        for name in ['student_portal_home', 'learning_student_list', 'learning_student_listen',
                     'learning_student_games', 'learning_student_achievements']:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertEqual(r['X-Robots-Tag'], 'noindex, nofollow')
        r = self.client.get(reverse('student_portal_home'))
        self.assertContains(r, 'آية اليوم')
        self.assertContains(r, 'واجباتي')

    def test_access_control(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse('learning_student_games')), reverse('student_login'), fetch_redirect_response=False)
        self.login(self.s_user)
        self.assertEqual(self.client.get(reverse('learning_teacher_list')).status_code, 302)
        self.assertEqual(self.client.get(reverse('learning_admin_list')).status_code, 302)
        self.login(self.t_user)
        self.assertEqual(self.client.get(reverse('learning_teacher_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('learning_teacher_new')).status_code, 200)
