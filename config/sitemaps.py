# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# استيراد الموديلات
try:
    from blog.models import Post, Category
    HAS_BLOG = True
except ImportError:
    HAS_BLOG = False

try:
    from accounts.models import TrialBooking
    HAS_ACCOUNTS = True
except ImportError:
    HAS_ACCOUNTS = False


class StaticViewSitemap(Sitemap):
    """Sitemap للصفحات الثابتة"""
    protocol = 'https'
    
    def items(self):
        """قائمة الصفحات الثابتة"""
        return [
            {'url': 'home', 'priority': 1.0, 'changefreq': 'daily'},
            {'url': 'pricing', 'priority': 0.9, 'changefreq': 'weekly'},
            {'url': 'about', 'priority': 0.7, 'changefreq': 'monthly'},
            {'url': 'quality_standards', 'priority': 0.7, 'changefreq': 'monthly'},
            {'url': 'contact', 'priority': 0.8, 'changefreq': 'monthly'},
            {'url': 'blog_list', 'priority': 0.8, 'changefreq': 'daily'},
            {'url': 'register', 'priority': 0.6, 'changefreq': 'yearly'},
            {'url': 'login', 'priority': 0.5, 'changefreq': 'yearly'},
        ]

    def location(self, obj):
        """URL لكل صفحة"""
        return reverse(obj['url'])
    
    def lastmod(self, obj):
        """آخر تعديل للصفحة"""
        return timezone.now()
    
    def changefreq(self, obj):
        """تكرار التغيير"""
        return obj['changefreq']
    
    def priority(self, obj):
        """أولوية الصفحة"""
        return obj['priority']


class BlogPostSitemap(Sitemap):
    """Sitemap لمقالات المدونة"""
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'
    limit = 1000  # عدد العناصر في كل sitemap

    def items(self):
        """جلب جميع المقالات المنشورة"""
        if not HAS_BLOG:
            return []
        return Post.objects.filter(status='published').order_by('-published_at')

    def lastmod(self, obj):
        """آخر تعديل للمقال"""
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.published_at

    def location(self, obj):
        """URL المقال"""
        return reverse('blog_detail', args=[obj.slug])
    
    def priority(self, obj):
        """أولوية المقال حسب المشاهدات والتاريخ"""
        # المقالات الحديثة والمميزة لها أولوية أعلى
        if hasattr(obj, 'is_featured') and obj.is_featured:
            return 0.9
        elif hasattr(obj, 'views_count') and obj.views_count > 100:
            return 0.85
        return 0.7


class BlogCategorySitemap(Sitemap):
    """Sitemap لتصنيفات المدونة"""
    changefreq = "weekly"
    priority = 0.7
    protocol = 'https'

    def items(self):
        """جلب جميع التصنيفات"""
        if not HAS_BLOG:
            return []
        return Category.objects.all().order_by('name')

    def lastmod(self, obj):
        """آخر تعديل للتصنيف"""
        if not HAS_BLOG:
            return timezone.now()
            
        # آخر مقال منشور في هذا التصنيف
        latest_post = Post.objects.filter(
            category=obj, 
            status='published'
        ).order_by('-published_at').first()
        
        return latest_post.published_at if latest_post else timezone.now()

    def location(self, obj):
        """URL التصنيف"""
        return reverse('category_posts', args=[obj.slug])


class PricingPackagesSitemap(Sitemap):
    """Sitemap للباقات التعليمية"""
    changefreq = "monthly"
    priority = 0.9
    protocol = 'https'

    def items(self):
        """قائمة الباقات الأربعة"""
        return [
            {
                'name': 'باقة البداية النورانية',
                'slug': 'beginner-package',
                'description': 'برنامج تحفيظ القرآن للأطفال',
                'anchor': 'beginner'
            },
            {
                'name': 'باقة الغراس الطيب',
                'slug': 'intermediate-package',
                'description': 'تحسين التلاوة وتصحيح الأخطاء',
                'anchor': 'intermediate'
            },
            {
                'name': 'باقة الهمة العالية',
                'slug': 'advanced-package',
                'description': 'حفظ القرآن للشباب',
                'anchor': 'advanced'
            },
            {
                'name': 'باقة سفراء القرآن',
                'slug': 'adults-package',
                'description': 'برنامج تحفيظ للكبار',
                'anchor': 'adults'
            },
        ]

    def location(self, item):
        """URL الباقة - الصفحة الرئيسية للباقات"""
        return reverse('pricing')

    def lastmod(self, item):
        """آخر تعديل"""
        return timezone.now()


class QualityStandardsSitemap(Sitemap):
    """Sitemap لأقسام مواثيق الجودة"""
    changefreq = "monthly"
    priority = 0.7
    protocol = 'https'

    def items(self):
        """أقسام مواثيق الجودة"""
        return [
            {'name': 'ميثاق المعلمة', 'anchor': 'teacher-charter'},
            {'name': 'معايير الحصة التعليمية', 'anchor': 'lesson-standards'},
            {'name': 'معايير المتابعة', 'anchor': 'follow-up-standards'},
            {'name': 'سياسة التعامل مع الأطفال', 'anchor': 'children-policy'},
            {'name': 'سياسة الاحترام والخصوصية', 'anchor': 'privacy-policy'},
            {'name': 'ضمان الجودة', 'anchor': 'quality-assurance'},
            {'name': 'حقوق الطالب', 'anchor': 'student-rights'},
        ]

    def location(self, item):
        """URL القسم"""
        return reverse('quality_standards')

    def lastmod(self, item):
        """آخر تعديل"""
        return timezone.now()


class PopularPagesSitemap(Sitemap):
    """Sitemap للصفحات الأكثر زيارة"""
    changefreq = "weekly"
    priority = 0.85
    protocol = 'https'

    def items(self):
        """الصفحات الشائعة"""
        pages = [
            {'url': 'home', 'title': 'الرئيسية'},
            {'url': 'pricing', 'title': 'الباقات'},
            {'url': 'contact', 'title': 'تواصل معنا'},
        ]
        
        # إضافة أشهر 5 مقالات
        if HAS_BLOG:
            popular_posts = Post.objects.filter(
                status='published'
            ).order_by('-views_count')[:5]
            
            for post in popular_posts:
                pages.append({
                    'url': 'blog_detail',
                    'slug': post.slug,
                    'title': post.title,
                    'is_post': True
                })
        
        return pages

    def location(self, item):
        """URL الصفحة"""
        if item.get('is_post'):
            return reverse(item['url'], args=[item['slug']])
        return reverse(item['url'])

    def lastmod(self, item):
        """آخر تعديل"""
        if item.get('is_post') and HAS_BLOG:
            try:
                post = Post.objects.get(slug=item['slug'])
                return post.updated_at if hasattr(post, 'updated_at') else post.published_at
            except:
                pass
        return timezone.now()


class ImageSitemap(Sitemap):
    """Sitemap للصور (للمدونة)"""
    changefreq = "monthly"
    priority = 0.6
    protocol = 'https'
    limit = 500

    def items(self):
        """الصور من المقالات"""
        if not HAS_BLOG:
            return []
        
        return Post.objects.filter(
            status='published',
            image__isnull=False
        ).exclude(image='').order_by('-published_at')[:50]

    def location(self, obj):
        """URL المقال الذي يحتوي على الصورة"""
        return reverse('blog_detail', args=[obj.slug])

    def lastmod(self, obj):
        """آخر تعديل"""
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.published_at


class NewsSitemap(Sitemap):
    """Sitemap للأخبار والمقالات الحديثة (آخر 48 ساعة)"""
    changefreq = "hourly"
    priority = 1.0
    protocol = 'https'

    def items(self):
        """المقالات المنشورة في آخر 48 ساعة"""
        if not HAS_BLOG:
            return []
        
        two_days_ago = timezone.now() - timedelta(days=2)
        return Post.objects.filter(
            status='published',
            published_at__gte=two_days_ago
        ).order_by('-published_at')

    def location(self, obj):
        """URL المقال"""
        return reverse('blog_detail', args=[obj.slug])

    def lastmod(self, obj):
        """آخر تعديل"""
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.published_at


class MobileSitemap(Sitemap):
    """Sitemap للصفحات المحسّنة للموبايل"""
    changefreq = "daily"
    priority = 0.9
    protocol = 'https'

    def items(self):
        """الصفحات المحسّنة للموبايل"""
        return [
            'home',
            'pricing',
            'contact',
            'blog_list',
        ]

    def location(self, item):
        """URL الصفحة"""
        return reverse(item)

    def lastmod(self, item):
        """آخر تعديل"""
        return timezone.now()