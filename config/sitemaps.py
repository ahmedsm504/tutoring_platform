# sitemaps.py
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
        """قائمة الصفحات الثابتة - تم دمج MobileSitemap هنا"""
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
        """URL لكل صفحة"""
        return reverse(obj['url'])
    
    def lastmod(self, obj):
        """آخر تعديل للصفحة (افتراضي الوقت الحالي)"""
        return timezone.now()
    
    def changefreq(self, obj):
        return obj['changefreq']
    
    def priority(self, obj):
        return obj['priority']


class BlogPostSitemap(Sitemap):
    """Sitemap لمقالات المدونة"""
    changefreq = "weekly"
    priority = 0.8
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
        """أولوية المقال حسب المشاهدات والتاريخ"""
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
        if not HAS_BLOG:
            return []
        return Category.objects.all().order_by('name')

    def lastmod(self, obj):
        """آخر تعديل للتصنيف (تاريخ أحدث مقال في هذا التصنيف)"""
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
    """Sitemap لأسئلة QNA (جميع الأسئلة المعتمدة)"""
    changefreq = "daily"
    priority = 0.8
    protocol = 'https'
    limit = 1000

    def items(self):
        if not HAS_QNA:
            return []
        return PublicQuestion.objects.filter(status='approved').order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('qna:question_detail', args=[obj.slug])
    
    def priority(self, obj):
        """أولوية السؤال (حسب وجود إجابة وشهرته)"""
        try:
            has_answer = QuestionAnswer.objects.filter(question=obj).exists()
            if has_answer:
                answer = QuestionAnswer.objects.filter(question=obj).first()
                if answer and answer.is_featured:
                    return 0.95
                return 0.85
        except:
            pass
        
        if obj.is_frequent:
            return 0.8
        
        if obj.view_count > 100:
            return 0.75
        
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
        """آخر تعديل للتصنيف (تاريخ أحدث سؤال معتمد في هذا التصنيف)"""
        if not HAS_QNA:
            return timezone.now()
            
        latest_question = PublicQuestion.objects.filter(
            category=obj, 
            status='approved'
        ).order_by('-created_at').first()
        
        return latest_question.created_at if latest_question else timezone.now()

    def location(self, obj):
        return f"{reverse('qna:question_list')}?category={obj.slug}"


class QNAAnsweredQuestionsSitemap(Sitemap):
    """Sitemap للأسئلة المُجابة فقط (أولوية أعلى)"""
    changefreq = "weekly"
    priority = 0.9
    protocol = 'https'
    limit = 500

    def items(self):
        if not HAS_QNA:
            return []
        
        answered_question_ids = QuestionAnswer.objects.values_list('question_id', flat=True)
        return PublicQuestion.objects.filter(
            id__in=answered_question_ids,
            status='approved'
        ).order_by('-view_count', '-created_at')

    def lastmod(self, obj):
        try:
            answer = QuestionAnswer.objects.filter(question=obj).first()
            return answer.answered_at if answer else obj.created_at
        except:
            return obj.created_at

    def location(self, obj):
        return reverse('qna:question_detail', args=[obj.slug])


class FrequentQuestionsSitemap(Sitemap):
    """Sitemap للأسئلة المتكررة"""
    changefreq = "monthly"
    priority = 0.85
    protocol = 'https'

    def items(self):
        if not HAS_QNA:
            return []
        
        return PublicQuestion.objects.filter(
            status='approved',
            is_frequent=True
        ).order_by('-view_count')

    def location(self, obj):
        return reverse('qna:question_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at


class NewsSitemap(Sitemap):
    """Sitemap للمحتوى الحديث (آخر 48 ساعة)"""
    changefreq = "hourly"
    priority = 0.9  # تم تخفيضها من 1.0
    protocol = 'https'

    def items(self):
        two_days_ago = timezone.now() - timedelta(days=2)
        items = []
        
        # المقالات الحديثة
        if HAS_BLOG:
            recent_posts = Post.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
            
            for post in recent_posts:
                items.append({
                    'type': 'blog',
                    'obj': post,
                    'url': 'blog_detail',
                    'slug': post.slug
                })
        
        # الأسئلة الحديثة
        if HAS_QNA:
            recent_questions = PublicQuestion.objects.filter(
                status='approved',
                created_at__gte=two_days_ago
            ).order_by('-created_at')
            
            for question in recent_questions:
                items.append({
                    'type': 'qna',
                    'obj': question,
                    'url': 'qna:question_detail',
                    'slug': question.slug
                })
        
        return items

    def location(self, item):
        return reverse(item['url'], args=[item['slug']])

    def lastmod(self, item):
        obj = item['obj']
        if item['type'] == 'blog':
            return obj.updated_at if hasattr(obj, 'updated_at') else obj.published_at
        else:  # qna
            return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at


class PopularPagesSitemap(Sitemap):
    """Sitemap للصفحات الأكثر زيارة (مقالات وأسئلة شائعة)"""
    changefreq = "weekly"
    priority = 0.85
    protocol = 'https'

    def items(self):
        pages = [
            {'url': 'home', 'title': 'الرئيسية'},
            {'url': 'pricing', 'title': 'الباقات'},
            {'url': 'contact', 'title': 'تواصل معنا'},
            {'url': 'qna:question_list', 'title': 'الأسئلة والأجوبة'},
        ]
        
        # إضافة أشهر 5 مقالات من المدونة
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
        
        # إضافة أشهر 5 أسئلة
        if HAS_QNA:
            popular_questions = PublicQuestion.objects.filter(
                status='approved'
            ).order_by('-view_count')[:5]
            
            for question in popular_questions:
                pages.append({
                    'url': 'qna:question_detail',
                    'slug': question.slug,
                    'title': question.title,
                    'is_question': True
                })
        
        return pages

    def location(self, item):
        if item.get('is_post'):
            return reverse(item['url'], args=[item['slug']])
        elif item.get('is_question'):
            return reverse(item['url'], args=[item['slug']])
        return reverse(item['url'])

    def lastmod(self, item):
        if item.get('is_post') and HAS_BLOG:
            try:
                post = Post.objects.get(slug=item['slug'])
                return post.updated_at if hasattr(post, 'updated_at') else post.published_at
            except:
                pass
        
        if item.get('is_question') and HAS_QNA:
            try:
                question = PublicQuestion.objects.get(slug=item['slug'])
                return question.updated_at if hasattr(question, 'updated_at') else question.created_at
            except:
                pass
        
        return timezone.now()


# ملاحظة: تم إزالة الخرائط التالية لتجنب التكرار:
# - PricingPackagesSitemap (لأن /pricing/ موجود بالفعل في StaticViewSitemap)
# - QualityStandardsSitemap (نفس الشيء)
# - MobileSitemap (تم دمجه في StaticViewSitemap)
# - ImageSitemap (إذا كنت بحاجة حقيقية لخريطة صور منفصلة، يمكنك إضافتها لاحقاً)