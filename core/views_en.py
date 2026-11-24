"""النسخة الإنجليزية من الصفحات العامة (/en/...) للزوار من برا الدول العربية.
نفس البيانات والفورم بتاع العربي، بس بنصوص إنجليزي وقوالب LTR في templates/en/."""
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils import translation

from . import en_content as en
from .site_content import REVIEWS
from .views import _latest_videos


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')


def _english_posts():
    from blog.models import Post
    return (Post.objects.indexable().filter(category__slug='english')
            .select_related('category').order_by('-is_featured', '-published_at'))


def home(request):
    return render(request, 'en/home.html', {
        'programs': en.PROGRAMS, 'steps': en.STEPS, 'features': en.FEATURES, 'faq': en.FAQ,
        'reviews': REVIEWS,
        'faq_ldjson': _ld(en.faq_schema()),
        'latest_posts': _english_posts()[:3],
        'latest_videos': _latest_videos(),
    })


def pricing(request):
    from core.pricing import context as pricing_ctx
    site = settings.CANONICAL_URL.rstrip('/')
    return render(request, 'en/pricing.html', {
        'programs': en.PROGRAMS, 'courses_ldjson': _ld(en.courses_schema(site)),
        **pricing_ctx(en=True),
    })


def about(request):
    return render(request, 'en/about.html')


def quality_standards(request):
    return render(request, 'en/quality_standards.html')


def privacy(request):
    return render(request, 'en/privacy.html')


def terms(request):
    return render(request, 'en/terms.html')


def editorial_policy(request):
    return render(request, 'en/editorial_policy.html')


def contact(request):
    """نفس فورم حجز الحلقة التجريبية (TrialBookingForm) - رسائل الأخطاء بالإنجليزي"""
    from accounts.forms import TrialBookingForm
    with translation.override('en'):
        if request.method == 'POST':
            form = TrialBookingForm(request.POST)
            if form.is_valid():
                # علامة [EN site] للإدارة إن الحجز جه من النسخة الإنجليزي (الأغلب محتاج معلم بيتكلم إنجليزي)
                from accounts.views import save_booking
                save_booking(request, form, en=True)
                return redirect('en_thank_you')
        else:
            initial = {}
            slug = request.GET.get('program', '')
            prog = next((p for p in en.PROGRAMS if p['slug'] == slug), None)
            if prog:
                initial['notes'] = f"Interested in: {prog['name']}"
            form = TrialBookingForm(initial=initial)
        return render(request, 'en/contact.html', {'form': form})


def thank_you(request):
    return render(request, 'en/thank_you.html')


def quran_index(request):
    from learning import quran
    surahs = []
    for s, (tr, meaning) in zip(quran.index(), en.SURAH_EN):
        surahs.append({**s, 'en': tr, 'meaning': meaning})
    return render(request, 'en/quran_index.html', {'surahs': surahs})


def blog_list(request):
    posts = Paginator(_english_posts(), 12).get_page(request.GET.get('page'))
    return render(request, 'en/blog_list.html', {'posts': posts})
