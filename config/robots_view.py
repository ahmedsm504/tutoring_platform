from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

@never_cache
@require_http_methods(["GET", "HEAD"])  # يقبل GET و HEAD
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: https://alagme.com/sitemap.xml",
        "",
        "Disallow: /admin/",
        "Disallow: /accounts/login/",
        "Disallow: /accounts/register/",
        "Disallow: /media/private/",
    ]
    response = HttpResponse("\n".join(lines), content_type="text/plain")
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response