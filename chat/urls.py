from django.urls import path

from . import views

urlpatterns = [
    # API لحظي (الصلاحية بتتحدد جوه حسب الدور)
    path('chat/api/<int:conv_id>/poll/', views.api_poll, name='chat_poll'),
    path('chat/api/<int:conv_id>/send/', views.api_send, name='chat_send'),
    path('chat/api/<int:conv_id>/typing/', views.api_typing, name='chat_typing'),
    path('chat/api/unread/', views.unread, name='chat_unread'),
    path('chat/file/<int:message_id>/', views.attachment, name='chat_attachment'),

    # الإدارة
    path('chat/admin/', views.admin_inbox, name='chat_admin_inbox'),
    path('chat/admin/student/<int:student_id>/', views.admin_thread, name='chat_admin_thread'),
    path('chat/admin/student/<int:student_id>/update/', views.admin_update, name='chat_admin_update'),

    # المعلمة
    path('teacher-portal/messages/', views.teacher_inbox, name='chat_teacher_inbox'),
    path('teacher-portal/messages/<int:student_id>/', views.teacher_thread, name='chat_teacher_thread'),

    # الطالب
    path('student-portal/chat/', views.student_chat, name='student_chat'),

    # المشرفة
    path('supervisor-portal/messages/', views.supervisor_inbox, name='chat_supervisor_inbox'),
    path('supervisor-portal/messages/<int:student_id>/', views.supervisor_thread, name='chat_supervisor_thread'),
]
