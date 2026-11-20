from django.urls import path

from . import views

app_name = 'careers'
urlpatterns = [
    path('jobs/', views.jobs_list, name='list'),
    path('jobs/<slug:slug>/', views.apply, name='apply'),
    path('jobs/<slug:slug>/done/', views.done, name='done'),
    path('staff/job-files/<int:pk>/', views.file_view, name='file'),
]
