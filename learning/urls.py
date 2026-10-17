from django.urls import path

from . import views

urlpatterns = [
    # المعلمة
    path('teacher-portal/homework/', views.teacher_list, name='learning_teacher_list'),
    path('teacher-portal/homework/new/', views.teacher_new, name='learning_teacher_new'),
    path('teacher-portal/homework/<int:pk>/', views.teacher_detail, name='learning_teacher_detail'),
    path('teacher-portal/homework/<int:pk>/delete/', views.teacher_delete, name='learning_teacher_delete'),
    # الطالب
    path('student-portal/homework/', views.student_list, name='learning_student_list'),
    path('student-portal/homework/<int:pk>/', views.student_homework, name='learning_student_homework'),
    path('student-portal/listen/', views.student_listen, name='learning_student_listen'),
    path('student-portal/games/', views.student_games, name='learning_student_games'),
    path('student-portal/stars/', views.student_achievements, name='learning_student_achievements'),
    path('student-portal/api/score/', views.api_score, name='learning_api_score'),
    # ملفات صوت محمية
    path('homework-audio/<str:kind>/<int:pk>/', views.audio, name='learning_audio'),
    # الإدارة
    path('learning/admin/', views.admin_list, name='learning_admin_list'),
    path('learning/admin/<int:pk>/', views.admin_detail, name='learning_admin_detail'),
    # عام (سيو)
    path('quran/', views.quran_index, name='quran_index'),
    path('quran/<int:n>/', views.quran_surah, name='quran_surah'),
]
