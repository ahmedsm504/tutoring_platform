from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView, TemplateView

from accounts import views as accounts_views
from core.push_status import push_status

from .robots_view import llms_txt, robots_txt
from .sitemaps import (BlogCategorySitemap, BlogPostSitemap, QNACategorySitemap, QNAQuestionsSitemap,
                       QuranSitemap, StaticViewSitemap)


def indexnow_key(request):
    # ملف التحقق لازم محتواه يكون نفس المفتاح بالظبط (قبل كده كان بيرجع مفتاح تاني فـ IndexNow كان بيرفض)
    return HttpResponse(settings.INDEXNOW_KEY, content_type="text/plain")


sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'blog-categories': BlogCategorySitemap,
    'qna-questions': QNAQuestionsSitemap,
    'qna-categories': QNACategorySitemap,
    'quran': QuranSitemap,
}


@cache_page(60 * 30)
def sitemap_view(request, **kwargs):
    # قالب بيضيف صورة الغلاف لكل مقال (image sitemap) عشان الصور تظهر في بحث جوجل للصور
    return sitemap(request, sitemaps=sitemaps, template_name='sitemaps/sitemap_images.xml')


def ads_txt(request):
    # مطلوب لـ Google AdSense - من غيره جوجل بيقلل الإعلانات/الأرباح
    return HttpResponse('google.com, pub-4253419170065458, DIRECT, f08c47fec0942fa0\n', content_type='text/plain')


urlpatterns = [
    path('ads.txt', ads_txt),
    path('admin/push-status/', push_status, name='push_status'),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap_view, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots'),
    path('llms.txt', llms_txt, name='llms_txt'),
    path(f'{settings.INDEXNOW_KEY}.txt', indexnow_key),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.png', permanent=True)),

    # صفحة التواصل الأساسية بقت /contact/ - الرابط القديم بيتحول عليها (من غير صفحتين مكررتين)
    path('accounts/contact/', RedirectView.as_view(pattern_name='contact', permanent=True)),

    path('', include('core.urls')),
    path('', include('chat.urls')),
    path('', include('learning.urls')),
    path('accounts/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('questions/', include('qna.urls', namespace='qna')),
    path('firebase-messaging-sw.js', TemplateView.as_view(
        template_name='firebase-messaging-sw.js', content_type='application/javascript'
    ), name='firebase-sw'),
    path('save-fcm-token/', accounts_views.save_fcm_token, name='save_fcm_token'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
