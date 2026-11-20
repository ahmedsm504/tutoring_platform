import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.core.cache import cache

from .models import Application, ApplicationFile, FormQuestion, JobOpening


def _answer(q):
    t = q.qtype
    if t == 'text':
        return 'فاطمة أحمد محمد' if q.role == 'name' else 'ليسانس دراسات إسلامية'
    if t == 'number':
        return '٢٦' if q.role == 'age' else str(max(q.min_value or 0, 3))
    if t == 'phone':
        return '01012345678'
    if t in ('radio', 'select', 'yesno', 'suggest'):
        return q.required_answer or q.choice_list()[0]
    if t == 'checkboxes':
        return q.choice_list()[0]
    if t == 'textarea':
        return 'أبدأ الحلقة بالمراجعة ثم التصحيح ثم شرح حكم تجويدي ثم الحفظ الجديد بالتلقين ثم الواجب والتقرير لولي الأمر بانتظام.'
    if t == 'agree':
        return 'on'
    return None


@override_settings(SECURE_SSL_REDIRECT=False)
class CareersTests(TestCase):
    def setUp(self):
        cache.clear()
        self.job = JobOpening.objects.get(slug='quran-teacher')

    def _payload(self, job, skip=None):
        data = {}
        for q in job.questions.filter(is_active=True):
            if q.key == skip:
                continue
            if q.qtype == 'files':
                if q.required:
                    data[q.key] = SimpleUploadedFile('a.jpg', b'\xff\xd8\xff\xe0' + b'0' * 500, content_type='image/jpeg')
            elif q.qtype == 'audio':
                data[q.key] = SimpleUploadedFile('rec', b'\x1aE\xdf\xa3' + b'0' * 500, content_type='audio/webm;codecs=opus')
            else:
                v = _answer(q)
                if v is not None:
                    data[q.key] = v
        return data

    def test_seeded_jobs_and_pages(self):
        self.assertEqual(set(JobOpening.objects.values_list('slug', flat=True)), {'quran-teacher', 'quran-supervisor'})
        r = self.client.get('/jobs/')
        self.assertContains(r, 'معلمة قرآن كريم وتجويد أونلاين')
        self.assertContains(r, 'مشرفة حلقات قرآن')
        for slug in ('quran-teacher', 'quran-supervisor'):
            r = self.client.get(f'/jobs/{slug}/')
            self.assertEqual(r.status_code, 200)
            html = r.content.decode()
            self.assertIn('"@type": "JobPosting"', html)
            self.assertNotIn('noindex', html.split('</head>')[0])

    def test_teacher_has_requested_questions(self):
        labels = ' | '.join(self.job.questions.values_list('label', flat=True))
        for s in ('صورة البطاقة', 'الشهادات', 'سورة الطلاق', 'الإدغام', 'السيرة الذاتية', 'الجنسية', 'المحافظة'):
            self.assertIn(s, labels)
        talaq = self.job.questions.get(qtype='audio', quran_ref='65:1-5')
        self.assertEqual([a for a, _ in talaq.quran_verses()], [1, 2, 3, 4, 5])

    def test_full_submission_saves_answers_and_private_files(self):
        r = self.client.post('/jobs/quran-teacher/', self._payload(self.job), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200, r.content.decode())
        self.assertTrue(r.json()['ok'])
        app = Application.objects.get()
        self.assertEqual((app.name, app.phone, app.age, app.city), ('فاطمة أحمد محمد', '+201012345678', '26', 'القاهرة'))
        self.assertEqual(app.files.filter(mime='audio/webm').count(), 2)
        self.assertGreaterEqual(app.files.count(), 4)
        f = ApplicationFile.objects.filter(mime='audio/webm').first()
        self.assertEqual(self.client.get(f'/staff/job-files/{f.pk}/').status_code, 302)  # مش متاح للزوار
        admin = get_user_model().objects.create_superuser('boss', 'b@example.com', 'x-Strong-pass-1')
        self.client.force_login(admin)
        r = self.client.get(f'/staff/job-files/{f.pk}/')
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'audio/webm'))
        r = self.client.get(f'/admin/careers/application/{app.pk}/change/')
        self.assertContains(r, '<audio')
        self.assertContains(r, 'سورة الطلاق')

    def test_basic_conditions_block(self):
        data = self._payload(self.job)
        grad = self.job.questions.get(label='هل أنهيتِ الدراسة؟')
        data[grad.key] = 'لا'
        r = self.client.post('/jobs/quran-teacher/', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 400)
        self.assertIn('خريجة', r.json()['errors'][grad.key])
        self.assertFalse(Application.objects.exists())

    def test_missing_recording_and_experience(self):
        talaq = self.job.questions.get(quran_ref='65:1-5')
        years = self.job.questions.get(label='سنوات الخبرة أونلاين')
        data = self._payload(self.job, skip=talaq.key)
        data[years.key] = '0'
        r = self.client.post('/jobs/quran-teacher/', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        errs = r.json()['errors']
        self.assertIn(talaq.key, errs)
        self.assertIn('سنة', errs[years.key])

    def test_admin_edits_change_the_form(self):
        q = FormQuestion.objects.create(job=self.job, step=self.job.steps.first(), order=99, qtype='radio',
                                        label='هل لديك خبرة في تعليم غير الناطقين بالعربية؟', choices='نعم\nلا')
        self.assertContains(self.client.get('/jobs/quran-teacher/'), 'غير الناطقين بالعربية')
        data = self._payload(self.job)
        data.pop(q.key)
        r = self.client.post('/jobs/quran-teacher/', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(q.key, r.json()['errors'])
        q.is_active = False
        q.save()
        self.assertNotContains(self.client.get('/jobs/quran-teacher/'), 'غير الناطقين بالعربية')

    def test_supervisor_submission(self):
        job = JobOpening.objects.get(slug='quran-supervisor')
        data = self._payload(job)
        for q in job.questions.filter(qtype='files', required=True):
            data[q.key] = SimpleUploadedFile('cv.pdf', b'%PDF-1.4' + b'0' * 300, content_type='application/pdf')
        r = self.client.post('/jobs/quran-supervisor/', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(r.json()['ok'], r.content.decode())
        self.assertEqual(Application.objects.get().job, job)

    def test_inactive_job_hidden_and_sitemap(self):
        self.assertIn('/jobs/quran-supervisor/', self.client.get('/sitemap.xml').content.decode())
        JobOpening.objects.filter(slug='quran-supervisor').update(is_active=False)
        cache.clear()  # السايت ماب متخزن مؤقتًا
        self.assertEqual(self.client.get('/jobs/quran-supervisor/').status_code, 404)
        self.assertNotIn('/jobs/quran-supervisor/', self.client.get('/sitemap.xml').content.decode())

    def test_honeypot(self):
        r = self.client.post('/jobs/quran-teacher/', {'website': 'spam'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(r.json()['ok'])
        self.assertFalse(Application.objects.exists())
