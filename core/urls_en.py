from django.urls import path

from learning import views_planner as vp

from . import views_en as v

# النسخة الإنجليزية من الصفحات العامة: /en/...
urlpatterns = [
    path('', v.home, name='en_home'),
    path('about/', v.about, name='en_about'),
    path('pricing/', v.pricing, name='en_pricing'),
    path('contact/', v.contact, name='en_contact'),
    path('contact/thank-you/', v.thank_you, name='en_thank_you'),
    path('quality-standards/', v.quality_standards, name='en_quality_standards'),
    path('privacy-policy/', v.privacy, name='en_privacy'),
    path('terms/', v.terms, name='en_terms'),
    path('editorial-policy/', v.editorial_policy, name='en_editorial_policy'),
    path('quran/', v.quran_index, name='en_quran_index'),
    path('quran/khatam-planner/', vp.khatma_en, name='en_khatma_planner'),
    path('quran/khatam-planner/<slug:slug>/', vp.khatma_en, name='en_khatma_preset'),
    path('quran/memorization-planner/', vp.hifz_en, name='en_hifz_planner'),
    path('quran/memorization-planner/<slug:slug>/', vp.hifz_en, name='en_hifz_preset'),
    path('blog/', v.blog_list, name='en_blog_list'),
]
