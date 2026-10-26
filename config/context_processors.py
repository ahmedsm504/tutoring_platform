from django.conf import settings
from django.utils.encoding import iri_to_uri


def seo(request):
    """رابط الـ canonical الصح دايمًا على https://alagme.com مهما كان الدومين اللي الزائر جه منه"""
    site_url = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    # الروابط العربية بتتكتب percent-encoded زي ما هي في sitemap.xml بالظبط (نفس الرابط حرفيًا في الاتنين)
    canonical = site_url + iri_to_uri(request.path)
    page = request.GET.get('page', '')
    if page.isdigit() and int(page) > 1:
        canonical += f'?page={int(page)}'
    wa = getattr(settings, 'WHATSAPP_PUBLIC_NUMBER', '')
    return {
        'SITE_URL': site_url,
        'canonical_url': canonical,
        'SITE_NAME': getattr(settings, 'SITE_NAME', ''),
        'WHATSAPP_PUBLIC_NUMBER': wa,
        'WHATSAPP_LINK': f'https://wa.me/{wa}' if wa else '',
    }
