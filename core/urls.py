from django.urls import path
from . import views
from .views import dashboard, robots_txt_new, robots_redirect

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('dashboard/', dashboard, name='dashboard'),
    path('quality-standards/', views.quality_standards, name='quality_standards'),

    # ملف robots الجديد
    path('robots-new.txt', robots_txt_new),

    # redirect من robots.txt القديم
    path('robots.txt', robots_redirect),
]