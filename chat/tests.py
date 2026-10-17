import json
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import FCMToken, StudentProfile
from core.models import Country, Student, Supervisor, Teacher, TeacherActivity

from . import filters
from .models import ChatMessage, Conversation

User = get_user_model()
MEDIA = tempfile.mkdtemp()
SETTINGS = dict(SECURE_SSL_REDIRECT=False, CHAT_PUSH_SYNC=True, MEDIA_ROOT=MEDIA)
AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class FilterTests(TestCase):
    def test_phone_numbers_detected(self):
        for t in ['رقمي 01012345678', 'كلميني ٠١٠١٢٣٤٥٦٧٨', '+20 101 234 5678', '010-1234-5678', '0 1 0 1 2 3 4 5 6 7 8']:
            self.assertTrue(filters.scan(t).is_strong, t)

    def test_normal_text_allowed(self):
        for t in ['الحلقة يوم 17-10-2026 الساعة 5', 'سورة البقرة آية 255', 'الصفحة 12 و 13', 'الحصة 30 دقيقة', 'ممتاز يا بطل 🌟']:
            self.assertFalse(filters.scan(t).is_strong, t)

    def test_links_email_handles(self):
        for t in ['wa.me/201012345678', 'instagram.com/teacher', 'ايميلي a.b@gmail.com', 'تابعيني @teacher_quran', 'https://t.me/abc']:
            self.assertTrue(filters.scan(t).is_strong, t)

    @override_settings(CHAT_ALLOWED_LINK_DOMAINS=['alagme.com', 'meet.google.com'])
    def test_allowed_domains(self):
        self.assertFalse(filters.scan('رابط الحلقة https://meet.google.com/abc-defg-hij').is_strong)

    def test_number_words_and_soft(self):
        self.assertTrue(filters.scan('صفر واحد صفر واحد اتنين تلاته اربعه').is_strong)
        r = filters.scan('ممكن نتكلم على الخاص؟')
        self.assertTrue(r.is_soft and not r.is_strong)


@override_settings(**SETTINGS)
class ChatTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        c = Country.objects.create(name='مصر')
        self.sup_user = User.objects.create_user('s1', password='pass12345', user_type='supervisor')
        self.sup = Supervisor.objects.create(name='مشرفة', user=self.sup_user)
        self.osup_user = User.objects.create_user('s2', password='pass12345', user_type='supervisor')
        Supervisor.objects.create(name='تانية', user=self.osup_user)
        self.t_user = User.objects.create_user('t1', password='pass12345', user_type='teacher')
        self.teacher = Teacher.objects.create(name='فاطمة', user=self.t_user, supervisor=self.sup)
        self.t2_user = User.objects.create_user('t2', password='pass12345', user_type='teacher')
        self.teacher2 = Teacher.objects.create(name='مريم', user=self.t2_user)
        s_user = User(username='st1', user_type='student')
        s_user._skip_student_profile = True
        s_user.set_password('pass12345')
        s_user.save()
        self.s_user = s_user
        self.student = Student.objects.create(country=c, teacher=self.teacher, name='أحمد', month='أكتوبر',
                                              phone='01011111111', guardian_phone='01022222222', user=s_user)
        self.other_student = Student.objects.create(country=c, teacher=self.teacher2, name='سارة', month='أكتوبر')
        self.admin = User.objects.create_user('boss', password='pass12345', is_staff=True, user_type='admin')

    def conv(self):
        return Conversation.objects.get_or_create(student=self.student)[0]

    def send(self, user, text='', file=None):
        conv = self.conv()
        self.client.force_login(user)
        data = {'text': text}
        if file:
            data['file'] = file
        return self.client.post(reverse('chat_send', args=[conv.pk]), data, **AJAX)

    # ---------- الأساسيات ----------
    def test_student_account_has_no_legacy_profile(self):
        self.assertFalse(StudentProfile.objects.filter(user=self.s_user).exists())

    def test_student_to_teacher_flow(self):
        r = self.send(self.s_user, 'السلام عليكم يا أستاذة')
        self.assertEqual(r.status_code, 200)
        self.assertIn('السلام عليكم', r.json()['html'])
        conv = self.conv()
        conv.refresh_from_db()
        self.assertEqual((conv.teacher_unread, conv.student_unread, conv.admin_unread), (1, 0, 1))
        # المعلمة بتشوفها والعداد بيتصفر وعلامة القراءة بتظهر للطالب
        self.client.force_login(self.t_user)
        self.assertEqual(self.client.get(reverse('chat_unread')).json()['count'], 1)
        r = self.client.get(reverse('chat_teacher_thread', args=[self.student.pk]))
        self.assertContains(r, 'السلام عليكم')
        conv.refresh_from_db()
        self.assertEqual(conv.teacher_unread, 0)
        msg = conv.messages.get()
        self.assertIsNotNone(msg.read_at)
        self.client.force_login(self.s_user)
        d = self.client.get(reverse('chat_poll', args=[conv.pk]), {'after': 0}).json()
        self.assertIn(msg.id, d['read_ids'])

    def test_teacher_reply_reaches_student_live(self):
        self.send(self.t_user, 'وعليكم السلام، برافو عليك')
        conv = self.conv()
        self.client.force_login(self.s_user)
        u = self.client.get(reverse('chat_unread')).json()
        self.assertEqual(u['count'], 1)
        self.assertIn('فاطمة', u['latest']['title'])
        d = self.client.get(reverse('chat_poll', args=[conv.pk]), {'after': 0}).json()
        self.assertIn('برافو', d['html'])
        conv.refresh_from_db()
        self.assertEqual(conv.student_unread, 0)

    def test_typing_and_online(self):
        conv = self.conv()
        self.client.force_login(self.t_user)
        self.client.post(reverse('chat_typing', args=[conv.pk]))
        self.client.get(reverse('chat_poll', args=[conv.pk]))
        self.client.force_login(self.s_user)
        d = self.client.get(reverse('chat_poll', args=[conv.pk])).json()
        self.assertTrue(d['typing'])
        self.assertTrue(d['online'])

    # ---------- الحماية ----------
    def test_teacher_phone_blocked(self):
        r = self.send(self.t_user, 'كلمني على ٠١٢٣٤٥٦٧٨٩٠ أحسن')
        self.assertTrue(r.json()['warning'])
        msg = ChatMessage.objects.get()
        self.assertTrue(msg.is_blocked and msg.flagged)
        conv = self.conv()
        conv.refresh_from_db()
        self.assertTrue(conv.is_flagged)
        self.assertEqual(conv.student_unread, 0)
        self.assertTrue(TeacherActivity.objects.filter(kind='chat_flag', status='blocked').exists())
        # الطالب مش شايفها خالص
        self.client.force_login(self.s_user)
        r = self.client.get(reverse('student_chat'))
        self.assertNotContains(r, '٠١٢٣٤٥٦٧٨٩٠')
        # الإدارة شايفاها
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('chat_admin_thread', args=[self.student.pk])), '٠١٢٣٤٥٦٧٨٩٠')

    def test_student_phone_blocked_too(self):
        self.send(self.s_user, 'ده رقم بابا 01099998888')
        self.assertTrue(ChatMessage.objects.get().is_blocked)
        self.client.force_login(self.t_user)
        r = self.client.get(reverse('chat_teacher_thread', args=[self.student.pk]))
        self.assertNotContains(r, '01099998888')
        self.assertTrue(TeacherActivity.objects.filter(kind='chat_flag', status='student').exists())

    def test_soft_words_delivered_but_flagged(self):
        self.send(self.t_user, 'ممكن نكمل على الخاص')
        msg = ChatMessage.objects.get()
        self.assertFalse(msg.is_blocked)
        self.assertTrue(msg.flagged)

    def test_admin_not_filtered(self):
        self.send(self.admin, 'رقم الإدارة 01044568181')
        self.assertFalse(ChatMessage.objects.get().is_blocked)

    def test_teacher_never_sees_student_phones(self):
        self.client.force_login(self.t_user)
        for url in [reverse('chat_teacher_inbox'), reverse('chat_teacher_thread', args=[self.student.pk])]:
            html = self.client.get(url).content.decode()
            self.assertNotIn('01011111111', html)
            self.assertNotIn('01022222222', html)

    # ---------- الصلاحيات ----------
    def test_other_teacher_and_students_blocked(self):
        conv = self.conv()
        self.client.force_login(self.t2_user)
        self.assertEqual(self.client.get(reverse('chat_teacher_thread', args=[self.student.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('chat_poll', args=[conv.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('chat_send', args=[conv.pk]), {'text': 'x'}, **AJAX).status_code, 403)
        other_conv = Conversation.objects.create(student=self.other_student)
        self.client.force_login(self.s_user)
        self.assertEqual(self.client.get(reverse('chat_poll', args=[other_conv.pk])).status_code, 403)

    def test_supervisor_readonly(self):
        self.send(self.s_user, 'سؤال')
        conv = self.conv()
        self.client.force_login(self.sup_user)
        r = self.client.get(reverse('chat_supervisor_thread', args=[self.student.pk]))
        self.assertContains(r, 'سؤال')
        self.assertNotContains(r, 'id="cb-form"')
        self.assertEqual(self.client.post(reverse('chat_send', args=[conv.pk]), {'text': 'x'}, **AJAX).status_code, 403)
        self.client.force_login(self.osup_user)
        self.assertEqual(self.client.get(reverse('chat_supervisor_thread', args=[self.student.pk])).status_code, 404)

    def test_admin_lock(self):
        self.conv()
        self.client.force_login(self.admin)
        self.client.post(reverse('chat_admin_update', args=[self.student.pk]), {'action': 'toggle_lock'})
        r = self.send(self.t_user, 'ازيك')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(ChatMessage.objects.exists())
        self.assertEqual(self.send(self.admin, 'الإدارة').status_code, 200)

    def test_admin_inbox_and_non_staff(self):
        self.send(self.s_user, 'مرحبا')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('chat_admin_inbox')), 'أحمد')
        self.client.force_login(self.t_user)
        self.assertNotEqual(self.client.get(reverse('chat_admin_inbox')).status_code, 200)

    # ---------- المرفقات ----------
    def test_voice_note(self):
        f = SimpleUploadedFile('voice.webm', b'\x1aE\xdf\xa3voice', content_type='audio/webm')
        r = self.send(self.t_user, '', f)
        self.assertEqual(r.status_code, 200)
        msg = ChatMessage.objects.get()
        self.assertEqual(msg.attachment_kind, 'audio')
        self.client.force_login(self.s_user)
        resp = self.client.get(reverse('chat_attachment', args=[msg.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(b''.join(resp.streaming_content), b'\x1aE\xdf\xa3voice')
        self.client.force_login(self.t2_user)
        self.assertEqual(self.client.get(reverse('chat_attachment', args=[msg.pk])).status_code, 404)

    def test_hidden_attachment(self):
        self.send(self.s_user, '', SimpleUploadedFile('a.png', b'\x89PNG', content_type='image/png'))
        msg = ChatMessage.objects.get()
        self.client.force_login(self.admin)
        self.client.post(reverse('chat_admin_update', args=[self.student.pk]), {'action': 'hide_attachment', 'message_id': msg.pk})
        self.client.force_login(self.t_user)
        self.assertEqual(self.client.get(reverse('chat_attachment', args=[msg.pk])).status_code, 404)

    def test_rejects_dangerous_files(self):
        for name, ct in [('x.html', 'text/html'), ('x.exe', 'application/octet-stream'), ('x.svg', 'image/svg+xml'), ('x.png.html', 'image/png')]:
            r = self.send(self.s_user, '', SimpleUploadedFile(name, b'<script>', content_type=ct))
            self.assertEqual(r.status_code, 400, name)
        self.assertFalse(ChatMessage.objects.exists())

    # ---------- الإشعارات ----------
    def test_push_sent_to_recipient_only(self):
        FCMToken.objects.create(token='tok-teacher', user=self.t_user)
        FCMToken.objects.create(token='tok-student', user=self.s_user)
        with mock.patch('accounts.notifications.send_user_notification') as push:
            with self.captureOnCommitCallbacks(execute=True):
                self.send(self.s_user, 'سؤال للمعلمة')
        push.assert_called_once()
        users, title = push.call_args[0][0], push.call_args[0][1]
        self.assertEqual(users, [self.t_user])
        self.assertIn('أحمد', title)

    def test_no_push_for_blocked(self):
        with mock.patch('accounts.notifications.send_user_notification') as push:
            with self.captureOnCommitCallbacks(execute=True):
                self.send(self.s_user, 'رقمي 01012345678')
        push.assert_not_called()

    def test_fcm_token_linked_to_user(self):
        self.client.force_login(self.s_user)
        self.client.post('/save-fcm-token/', data=json.dumps({'token': 'abc'}), content_type='application/json')
        self.assertEqual(FCMToken.objects.get(token='abc').user, self.s_user)

    # ---------- بوابة الطالب ----------
    def test_student_portal_and_login(self):
        self.client.post(reverse('student_login'), {'username': 'st1', 'password': 'pass12345'})
        r = self.client.get(reverse('student_portal_home'))
        self.assertContains(r, 'أحمد')
        self.assertContains(r, 'فاطمة')
        self.assertEqual(self.client.get(reverse('student_chat')).status_code, 200)
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'st1', 'password': 'pass12345'})
        self.assertEqual(r['Location'], reverse('student_portal_home'))
        self.client.force_login(self.t_user)
        self.assertEqual(self.client.get(reverse('student_portal_home')).status_code, 302)

    def test_admin_creates_student_login(self):
        s = Student.objects.create(country=self.student.country, teacher=self.teacher, name='يوسف', month='x')
        self.client.force_login(self.admin)
        self.client.post(reverse('create_student_login', args=[s.pk]), {'username': 'yousef', 'password': 'abc12345', 'password2': 'abc12345'})
        s.refresh_from_db()
        self.assertEqual(s.user.username, 'yousef')
        self.assertFalse(s.user.is_staff)
        self.assertFalse(StudentProfile.objects.filter(user=s.user).exists())
        self.client.post(reverse('revoke_student_login', args=[s.pk]))
        s.refresh_from_db()
        self.assertIsNone(s.user)
