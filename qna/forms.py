# qna/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import PublicQuestion, QuestionCategory, CommunityAnswer
import re

class PublicQuestionForm(forms.ModelForm):
    """نموذج السؤال مع كل شروط التحقق"""
    
    agree_to_terms = forms.BooleanField(
        required=True,
        label="أوافق على شروط النشر وأن سؤالي يخضع للمراجعة",
        error_messages={
            'required': 'يجب الموافقة على شروط النشر'
        }
    )
    
    class Meta:
        model = PublicQuestion
        fields = ['visitor_name', 'visitor_email', 'visitor_phone', 
                 'category', 'title', 'question_text']
        
        widgets = {
            'visitor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: محمد أحمد علي',
                'required': True
            }),
            'visitor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com (لن يتم نشره)',
            }),
            'visitor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+20 123 456 7890 (اختياري)',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: كيف أشجع طفلي البالغ ٦ سنوات على حفظ القرآن؟',
                'required': True
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'اكتب سؤالك بالتفصيل... (20 حرف على الأقل)',
                'required': True
            }),
        }
        
        labels = {
            'visitor_name': 'الاسم الكامل',
            'visitor_email': 'البريد الإلكتروني (لن ننشره)',
            'visitor_phone': 'رقم الهاتف (اختياري)',
            'category': 'اختر الفئة المناسبة',
            'title': 'عنوان السؤال',
            'question_text': 'تفاصيل السؤال',
        }
        
        help_texts = {
            'visitor_name': 'الاسم الحقيقي الثلاثي أو الرباعي',
            'visitor_email': 'لإرسال إشعار عند الرد على سؤالك',
            'title': 'عنوان واضح ومختصر (10-200 حرف)',
            'question_text': 'اشرح سؤالك بالتفصيل (20 حرف على الأقل)',
        }
    
    def clean_visitor_name(self):
        """التحقق من صحة الاسم"""
        name = self.cleaned_data.get('visitor_name', '').strip()
        
        if not name:
            raise ValidationError('الرجاء إدخال الاسم')
        
        # منع الأسماء الوهمية
        fake_names = [
            'مجهول', 'غير معروف', 'xxx', 'test', 'مستخدم', 
            'user', 'admin', 'زائر', 'visitor', 'aaa', 'zzz',
            'asdf', 'qwerty', 'anonymous'
        ]
        
        if name.lower() in fake_names:
            raise ValidationError('الرجاء إدخال اسمك الحقيقي')
        
        # التحقق من الطول
        if len(name) < 2:
            raise ValidationError('الاسم يجب أن يكون حرفين على الأقل')
        
        if len(name) > 100:
            raise ValidationError('الاسم طويل جداً')
        
        # التحقق من وجود أحرف فقط (مع السماح بالمسافات والأحرف العربية)
        if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', name):
            raise ValidationError('الاسم يجب أن يحتوي على أحرف فقط')
        
        # منع الأسماء المكررة (نفس الحرف)
        if len(set(name.replace(' ', ''))) <= 2:
            raise ValidationError('الرجاء إدخال اسم حقيقي')
        
        return name
    
    def clean_visitor_email(self):
        """التحقق من صحة البريد الإلكتروني"""
        email = self.cleaned_data.get('visitor_email', '').strip()
        
        if email:
            # منع البريد المؤقت
            temp_domains = [
                'tempmail.com', 'guerrillamail.com', '10minutemail.com',
                'mailinator.com', 'throwaway.email', 'temp-mail.org'
            ]
            
            domain = email.split('@')[-1].lower()
            if domain in temp_domains:
                raise ValidationError('لا يسمح باستخدام البريد الإلكتروني المؤقت')
        
        return email
    
    def clean_visitor_phone(self):
        """التحقق من صحة رقم الهاتف"""
        phone = self.cleaned_data.get('visitor_phone', '').strip()
        
        if phone:
            # إزالة المسافات والرموز
            phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
            
            # التحقق من أن الرقم يحتوي على أرقام فقط (مع السماح بـ +)
            if not re.match(r'^\+?[0-9]{10,15}$', phone_clean):
                raise ValidationError('رقم الهاتف غير صحيح')
        
        return phone
    
    def clean_title(self):
        """التحقق من صحة عنوان السؤال"""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise ValidationError('الرجاء إدخال عنوان السؤال')
        
        # التحقق من الطول
        if len(title) < 10:
            raise ValidationError('عنوان السؤال قصير جداً، اكتب شرحاً واضحاً (10 أحرف على الأقل)')
        
        if len(title) > 200:
            raise ValidationError('عنوان السؤال طويل جداً (200 حرف كحد أقصى)')
        
        # منع العناوين غير اللائقة
        inappropriate_words = [
            'سخيف', 'غبي', 'تافه', 'حقير', 'قذر', 'سيء',
            'stupid', 'idiot', 'bad', 'spam'
        ]
        
        title_lower = title.lower()
        for word in inappropriate_words:
            if word in title_lower:
                raise ValidationError('العنوان يحتوي على كلمات غير لائقة')
        
        # منع التكرار الزائد لنفس الحرف
        if re.search(r'(.)\1{4,}', title):
            raise ValidationError('العنوان يحتوي على تكرار غير طبيعي للأحرف')
        
        # منع العناوين بالأحرف الكبيرة فقط
        if title.isupper() and len(title) > 20:
            raise ValidationError('الرجاء عدم الكتابة بالأحرف الكبيرة فقط')
        
        return title
    
    def clean_question_text(self):
        """التحقق من صحة نص السؤال"""
        text = self.cleaned_data.get('question_text', '').strip()
        
        if not text:
            raise ValidationError('الرجاء إدخال تفاصيل السؤال')
        
        # التحقق من الطول
        if len(text) < 20:
            raise ValidationError('السؤال قصير جداً، اكتب تفاصيل أكثر (20 حرف على الأقل)')
        
        if len(text) > 5000:
            raise ValidationError('السؤال طويل جداً (5000 حرف كحد أقصى)')
        
        # منع الروابط (منع الإعلانات)
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        if url_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج روابط في السؤال')
        
        # منع البريد الإلكتروني في النص
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        if email_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج عناوين البريد الإلكتروني في السؤال')
        
        # منع أرقام الهواتف في النص
        phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}')
        if phone_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج أرقام الهواتف في السؤال')
        
        # منع التكرار الزائد لنفس الحرف
        if re.search(r'(.)\1{6,}', text):
            raise ValidationError('النص يحتوي على تكرار غير طبيعي للأحرف')
        
        # منع الكلمات غير اللائقة
        inappropriate_words = [
            'سخيف', 'غبي', 'تافه', 'حقير', 'قذر',
            'stupid', 'idiot', 'spam'
        ]
        
        text_lower = text.lower()
        for word in inappropriate_words:
            if word in text_lower:
                raise ValidationError('النص يحتوي على كلمات غير لائقة')
        
        return text
    
    def clean(self):
        """التحقق العام من النموذج"""
        cleaned_data = super().clean()
        
        title = cleaned_data.get('title', '')
        question_text = cleaned_data.get('question_text', '')
        
        # التحقق من عدم تكرار نفس المحتوى في العنوان والنص
        if title and question_text:
            if title.lower() == question_text.lower():
                raise ValidationError('العنوان والتفاصيل لا يمكن أن يكونا متطابقين')
        
        return cleaned_data

class CommunityAnswerForm(forms.ModelForm):
    """نموذج إجابة المجتمع"""
    
    agree_to_terms = forms.BooleanField(
        required=True,
        label="أوافق على شروط النشر وأن إجابتي تخضع للمراجعة",
        error_messages={
            'required': 'يجب الموافقة على شروط النشر'
        }
    )
    
    class Meta:
        model = CommunityAnswer
        fields = ['visitor_name', 'visitor_email', 'answer_text']
        
        widgets = {
            'visitor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسمك (اختياري إذا كنت مسجلاً)',
            }),
            'visitor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'بريدك الإلكتروني (لن يتم نشره - اختياري)',
            }),
            'answer_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'اكتب إجابتك بالتفصيل... (20 حرف على الأقل)',
                'required': True
            }),
        }
        
        labels = {
            'visitor_name': 'اسمك',
            'visitor_email': 'البريد الإلكتروني',
            'answer_text': 'إجابتك',
        }
        
        help_texts = {
            'visitor_name': 'اختياري - إذا كنت مسجلاً سيتم استخدام اسم حسابك',
            'visitor_email': 'اختياري - للإشعارات فقط',
            'answer_text': 'اكتب إجابة مفيدة ومختصرة',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # إذا كان المستخدم مسجلاً، لا نحتاج لاسم الزائر
        if self.user and self.user.is_authenticated:
            self.fields['visitor_name'].required = False
            self.fields['visitor_email'].required = False
    
    def clean_answer_text(self):
        """التحقق من صحة نص الإجابة"""
        text = self.cleaned_data.get('answer_text', '').strip()
        
        if not text:
            raise ValidationError('الرجاء إدخال نص الإجابة')
        
        # التحقق من الطول
        if len(text) < 20:
            raise ValidationError('الإجابة قصيرة جداً، اكتب تفاصيل أكثر (20 حرف على الأقل)')
        
        if len(text) > 2000:
            raise ValidationError('الإجابة طويلة جداً (2000 حرف كحد أقصى)')
        
        # منع الروابط (منع الإعلانات)
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        if url_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج روابط في الإجابة')
        
        # منع البريد الإلكتروني في النص
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        if email_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج عناوين البريد الإلكتروني في الإجابة')
        
        # منع أرقام الهواتف في النص
        phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}')
        if phone_pattern.search(text):
            raise ValidationError('لا يسمح بإدراج أرقام الهواتف في الإجابة')
        
        # منع الكلمات غير اللائقة
        inappropriate_words = [
            'سخيف', 'غبي', 'تافه', 'حقير', 'قذر',
            'stupid', 'idiot', 'spam'
        ]
        
        text_lower = text.lower()
        for word in inappropriate_words:
            if word in text_lower:
                raise ValidationError('النص يحتوي على كلمات غير لائقة')
        
        return text
    
    def clean_visitor_name(self):
        """التحقق من صحة اسم الزائر"""
        name = self.cleaned_data.get('visitor_name', '').strip()
        
        if self.user and self.user.is_authenticated:
            return ''  # لا نحتاج لاسم الزائر للمستخدم المسجل
        
        if not name:
            raise ValidationError('الرجاء إدخال اسمك')
        
        # منع الأسماء الوهمية
        fake_names = [
            'مجهول', 'غير معروف', 'xxx', 'test', 'مستخدم', 
            'user', 'admin', 'زائر', 'visitor', 'aaa', 'zzz'
        ]
        
        if name.lower() in fake_names:
            raise ValidationError('الرجاء إدخال اسمك الحقيقي')
        
        # التحقق من الطول
        if len(name) < 2:
            raise ValidationError('الاسم يجب أن يكون حرفين على الأقل')
        
        if len(name) > 100:
            raise ValidationError('الاسم طويل جداً')
        
        return name
    
    def save(self, commit=True):
        """حفظ النموذج مع ربط المستخدم المسجل"""
        answer = super().save(commit=False)
        
        if self.user and self.user.is_authenticated:
            answer.answered_by = self.user
            answer.visitor_name = ''
            answer.visitor_email = ''
        
        if commit:
            answer.save()
        
        return answer