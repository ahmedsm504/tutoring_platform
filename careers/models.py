"""قسم التوظيف (معلمات، مشرفات، وأي وظيفة جديدة) — كله بيتعدل من لوحة الأدمن:
- JobOpening: صفحة الوظيفة (العناوين والشروط والراتب والأسئلة الشائعة وبيانات جوجل للوظائف).
- FormStep / FormQuestion: خطوات النموذج وأسئلته (تضيف/تعدل/تمسح/ترتب من غير كود).
- Application: الطلب المرسل؛ الإجابات بتتحفظ نصًا مع السؤال، فلو عدّلت الأسئلة بعدين الطلبات القديمة متتلخبطش.
- ApplicationFile: المرفقات (صور/PDF/تسجيلات صوتية) جوه قاعدة البيانات: خاصة ومتتمسحش مع النشر على Railway.
"""
from django.db import models
from django.urls import reverse

LINES_HELP = 'كل بند في سطر.'


class JobOpening(models.Model):
    EMPLOYMENT = [('PART_TIME', 'دوام جزئي'), ('FULL_TIME', 'دوام كامل'), ('CONTRACTOR', 'تعاقد / بالساعة')]
    UNIT = [('HOUR', 'للساعة'), ('MONTH', 'شهريًا')]

    title = models.CharField('اسم الوظيفة', max_length=120, help_text='مثال: معلمة قرآن وتجويد أونلاين')
    slug = models.SlugField('الرابط', max_length=60, unique=True, help_text='بالإنجليزي، مثال: quran-teacher ← alagme.com/jobs/quran-teacher/')
    is_active = models.BooleanField('مفتوحة للتقديم', default=True)
    order = models.PositiveSmallIntegerField('الترتيب', default=0)

    # الصفحة
    chip = models.CharField('الشارة الصغيرة فوق العنوان', max_length=80, blank=True, default='✨ يا مرحبًا بأهل القرآن')
    h1 = models.CharField('العنوان الرئيسي', max_length=150)
    subtitle = models.CharField('العنوان الفرعي', max_length=200, blank=True)
    intro = models.TextField('المقدمة', blank=True)
    features = models.TextField('3 مميزات تحت المقدمة', blank=True,
                                help_text='كل سطر: «🛡️ العنوان | الوصف». ' + LINES_HELP)
    summary = models.TextField('نقاط «ملخص سريع»', blank=True, help_text=LINES_HELP)
    important_note = models.CharField('المعلومة المهمة (الراتب مثلًا)', max_length=200, blank=True)
    requirements = models.TextField('الشروط الأساسية', blank=True, help_text='كل سطر: «📖 الشرط | توضيح». ' + LINES_HELP)
    process = models.TextField('خطوات التوظيف بعد التقديم', blank=True, help_text='كل سطر: «العنوان | الوصف». ' + LINES_HELP)
    faq = models.TextField('الأسئلة الشائعة', blank=True, help_text='كل سطر: «السؤال | الإجابة». ' + LINES_HELP)
    card_text = models.CharField('وصف قصير في صفحة كل الوظائف', max_length=220, blank=True)
    icon = models.CharField('أيقونة (إيموجي)', max_length=8, default='👩‍🏫')
    thanks_text = models.TextField('رسالة الشكر بعد الإرسال', blank=True,
                                   default='وصلنا طلبك بنجاح، جزاكِ الله خيرًا. ستراجع الإدارة بياناتك وتسجيلاتك، '
                                           'وإذا كان طلبك مناسبًا سنتواصل معك على واتساب لتحديد موعد الاختبار.')

    # السيو وجوجل للوظائف
    meta_title = models.CharField('عنوان جوجل (Title)', max_length=90, blank=True)
    meta_description = models.CharField('وصف جوجل', max_length=170, blank=True)
    keywords = models.CharField('كلمات مفتاحية', max_length=300, blank=True)
    og_image = models.CharField('صورة المشاركة (مسار في static)', max_length=120, blank=True, default='images/og-jobs.jpg')
    employment_type = models.CharField('نوع العمل', max_length=12, choices=EMPLOYMENT, default='PART_TIME')
    salary_value = models.DecimalField('الراتب (رقم فقط، اختياري)', max_digits=9, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField('أقصى راتب (لو فيه نطاق «من … إلى»)', max_digits=9, decimal_places=2,
                                     null=True, blank=True)
    salary_unit = models.CharField('الراتب لكل', max_length=6, choices=UNIT, default='HOUR')
    salary_currency = models.CharField('العملة', max_length=3, default='EGP')
    experience_months = models.PositiveSmallIntegerField('أقل خبرة بالشهور (اختياري)', null=True, blank=True)
    requires_degree = models.BooleanField('يشترط مؤهل جامعي', default=True)
    date_posted = models.DateField('تاريخ النشر')
    valid_through = models.DateField('آخر موعد للتقديم (لجوجل)', null=True, blank=True)

    class Meta:
        verbose_name = 'وظيفة'
        verbose_name_plural = 'الوظائف ونماذج التقديم'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('careers:apply', args=[self.slug])

    @staticmethod
    def _rows(text, parts=2):
        out = []
        for line in (text or '').splitlines():
            line = line.strip()
            if not line:
                continue
            bits = [b.strip() for b in line.split('|', parts - 1)]
            out.append(bits + [''] * (parts - len(bits)))
        return out

    def _icon_rows(self, text):
        rows = []
        for title, desc in self._rows(text):
            icon = ''
            if title and not title[0].isalnum() and ' ' in title:
                icon, title = title.split(' ', 1)
            rows.append((icon, title, desc))
        return rows

    def features_list(self):
        return self._icon_rows(self.features)

    def requirements_list(self):
        return self._icon_rows(self.requirements)

    def summary_list(self):
        return [r[0] for r in self._rows(self.summary, 1)]

    def process_list(self):
        return self._rows(self.process)

    def faq_list(self):
        return [r for r in self._rows(self.faq) if r[1]]


class FormStep(models.Model):
    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='steps', verbose_name='الوظيفة')
    order = models.PositiveSmallIntegerField('الترتيب', default=1)
    title = models.CharField('اسم الخطوة', max_length=80)

    class Meta:
        verbose_name = 'خطوة'
        verbose_name_plural = 'خطوات النموذج'
        ordering = ['order', 'pk']

    def __str__(self):
        return f'{self.order}) {self.title}'


class FormQuestion(models.Model):
    TYPES = [
        ('text', 'نص قصير'), ('textarea', 'نص طويل'), ('number', 'رقم'), ('phone', 'رقم هاتف / واتساب'),
        ('radio', 'اختيار واحد (أزرار)'), ('select', 'قائمة منسدلة'), ('checkboxes', 'اختيار متعدد'),
        ('suggest', 'نص مع اقتراحات'), ('yesno', 'نعم / لا'), ('agree', 'موافقة على شرط (مربع اختيار)'),
        ('files', 'رفع صور / ملفات'), ('audio', 'تسجيل صوتي (تسجيل مباشر أو رفع ملف)'), ('info', 'فقرة توضيحية فقط'),
    ]
    ROLES = [('', '—'), ('name', 'اسم المتقدمة'), ('phone', 'رقم التواصل'), ('age', 'السن'), ('city', 'المحافظة / المدينة')]
    FILE_KINDS = [('images', 'صور أو PDF'), ('docs', 'PDF أو Word أو صور')]

    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='questions', verbose_name='الوظيفة')
    step = models.ForeignKey(FormStep, on_delete=models.CASCADE, related_name='questions', verbose_name='الخطوة')
    order = models.PositiveSmallIntegerField('الترتيب', default=1)
    is_active = models.BooleanField('ظاهر', default=True)
    qtype = models.CharField('نوع السؤال', max_length=12, choices=TYPES, default='text')
    label = models.CharField('السؤال', max_length=250)
    help_text = models.CharField('توضيح تحت السؤال', max_length=300, blank=True)
    intro = models.TextField('شرح فوق خانة الإجابة', blank=True)
    placeholder = models.CharField('مثال داخل الخانة', max_length=200, blank=True)
    required = models.BooleanField('إجباري', default=True)
    choices = models.TextField('الاختيارات', blank=True, help_text='للاختيار الواحد / المتعدد / القائمة / الاقتراحات: كل اختيار في سطر.')
    required_answer = models.CharField('إجابة لازمة (شرط أساسي)', max_length=100, blank=True,
                                       help_text='مثال: «نعم». لو المتقدمة اختارت غيرها يظهر لها «رسالة الرفض» ومتقدرش تكمل.')
    reject_message = models.CharField('رسالة الرفض', max_length=200, blank=True)
    policy_title = models.CharField('عنوان مربع السياسة (اختياري)', max_length=100, blank=True)
    policy_text = models.TextField('نص السياسة / الشرط (يظهر في مربع فوق السؤال)', blank=True)
    min_length = models.PositiveSmallIntegerField('أقل عدد حروف (للنص الطويل)', null=True, blank=True)
    min_value = models.IntegerField('أقل رقم', null=True, blank=True)
    max_value = models.IntegerField('أكبر رقم', null=True, blank=True)
    min_words = models.PositiveSmallIntegerField('أقل عدد كلمات (مثلًا 3 للاسم الثلاثي)', null=True, blank=True)
    max_files = models.PositiveSmallIntegerField('أقصى عدد ملفات', default=1)
    file_kind = models.CharField('نوع الملفات المسموحة', max_length=8, choices=FILE_KINDS, default='images')
    quran_ref = models.CharField('آيات تظهر للقراءة منها', max_length=20, blank=True,
                                 help_text='للتسجيل الصوتي: «رقم السورة:من-إلى» مثال 65:1-5 (أول وجه من الطلاق).')
    half_width = models.BooleanField('نصف عرض (خانتين جنب بعض)', default=False)
    highlight = models.BooleanField('سؤال مميز (إطار أزرق)', default=False)
    role = models.CharField('يستخدم كـ', max_length=6, choices=ROLES, blank=True,
                            help_text='يظهر في قائمة الطلبات في الأدمن.')

    class Meta:
        verbose_name = 'سؤال'
        verbose_name_plural = 'أسئلة النموذج'
        ordering = ['step__order', 'order', 'pk']

    def __str__(self):
        return self.label

    @property
    def key(self):
        return f'q{self.pk}'

    def choice_list(self):
        if self.qtype == 'yesno':
            return ['نعم', 'لا']
        return [c.strip() for c in (self.choices or '').splitlines() if c.strip()]

    def quran_verses(self):
        import re
        m = re.fullmatch(r'\s*(\d{1,3})\s*:\s*(\d{1,3})\s*-\s*(\d{1,3})\s*', self.quran_ref or '')
        if not m:
            return []
        s, a, b = map(int, m.groups())
        try:
            from learning import quran
            return [(n, t) for n, t in quran.verses(s) if a <= n <= b]
        except Exception:
            return []


class Application(models.Model):
    STATUS = [('new', 'جديد'), ('reviewing', 'قيد المراجعة'), ('interview', 'اختبار / مقابلة'),
              ('accepted', 'مقبول'), ('rejected', 'مرفوض')]
    job = models.ForeignKey(JobOpening, on_delete=models.PROTECT, related_name='applications', verbose_name='الوظيفة')
    status = models.CharField('الحالة', max_length=10, choices=STATUS, default='new', db_index=True)
    admin_notes = models.TextField('ملاحظات الإدارة', blank=True)
    created_at = models.DateTimeField('تاريخ التقديم', auto_now_add=True, db_index=True)
    name = models.CharField('الاسم', max_length=150, blank=True)
    phone = models.CharField('رقم التواصل', max_length=25, blank=True)
    age = models.CharField('السن', max_length=10, blank=True)
    city = models.CharField('المحافظة', max_length=80, blank=True)
    answers = models.JSONField('الإجابات', default=list)
    ip = models.GenericIPAddressField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = 'طلب توظيف'
        verbose_name_plural = 'طلبات التوظيف'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name or "طلب"} – {self.job}'


class ApplicationFile(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='files')
    question = models.ForeignKey(FormQuestion, on_delete=models.SET_NULL, null=True, blank=True)
    label = models.CharField('السؤال', max_length=250)
    name = models.CharField('اسم الملف', max_length=200)
    mime = models.CharField(max_length=100)
    size = models.PositiveIntegerField('الحجم (بايت)')
    data = models.BinaryField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مرفق'
        verbose_name_plural = 'مرفقات الطلبات'
        ordering = ['application', 'pk']

    def __str__(self):
        return f'{self.label}: {self.name}'

    @property
    def is_image(self):
        return self.mime.startswith('image/')

    @property
    def is_audio(self):
        return self.mime.startswith('audio/')
