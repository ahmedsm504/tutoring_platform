from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.video_list, name='video_list'),
    re_path(r'^(?P<slug>[\w-]+)/$', views.video_detail, name='video_detail'),
]
