# sitemaps.py (النسخة النهائية بعد التعديل ومعالجة خطأ None)
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# استيراد الموديلات مع التأكد من وجود التطبيقات
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

try:
    from qna.models import PublicQuestion, QuestionCategory, QuestionAnswer
    HAS_QNA = True
except ImportError:
    HAS_QNA = False


class StaticViewSitemap(Sitemap):
    """الصفحات الثابتة المهمة بس (صفحات الدخول والتسجيل وفورم السؤال اتشالوا: مالهمش قيمة في البحث
    وكانوا متعارضين مع robots.txt)"""
    protocol = 'https'

    PAGES = [
        ('home', 1.0, 'daily'),
        ('pricing', 0.9, 'weekly'),
        ('contact', 0.8, 'monthly'),
        ('about', 0.7, 'monthly'),
        ('quality_standards', 0.7, 'monthly'),
        ('editorial_policy', 0.4, 'yearly'),
        ('privacy', 0.3, 'yearly'),
        ('terms', 0.3, 'yearly'),
        ('blog_list', 0.8, 'daily'),
        ('qna:question_list', 0.85, 'daily'),
        ('site_index', 0.6, 'daily'),
    ]

    def items(self):
        return self.PAGES

    def location(self, obj):
        return reverse(obj[0])

    def priority(self, obj):
        return obj[1]

    def changefreq(self, obj):
        return obj[2]

    def lastmod(self, obj):
        # آخر تحديث حقيقي للصفحات اللي محتواها بيتغير (بدل "دلوقتي" كل مرة - جوجل بيتجاهل ده)
        if obj[0] in ('blog_list', 'home', 'site_index') and HAS_BLOG:
            p = Post.objects.filter(status='published').order_by('-published_at').values_list('published_at', flat=True).first()
            return p
        if obj[0] == 'qna:question_list' and HAS_QNA:
            return PublicQuestion.objects.filter(status='approved').order_by('-created_at').values_list('created_at', flat=True).first()
        return None


class BlogPostSitemap(Sitemap):
    """Sitemap موحد لجميع مقالات المدونة مع أولوية ديناميكية"""
    changefreq = "weekly"
    protocol = 'https'
    limit = 1000

    def items(self):
        """جلب جميع المقالات المنشورة"""
        if not HAS_BLOG:
            return []
        return Post.objects.filter(status='published').order_by('-published_at')

    def lastmod(self, obj):
        """آخر تعديل للمقال"""
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.published_at

    def location(self, obj):
        return reverse('blog_detail', args=[obj.slug])
    
    def priority(self, obj):
        """أولوية ديناميكية بناءً على عدة عوامل"""
        # أعلى أولوية للمقالات المميزة
        if hasattr(obj, 'is_featured') and obj.is_featured:
            return 0.95
        
        # أولوية عالية للمقالات الأكثر مشاهدة
        if hasattr(obj, 'views_count'):
            if obj.views_count > 500:
                return 0.9
            elif obj.views_count > 100:
                return 0.85
        
        # أولوية متوسطة للمقالات الحديثة (آخر 7 أيام) - مع التحقق من وجود تاريخ
        if obj.published_at and (timezone.now() - obj.published_at) < timedelta(days=7):
            return 0.8
        
        # أولوية افتراضية
        return 0.7


class BlogCategorySitemap(Sitemap):
    """Sitemap لتصنيفات المدونة"""
    changefreq = "weekly"
    priority = 0.7
    protocol = 'https'

    def items(self):
        if not HAS_BLOG:
            return []
        return Category.objects.all().order_by('name')

    def lastmod(self, obj):
        if not HAS_BLOG:
            return timezone.now()
            
        latest_post = Post.objects.filter(
            category=obj, 
            status='published'
        ).order_by('-published_at').first()
        
        return latest_post.published_at if latest_post else timezone.now()

    def location(self, obj):
        return reverse('category_posts', args=[obj.slug])


class QNAQuestionsSitemap(Sitemap):
    """Sitemap موحد لجميع أسئلة QNA مع أولوية ديناميكية (يغطي جميع الحالات)"""
    changefreq = "daily"
    protocol = 'https'
    limit = 1000

    def items(self):
        if not HAS_QNA:
            return []
        from django.db.models import Exists, OuterRef
        return (PublicQuestion.objects.filter(status='approved')
                .annotate(has_answer=Exists(QuestionAnswer.objects.filter(question=OuterRef('pk'))))
                .order_by('-created_at'))

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('qna:question_detail', args=[obj.slug])
    
    def priority(self, obj):
        """أولوية ديناميكية تشمل جميع العوامل (مميز، متكرر، مُجاب، مشاهدات، حديث)"""
        # 1. الأسئلة المميزة (إذا كان لديك حقل is_featured)
        if hasattr(obj, 'is_featured') and obj.is_featured:
            return 0.95
        
        # 2. الأسئلة المتكررة (frequent)
        if hasattr(obj, 'is_frequent') and obj.is_frequent:
            return 0.9
        
        # 3. الأسئلة التي لها إجابة معتمدة (محسوبة مرة واحدة في items)
        if getattr(obj, 'has_answer', False):
            return 0.85

        # 4. الأسئلة الأكثر مشاهدة
        if hasattr(obj, 'view_count'):
            if obj.view_count > 500:
                return 0.88
            elif obj.view_count > 100:
                return 0.8
        
        # 5. الأسئلة الحديثة (آخر 48 ساعة) - مع التحقق من وجود تاريخ
        if obj.created_at and (timezone.now() - obj.created_at) < timedelta(days=2):
            return 0.82
        
        # 6. أولوية افتراضية
        return 0.7


class QNACategorySitemap(Sitemap):
    """Sitemap لتصنيفات الأسئلة"""
    changefreq = "weekly"
    priority = 0.75
    protocol = 'https'

    def items(self):
        if not HAS_QNA:
            return []
        return QuestionCategory.objects.all().order_by('name')

    def lastmod(self, obj):
        if not HAS_QNA:
            return timezone.now()
            
        latest_question = PublicQuestion.objects.filter(
            category=obj, 
            status='approved'
        ).order_by('-created_at').first()
        
        return latest_question.created_at if latest_question else timezone.now()

    def location(self, obj):
        return f"{reverse('qna:question_list')}?category={obj.slug}"


# ملاحظة: تمت إزالة الخرائط التالية لتجنب التكرار:
# - QNAAnsweredQuestionsSitemap
# - FrequentQuestionsSitemap
# - NewsSitemap
# - PopularPagesSitemap
# لأن وظائفها مغطاة بالكامل في QNAQuestionsSitemap و BlogPostSitemap من خلال دوال priority الذكية.


class QuranSitemap(Sitemap):
    """صفحات المصحف: فهرس السور + صفحة لكل سورة (114) - بحث قوي جدًا زي "سورة الكهف مكتوبة" """
    protocol = 'https'
    changefreq = 'monthly'

    def items(self):
        return ['index'] + list(range(1, 115))

    def location(self, obj):
        return reverse('quran_index') if obj == 'index' else reverse('quran_surah', args=[obj])

    def priority(self, obj):
        if obj == 'index':
            return 0.85
        return 0.75 if obj in (1, 2, 18, 36, 55, 56, 67, 112, 113, 114) else 0.6
