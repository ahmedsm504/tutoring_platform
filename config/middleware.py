"""Middlewares خاصة بالسيو."""
from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http import HttpResponsePermanentRedirect

# الصفحات العامة اللي عايزين جوجل يأرشفها - أي حاجة تانية (لوحات التحكم، البورتالات،
# المراسلات، تقارير الطلاب الخاصة...) بتاخد X-Robots-Tag: noindex تلقائيًا
PUBLIC_PREFIXES = (
    '/about/', '/contact/', '/pricing/', '/quality-standards/',
    '/blog/', '/questions/', '/quran/', '/static/', '/media/',
    '/sitemap.xml', '/robots.txt', '/llms.txt', '/favicon.ico', '/firebase-messaging-sw.js',
)
PRIVATE_UNDER_PUBLIC = ('/questions/vote', '/questions/vote-community', '/questions/verify-community',
                        '/questions/delete-community', '/questions/report', '/questions/subscribe')


class CanonicalHostMiddleware:
    """www.alagme.com ودومين Railway -> 301 على https://alagme.com بنفس المسار.
    ده بيمنع "المحتوى المكرر" وبيجمّع قوة الروابط كلها على دومين واحد."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.redirect_hosts = {h.lower() for h in getattr(settings, 'SEO_REDIRECT_HOSTS', [])}
        self.canonical = getattr(settings, 'CANONICAL_HOST', '')

    def __call__(self, request):
        if not settings.DEBUG and self.redirect_hosts and request.method in ('GET', 'HEAD'):
            try:
                host = request.get_host().split(':')[0].lower()
            except DisallowedHost:
                host = ''
            if host in self.redirect_hosts:
                return HttpResponsePermanentRedirect(f'https://{self.canonical}{request.get_full_path()}')
        return self.get_response(request)


def is_public_path(path):
    if path == '/':
        return True
    if path.startswith(PRIVATE_UNDER_PUBLIC):
        return False
    return path.startswith(PUBLIC_PREFIXES)


class PrivatePagesNoIndexMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not is_public_path(request.path) and 'X-Robots-Tag' not in response:
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
