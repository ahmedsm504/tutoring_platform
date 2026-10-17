from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

PRIVATE_PATHS = [
    '/admin/', '/dashboard/', '/teacher-portal/', '/supervisor-portal/', '/student-portal/', '/chat/',
    '/report/', '/accounts/', '/save-fcm-token/', '/learning/', '/homework-audio/',
    '/questions/vote/', '/questions/vote-community/', '/questions/report/', '/questions/subscribe/',
    '/questions/verify-community/', '/questions/delete-community/',
    '/blog/?search=', '/questions/?search=', '/*?sort=',
]


@require_http_methods(["GET", "HEAD"])
@cache_control(public=True, max_age=3600)
def robots_txt(request):
    site = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {p}" for p in PRIVATE_PATHS]
    lines += ["", f"Sitemap: {site}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_http_methods(["GET", "HEAD"])
@cache_control(public=True, max_age=86400)
def llms_txt(request):
    site = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
    body = f"""# مؤسسة العجمي لتحفيظ القرآن الكريم (Alagme)

> منصة تعليمية لتحفيظ القرآن الكريم وتعليم التجويد عن بُعد (أونلاين) بحصص فردية مع معلمات ومعلمين متقنين، للأطفال والكبار من جميع الدول. أول حلقة تجريبية مجانية.

## الصفحات الأساسية
- [الرئيسية]({site}/): نظرة عامة على المنصة والحلقة التجريبية المجانية
- [الباقات والأسعار]({site}/pricing/): باقات التحفيظ وتصحيح التلاوة والدورات (نور البيان، الأربعون النووية)
- [من نحن]({site}/about/): رؤية المؤسسة ورسالتها
- [مواثيق الجودة]({site}/quality-standards/): معايير الجودة في التعليم والتعامل
- [تواصل معنا / احجز حلقة تجريبية]({site}/contact/)
- [المدونة]({site}/blog/): مقالات عن الحفظ والتجويد والتربية القرآنية
- [أسئلة وأجوبة]({site}/questions/): أسئلة الناس عن القرآن والتجويد وإجاباتها
- [القرآن الكريم مكتوب واستماع]({site}/quran/): نص المصحف بالرسم العثماني لكل السور مع استماع آية بآية بصوت الحصري والمنشاوي وغيرهم

## تواصل
- واتساب: https://wa.me/{getattr(settings, 'WHATSAPP_PUBLIC_NUMBER', '')}
- خريطة الموقع: {site}/sitemap.xml
"""
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
