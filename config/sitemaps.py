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
    """Sitemap للصفحات الثابتة (بما في ذلك صفحات الموبايل)"""
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
            {'url': 'qna:question_list', 'priority': 0.85, 'changefreq': 'daily'},
            {'url': 'qna:ask', 'priority': 0.75, 'changefreq': 'weekly'},
            {'url': 'register', 'priority': 0.6, 'changefreq': 'yearly'},
            {'url': 'login', 'priority': 0.5, 'changefreq': 'yearly'},
        ]

    def location(self, obj):
        return reverse(obj['url'])
    
    def lastmod(self, obj):
        return timezone.now()
    
    def changefreq(self, obj):
        return obj['changefreq']
    
    def priority(self, obj):
        return obj['priority']


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
        # جميع الأسئلة المعتمدة
        return PublicQuestion.objects.filter(status='approved').order_by('-created_at')

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
        
        # 3. الأسئلة التي لها إجابة معتمدة
        try:
            has_answer = QuestionAnswer.objects.filter(question=obj).exists()
            if has_answer:
                # تحقق إذا كانت الإجابة مميزة
                answer = QuestionAnswer.objects.filter(question=obj).first()
                if answer and hasattr(answer, 'is_featured') and answer.is_featured:
                    return 0.92
                return 0.85
        except:
            pass
        
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