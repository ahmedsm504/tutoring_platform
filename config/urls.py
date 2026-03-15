# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from .robots_view import robots_txt

from .sitemaps import (
    StaticViewSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    PopularPagesSitemap,
    NewsSitemap,
    QNAQuestionsSitemap,
    QNACategorySitemap,
    QNAAnsweredQuestionsSitemap,
    FrequentQuestionsSitemap,
)

sitemaps = {
    'static': StaticViewSitemap,
    'popular': PopularPagesSitemap,
    'blog': BlogPostSitemap,
    'blog-categories': BlogCategorySitemap,
    'qna-questions': QNAQuestionsSitemap,
    'qna-categories': QNACategorySitemap,
    'qna-answered': QNAAnsweredQuestionsSitemap,
    'qna-frequent': FrequentQuestionsSitemap,
    'news': NewsSitemap,
}


# ✅ wrapper يشيل X-Robots-Tag noindex ويضيف index
def sitemap_view(request, **kwargs):
    response = sitemap(request, sitemaps=sitemaps)
    response['X-Robots-Tag'] = 'index, follow'
    return response


urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ Sitemap
    path('sitemap.xml', sitemap_view, name='django.contrib.sitemaps.views.sitemap'),

    path('robots.txt', robots_txt, name='robots'),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('questions/', include('qna.urls', namespace='qna')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)