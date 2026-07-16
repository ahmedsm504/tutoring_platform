from django.urls import path
from . import views

urlpatterns = [
    # الصفحات العامة
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('quality-standards/', views.quality_standards, name='quality_standards'),

    # لوحة التحكم
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('country/<int:country_id>/', views.country_students, name='country_students'),
    path('add-student/', views.add_student, name='add_student'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('student/<int:student_id>/toggle-status/', views.toggle_student_status, name='toggle_student_status'),
    path('edit-student/<int:student_id>/', views.edit_student, name='edit_student'),

    path('teachers/', views.teachers_list, name='teachers_list'),
    path('teacher/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('edit-teacher/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('delete-teacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),

    path('all-students/', views.all_students, name='all_students'),
    path('statistics/', views.statistics, name='statistics'),

    # السنوات -> الشهور -> المدفوعات
    path('years/', views.years_list, name='years_list'),
    path('years/<int:year>/', views.year_months, name='year_months'),
    path('years/<int:year>/<int:month>/', views.month_payments, name='month_payments'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    path('student/<int:student_id>/add-payment/', views.add_student_payment, name='add_student_payment'),

    # إدارة الدول
    path('countries/', views.countries_list, name='countries_list'),
    path('add-country/', views.add_country, name='add_country'),
    path('edit-country/<int:country_id>/', views.edit_country, name='edit_country'),
    path('delete-country/<int:country_id>/', views.delete_country, name='delete_country'),

    # المصروفات
    path('expenses/', views.expenses_list, name='expenses_list'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('edit-expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),

    # التقارير المالية (شهري / سنوي)
    path('financial-reports/', views.financial_reports, name='financial_reports'),
]
