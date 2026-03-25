from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
from unidecode import unidecode
import re

class QuestionCategory(models.Model):
    """فئات الأسئلة لتنظيم المحتوى"""
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    slug = models.SlugField(unique=True, verbose_name="الرابط")
    icon = models.CharField(max_length=50, blank=True, verbose_name="الأيقونة")
    description = models.TextField(blank=True, verbose_name="الوصف")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    
    class Meta:
        verbose_name = "فئة الأسئلة"
        verbose_name_plural = "فئات الأسئلة"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_questions_count(self):
        return self.publicquestion_set.filter(status='approved').count()

class PublicQuestion(models.Model):
    """النموذج الرئيسي للسؤال مع كل الحماية"""
    
    STATUS_CHOICES = [
        ('pending', '⏳ قيد المراجعة'),
        ('approved', '✅ معتمد ونشر'),
        ('rejected', '❌ مرفوض'),
        ('spam', '🚫 سبام'),
    ]
    
    # معلومات الزائر
    visitor_name = models.CharField(
        max_length=100, 
        verbose_name="الاسم",
        validators=[MinLengthValidator(2, message="الاسم يجب أن يكون حرفين على الأقل")]
    )
    visitor_email = models.EmailField(verbose_name="البريد الإلكتروني", blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True, verbose_name="الهاتف")
    notification_sent = models.BooleanField(default=False, verbose_name="تم إرسال إشعار")
    
    # محتوى السؤال
    title = models.CharField(
        max_length=200, 
        verbose_name="عنوان السؤال",
        validators=[MinLengthValidator(10, message="العنوان يجب أن يكون 10 أحرف على الأقل")],
        help_text="عنوان واضح ومختصر للسؤال"
    )
    question_text = models.TextField(
        verbose_name="تفاصيل السؤال",
        validators=[MinLengthValidator(20, message="السؤال يجب أن يكون 20 حرف على الأقل")],
        help_text="اشرح سؤالك بالتفصيل"
    )
    category = models.ForeignKey(
        QuestionCategory, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        verbose_name="الفئة"
    )
    
    # معلومات تلقائية للأمان
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, verbose_name="متصفح الزائر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    # حالة المراجعة
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES,
        default='pending', 
        verbose_name="حالة السؤال",
        db_index=True
    )
    
    # تفاعل المستخدمين
    view_count = models.PositiveIntegerField(default=0, verbose_name="عدد المشاهدات")
    is_frequent = models.BooleanField(default=False, verbose_name="سؤال متكرر")
    
    # SEO
    slug = models.SlugField(
        max_length=250, 
        unique=True, 
        blank=True, 
        verbose_name="رابط السؤال",
        db_index=True,
        allow_unicode=True
    )
    meta_description = models.TextField(
        max_length=160, 
        blank=True,
        verbose_name="وصف للبحث",
        help_text="وصف مختصر يظهر في نتائج محركات البحث"
    )
    
    class Meta:
        verbose_name = "سؤال عام"
        verbose_name_plural = "الأسئلة العامة"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]}... - {self.visitor_name}"
    
    def save(self, *args, **kwargs):
        # إنشاء slug فريد يدعم العربية
        if not self.slug:
            # إنشاء slug من العنوان مع استبدال المسافات بشرطات
            arabic_slug = self.title.strip().replace(' ', '-')
            # إزالة أي أحرف غير مرغوبة
            arabic_slug = re.sub(r'[^\w\-]', '', arabic_slug)
            self.slug = arabic_slug
        
        # التحقق من عدم تكرار الـ slug
        original_slug = self.slug
        counter = 1
        while PublicQuestion.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            self.slug = f'{original_slug}-{counter}'
            counter += 1
        
        # إنشاء meta description تلقائي
        if not self.meta_description and self.question_text:
            self.meta_description = self.question_text[:155] + "..."
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('qna:question_detail', kwargs={'slug': self.slug})
    
    def has_official_answer(self):
        """تحقق مما إذا كان للسؤال إجابة رسمية من المعلم"""
        return hasattr(self, 'official_answer')
    
    def get_community_answers(self):
        """الحصول على إجابات المجتمع (غير الرسمية)"""
        return self.answers.filter(is_official=False)
    
    def increment_views(self):
        """زيادة عداد المشاهدات"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])
        self.refresh_from_db()

class QuestionAnswer(models.Model):
    """إجابة المعلم أو المشرف"""
    question = models.OneToOneField(
        PublicQuestion, 
        on_delete=models.CASCADE,
        related_name='official_answer', 
        verbose_name="السؤال"
    )
    answer_text = models.TextField(
        verbose_name="نص الإجابة",
        validators=[MinLengthValidator(20, message="الإجابة يجب أن تكون 20 حرف على الأقل")]
    )
    
    # من أجاب
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="أجاب بواسطة"
    )
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإجابة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    # تقييم الجودة
    is_featured = models.BooleanField(default=False, verbose_name="إجابة مميزة")
    likes = models.PositiveIntegerField(default=0, verbose_name="الإعجابات")
    
    class Meta:
        verbose_name = "إجابة رسمية"
        verbose_name_plural = "الإجابات الرسمية"
        ordering = ['-answered_at']
    
    def __str__(self):
        return f"إجابة على: {self.question.title[:30]}"
    
    def save(self, *args, **kwargs):
        # تحديث حالة السؤال تلقائياً عند الإجابة
        if not self.pk and self.question.status == 'pending':
            self.question.status = 'approved'
            self.question.save(update_fields=['status'])
        super().save(*args, **kwargs)

class CommunityAnswer(models.Model):
    """إجابات المجتمع من المستخدمين والزوار"""
    question = models.ForeignKey(
        PublicQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="السؤال"
    )
    answer_text = models.TextField(
        verbose_name="نص الإجابة",
        validators=[MinLengthValidator(20, message="الإجابة يجب أن تكون 20 حرف على الأقل")],
        help_text="اكتب إجابتك بالتفصيل"
    )
    
    # معلومات المجيب (مسجل أو زائر)
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_answers',
        null=True,
        blank=True,
        verbose_name="المستخدم"
    )
    visitor_name = models.CharField(
        max_length=100, 
        verbose_name="اسم الزائر", 
        blank=True,
        help_text="اكتب اسمك إذا لم تكن مسجلاً"
    )
    visitor_email = models.EmailField(
        verbose_name="البريد الإلكتروني", 
        blank=True,
        help_text="اختياري - للإشعارات"
    )
    
    # معلومات التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    # حالة الإجابة
    is_verified = models.BooleanField(default=False, verbose_name="تم التحقق")
    is_spam = models.BooleanField(default=False, verbose_name="محتوى غير مرغوب")
    likes = models.PositiveIntegerField(default=0, verbose_name="الإعجابات")
    
    # معلومات تلقائية للأمان
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, verbose_name="متصفح المستخدم")
    
    class Meta:
        verbose_name = "إجابة المجتمع"
        verbose_name_plural = "إجابات المجتمع"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['question', '-created_at']),
            models.Index(fields=['is_verified', '-created_at']),
        ]
    
    def __str__(self):
        return f"إجابة مجتمعية على: {self.question.title[:30]}"
    
    def save(self, *args, **kwargs):
        # تحديث حالة السؤال تلقائياً عند وجود إجابات مجتمعية
        if not self.pk and self.question.status == 'pending':
            self.question.status = 'approved'
            self.question.save(update_fields=['status'])
        
        # إذا كان المستخدم مسجلاً، لا نحتاج لاسم الزائر
        if self.answered_by and self.visitor_name:
            self.visitor_name = ""
            
        super().save(*args, **kwargs)
    
    def get_answerer_name(self):
        """الحصول على اسم المجيب"""
        if self.answered_by:
            return self.answered_by.get_full_name() or self.answered_by.username
        return self.visitor_name or "مستخدم مجهول"
    
    def get_answerer_initials(self):
        """الحصول على الأحرف الأولى من اسم المجيب"""
        name = self.get_answerer_name()
        if name:
            return name[0].upper()
        return "?"

class UserVote(models.Model):
    """لتسجيل تصويت المستخدمين على الإجابات الرسمية"""
    answer = models.ForeignKey(
        QuestionAnswer, 
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="الإجابة"
    )
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التصويت")
    
    class Meta:
        verbose_name = "تصويت رسمي"
        verbose_name_plural = "التصويتات الرسمية"
        unique_together = ['answer', 'ip_address']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"تصويت على: {self.answer.question.title[:30]}"

class CommunityAnswerVote(models.Model):
    """لتسجيل تصويت المستخدمين على إجابات المجتمع"""
    answer = models.ForeignKey(
        CommunityAnswer,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="إجابة المجتمع"
    )
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التصويت")
    
    class Meta:
        verbose_name = "تصويت مجتمعي"
        verbose_name_plural = "التصويتات المجتمعية"
        unique_together = ['answer', 'ip_address']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"تصويت على إجابة مجتمعية"

class QuestionReport(models.Model):
    """لتسجيل الإبلاغ عن أسئلة أو إجابات غير لائقة"""
    
    REPORT_TYPES = [
        ('spam', 'محتوى ترويجي'),
        ('inappropriate', 'محتوى غير لائق'),
        ('incorrect', 'معلومات غير صحيحة'),
        ('duplicate', 'سؤال مكرر'),
        ('other', 'أخرى'),
    ]
    
    question = models.ForeignKey(
        PublicQuestion,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="السؤال"
    )
    answer = models.ForeignKey(
        CommunityAnswer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="الإجابة (إذا كان الإبلاغ عليها)"
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        verbose_name="نوع الإبلاغ"
    )
    description = models.TextField(
        verbose_name="تفاصيل الإبلاغ",
        help_text="اشرح سبب الإبلاغ"
    )
    reporter_ip = models.GenericIPAddressField(verbose_name="عنوان IP المبلغ")
    reporter_email = models.EmailField(
        verbose_name="البريد الإلكتروني",
        blank=True,
        help_text="اختياري - للتواصل معك"
    )
    is_resolved = models.BooleanField(default=False, verbose_name="تم الحل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإبلاغ")
    
    class Meta:
        verbose_name = "إبلاغ"
        verbose_name_plural = "الإبلاغات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"إبلاغ على: {self.question.title[:30]}"

class QuestionSubscription(models.Model):
    """اشتراكات المستخدمين للتنبيه عند وجود إجابات جديدة"""
    question = models.ForeignKey(
        PublicQuestion,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="السؤال"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='question_subscriptions',
        verbose_name="المستخدم"
    )
    email = models.EmailField(
        verbose_name="البريد الإلكتروني",
        blank=True,
        help_text="للتسجيل بدون حساب"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاشتراك")
    
    class Meta:
        verbose_name = "اشتراك"
        verbose_name_plural = "الاشتراكات"
        unique_together = [['question', 'user'], ['question', 'email']]
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} مشترك في: {self.question.title[:30]}"
        return f"{self.email} مشترك في: {self.question.title[:30]}"