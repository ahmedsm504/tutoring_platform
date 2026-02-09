# urls.py (الملف الرئيسي للمشروع)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

# استيراد Sitemaps
from .sitemaps import (
    StaticViewSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    PricingPackagesSitemap,
    QualityStandardsSitemap,
    PopularPagesSitemap,
    ImageSitemap,
    NewsSitemap,
    MobileSitemap,
)

# تعريف جميع Sitemaps
sitemaps = {
    'static': StaticViewSitemap,          # الصفحات الثابتة
    'blog': BlogPostSitemap,              # مقالات المدونة
    'categories': BlogCategorySitemap,    # تصنيفات المدونة
    'packages': PricingPackagesSitemap,   # الباقات
    'quality': QualityStandardsSitemap,   # مواثيق الجودة
    'popular': PopularPagesSitemap,       # الصفحات الشائعة
    'images': ImageSitemap,               # صور المقالات
    'news': NewsSitemap,                  # الأخبار الحديثة
    'mobile': MobileSitemap,              # صفحات الموبايل
}

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # ============= Sitemap =============
    path('sitemap.xml', 
         sitemap, 
         {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    
    # Sitemap Index (إذا كان لديك sitemaps كثيرة)
    path('sitemap-<section>.xml',
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
    path('', include('core.urls')),           # الصفحات الرئيسية
    
    # ============= Accounts URLs =============
    path('accounts/', include('accounts.urls')),  # نظام المستخدمين
    
    # ============= Blog URLs =============
    path('blog/', include('blog.urls')),      # المدونة
    
    path('questions/', include('qna.urls', namespace='qna')),
    # ============= Security Files =============
    # .well-known للتحقق من الملكية

]

# Static and Media files في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

