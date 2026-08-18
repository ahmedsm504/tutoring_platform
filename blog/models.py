from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import uuid
import cloudinary.uploader

User = get_user_model()

class Category(models.Model):
    """تصنيفات المقالات"""
    name = models.CharField(max_length=100, verbose_name='اسم التصنيف')
    slug = models.SlugField(unique=True, blank=True, allow_unicode=True)
    description = models.TextField(blank=True, verbose_name='الوصف')
    icon = models.CharField(max_length=50, blank=True, help_text='مثال: 📚', verbose_name='أيقونة')
    
    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Post(models.Model):
    """مقالات البلوج"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('published', 'منشور'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='العنوان')
    slug = models.SlugField(unique=True, blank=True, allow_unicode=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', verbose_name='الكاتب')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name='التصنيف')
    
    # المحتوى
    excerpt = models.TextField(max_length=300, blank=True, verbose_name='مقتطف', help_text='ملخص قصير للمقال')
    content = models.TextField(verbose_name='المحتوى')
    image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name='الصورة الرئيسية')
    cloud_url = models.URLField(blank=True, null=True, verbose_name='رابط الصورة على كلاود')
    # ✅ جديد: نص بديل مخصص للصورة الرئيسية (يفيد الـ SEO وقارئ الشاشة).
    # اختياري تماماً، والمقالات القديمة تعمل بدونه (يتم استخدام العنوان بدلاً منه تلقائياً).
    image_alt = models.CharField(max_length=200, blank=True, verbose_name='النص البديل للصورة (Alt)',
                                  help_text='اختياري - لو تُرك فارغاً سيُستخدم عنوان المقال تلقائياً')

    # الحالة والتواريخ
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ النشر')
    
    # إحصائيات
    views_count = models.PositiveIntegerField(default=0, verbose_name='عدد المشاهدات')
    reading_time = models.PositiveIntegerField(default=5, verbose_name='وقت القراءة (دقائق)')
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='وصف SEO')
    keywords = models.CharField(max_length=200, blank=True, verbose_name='كلمات مفتاحية')
    
    # الميزات
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    allow_comments = models.BooleanField(default=True, verbose_name='السماح بالتعليقات')
    
    class Meta:
        verbose_name = 'مقال'
        verbose_name_plural = 'المقالات'
        ordering = ['-published_at', '-created_at']
    

    def save(self, *args, **kwargs):
        # توليد slug تلقائياً
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            original = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original}-{counter}"
                counter += 1
        
        # رفع الصورة على Cloudinary لو موجودة ولم يتم رفعها قبل
        if self.image and not self.cloud_url:
            result = cloudinary.uploader.upload(self.image)
            self.cloud_url = result['secure_url']
        
        # حساب وقت القراءة
        word_count = len(self.content.split())
        self.reading_time = max(1, round(word_count / 200))
        
        # إنشاء excerpt تلقائياً إذا لم يكن موجود
        if not self.excerpt and self.content:
            self.excerpt = self.content[:250] + '...'
        
        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.title
    
    def increment_views(self):
        """زيادة عدد المشاهدات"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def display_image_alt(self):
        """النص البديل النهائي المستخدم فعلياً في القوالب"""
        return self.image_alt or self.title


class PostImage(models.Model):
    """
    ✅ جديد: معرض صور إضافي للمقال.
    يسمح بإضافة أي عدد من الصور لكل مقال (بجانب الصورة الرئيسية) بدون التأثير
    على المقالات القديمة، لأن هذا موديل منفصل تماماً ولا يعدّل جدول Post.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='gallery_images', verbose_name='المقال')
    image = models.ImageField(upload_to='blog/gallery/', verbose_name='الصورة')
    cloud_url = models.URLField(blank=True, null=True, verbose_name='رابط الصورة على كلاود')
    caption = models.CharField(max_length=200, blank=True, verbose_name='وصف الصورة (Alt/Caption)')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'صورة إضافية'
        verbose_name_plural = '📷 معرض الصور'
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        if self.image and not self.cloud_url:
            result = cloudinary.uploader.upload(self.image)
            self.cloud_url = result['secure_url']
        super().save(*args, **kwargs)

    def __str__(self):
        return f"صورة - {self.post.title[:30]}"

    @property
    def display_alt(self):
        return self.caption or self.post.title


class PostVideo(models.Model):
    """
    ✅ جديد: فيديوهات يوتيوب / تيك توك مرتبطة بالمقال.
    يكفي لصق رابط الفيديو العادي (يوتيوب أو تيك توك) وسيتم تحويله تلقائياً
    لصيغة العرض (embed) المناسبة في صفحة المقال.
    """
    PLATFORM_CHOICES = [
        ('youtube', 'يوتيوب'),
        ('tiktok', 'تيك توك'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='videos', verbose_name='المقال')
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='youtube', verbose_name='المنصة')
    url = models.URLField(verbose_name='رابط الفيديو', help_text='الصق رابط يوتيوب أو تيك توك هنا مباشرة')
    title = models.CharField(max_length=200, blank=True, verbose_name='عنوان الفيديو (اختياري)')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'فيديو'
        verbose_name_plural = '🎬 الفيديوهات'
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        # اكتشاف المنصة تلقائياً من الرابط لو المستخدم نساها
        url_lower = (self.url or '').lower()
        if 'tiktok.com' in url_lower:
            self.platform = 'tiktok'
        elif 'youtu' in url_lower:
            self.platform = 'youtube'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"فيديو - {self.post.title[:30]}"

    @property
    def youtube_id(self):
        """يستخرج معرّف فيديو اليوتيوب من أي صيغة رابط شائعة"""
        url = (self.url or '').strip()
        video_id = None
        if 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1]
        elif 'watch?v=' in url:
            video_id = url.split('watch?v=')[-1]
        elif '/embed/' in url:
            video_id = url.split('/embed/')[-1]
        elif '/shorts/' in url:
            video_id = url.split('/shorts/')[-1]
        if video_id:
            return video_id.split('?')[0].split('&')[0].split('/')[0]
        return None

    @property
    def embed_url(self):
        """رابط جاهز للعرض داخل iframe (يوتيوب فقط، تيك توك له embed خاص في القالب)"""
        if self.platform == 'youtube' and self.youtube_id:
            return f"https://www.youtube.com/embed/{self.youtube_id}"
        return self.url

    @property
    def tiktok_video_id(self):
        if self.platform == 'tiktok':
            parts = self.url.strip().rstrip('/').split('/video/')
            if len(parts) > 1:
                return parts[1].split('?')[0]
        return None

    @property
    def thumbnail_url(self):
        """صورة مصغّرة للفيديو (تفيد في Schema.org VideoObject)"""
        if self.platform == 'youtube' and self.youtube_id:
            return f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        return None


class Comment(models.Model):
    """تعليقات على المقالات"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='المقال')
    author_name = models.CharField(max_length=100, verbose_name='الاسم')
    author_email = models.EmailField(verbose_name='البريد الإلكتروني')
    content = models.TextField(verbose_name='التعليق')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='التاريخ')
    is_approved = models.BooleanField(default=False, verbose_name='موافق عليه')
    
    class Meta:
        verbose_name = 'تعليق'
        verbose_name_plural = 'التعليقات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author_name} - {self.post.title[:30]}"
    

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Post)
def clear_sitemap_cache(sender, instance, **kwargs):
    """مسح كاش الـ Sitemap عند نشر مقال جديد"""
    cache.clear()
