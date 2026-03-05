# urls.py (الملف الرئيسي للمشروع)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

# استيراد Sitemaps (بعد التعديلات - إزالة الخرائط المكررة)
from .sitemaps import (
    StaticViewSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    PopularPagesSitemap,
    NewsSitemap,
    # QNA Sitemaps
    QNAQuestionsSitemap,
    QNACategorySitemap,
    QNAAnsweredQuestionsSitemap,
    FrequentQuestionsSitemap,
)

# تعريف جميع Sitemaps المتاحة
sitemaps = {
    # الصفحات الأساسية
    'static': StaticViewSitemap,          # الصفحات الثابتة
    'popular': PopularPagesSitemap,       # الصفحات الشائعة
    
    # المدونة
    'blog': BlogPostSitemap,              # مقالات المدونة
    'blog-categories': BlogCategorySitemap,  # تصنيفات المدونة
    
    # الأسئلة والأجوبة (QNA)
    'qna-questions': QNAQuestionsSitemap,     # جميع الأسئلة
    'qna-categories': QNACategorySitemap,     # تصنيفات الأسئلة
    'qna-answered': QNAAnsweredQuestionsSitemap,  # الأسئلة المُجابة
    'qna-frequent': FrequentQuestionsSitemap, # الأسئلة المتكررة
    
    # المحتوى الحديث
    'news': NewsSitemap,                  # الأخبار والمحتوى الحديث
}

urlpatterns = [
    # ============= Admin Panel =============
    path('admin/', admin.site.urls),
    
    # ============= Sitemap =============
    # Sitemap الرئيسي
    path('sitemap.xml', 
         sitemap, 
         {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    
    # ============= Robots.txt =============
    path('robots.txt',
         TemplateView.as_view(
             template_name="robots.txt",
             content_type="text/plain"
         ),
         name='robots'),
    
    # ============= Core URLs =============
    path('', include('core.urls')),  # الصفحات الرئيسية (home, pricing, about, etc.)
    
    # ============= Accounts URLs =============
    path('accounts/', include('accounts.urls')),  # نظام المستخدمين
    
    # ============= Blog URLs =============
    path('blog/', include('blog.urls')),  # المدونة
    
    # ============= QNA URLs =============
    path('questions/', include('qna.urls', namespace='qna')),  # الأسئلة والأجوبة
]

# Static and Media files في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)