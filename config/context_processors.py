from django.conf import settings


def seo(request):
    """رابط الـ canonical الصح دايمًا على https://alagme.com مهما كان الدومين اللي الزائر جه منه"""
    site_url = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    canonical = site_url + request.path
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
