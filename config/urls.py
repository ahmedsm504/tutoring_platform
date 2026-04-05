# urls.py (بعد التعديل)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from .robots_view import robots_txt
from django.views.generic import TemplateView
from accounts import views as accounts_views

from django.http import HttpResponse

def indexnow_key(request):
    return HttpResponse("b52bd4ea55c149459d7c6e1f2ca39c98", content_type="text/plain")


# استيراد الخرائط المحدثة (بعد إزالة المكررة)
from .sitemaps import (
    StaticViewSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    QNAQuestionsSitemap,        # الخريطة الموحدة للأسئلة
    QNACategorySitemap,
    # تم إزالة: PopularPagesSitemap, NewsSitemap, QNAAnsweredQuestionsSitemap, FrequentQuestionsSitemap
)

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'blog-categories': BlogCategorySitemap,
    'qna-questions': QNAQuestionsSitemap,
    'qna-categories': QNACategorySitemap,
    # تم إزالة: 'popular', 'news', 'qna-answered', 'qna-frequent'
}

def sitemap_view(request, **kwargs):
    response = sitemap(request, sitemaps=sitemaps)
    response['X-Robots-Tag'] = 'index, follow'
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap_view, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots'),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('questions/', include('qna.urls', namespace='qna')),
        # ... الـ urls الموجودة
    path('firebase-messaging-sw.js', TemplateView.as_view(
        template_name='firebase-messaging-sw.js',
        content_type='application/javascript'
    ), name='firebase-sw'),
    path('save-fcm-token/', accounts_views.save_fcm_token, name='save_fcm_token'),
    path("b52bd4ea55c149459d7c6e1f2ca39c98.txt", indexnow_key),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



