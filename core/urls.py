from django.urls import path
from . import views
from .views import dashboard


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path("dashboard/", dashboard, name="dashboard"),
    path('quality-standards/', views.quality_standards, name='quality_standards'),

]
