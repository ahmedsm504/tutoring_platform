# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ============= Authentication =============
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============= Contact & Booking =============
    path('contact/', views.contact_view, name='contact'),
    
    # ============= Student Pages =============
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('send-message/', views.send_message, name='send_message'),
    
    # ============= Supervisor Pages =============
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/mark-message-read/<int:message_id>/', views.mark_message_as_read, name='mark_message_as_read'),
    path('supervisor/mark-student-messages-read/<int:student_id>/', views.mark_student_messages_read, name='mark_student_messages_read'),
    
    # ============= API Endpoints =============
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]