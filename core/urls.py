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

    # قائمة الرواتب
    path('salaries/', views.salaries_list, name='salaries_list'),
    path('add-salary/', views.add_salary_record, name='add_salary_record'),
    path('delete-salary/<int:record_id>/', views.delete_salary_record, name='delete_salary_record'),
    path('teacher/<int:teacher_id>/update-commission/', views.update_teacher_commission, name='update_teacher_commission'),

    # الحلقات ومتابعة الحضور والانضباط
    path('lessons/', views.lessons_dashboard, name='lessons_dashboard'),
    path('lessons/add/', views.add_lesson, name='add_lesson'),
    path('lessons/<int:lesson_id>/mark/', views.mark_lesson, name='mark_lesson'),
    path('lessons/<int:lesson_id>/mark-started/', views.mark_lesson_started, name='mark_lesson_started'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),

    # طلبات المواعيد
    path('schedule-requests/', views.schedule_requests_list, name='schedule_requests_list'),
    path('schedule-requests/<int:request_id>/review/', views.review_schedule_request, name='review_schedule_request'),

    # شكاوى المعلمات
    path('teacher/<int:teacher_id>/add-complaint/', views.add_complaint, name='add_complaint'),

    # إدارة حساب دخول المعلمة (من لوحة الأدمن)
    path('teacher/<int:teacher_id>/create-login/', views.create_teacher_login, name='create_teacher_login'),
    path('teacher/<int:teacher_id>/reset-login-password/', views.reset_teacher_login_password, name='reset_teacher_login_password'),
    path('teacher/<int:teacher_id>/revoke-login/', views.revoke_teacher_login, name='revoke_teacher_login'),

    # بورتال المعلمة (صلاحيات محدودة - مش أدمن)
    path('teacher-portal/login/', views.teacher_login, name='teacher_login'),
    path('teacher-portal/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher-portal/', views.teacher_portal_home, name='teacher_portal_home'),
    path('teacher-portal/lessons/<int:lesson_id>/mark/', views.teacher_mark_lesson, name='teacher_mark_lesson'),
    path('teacher-portal/lessons/<int:lesson_id>/mark-started/', views.teacher_mark_lesson_started, name='teacher_mark_lesson_started'),
    path('teacher-portal/schedule-requests/', views.teacher_schedule_requests, name='teacher_schedule_requests'),
    path('teacher-portal/evaluations/', views.teacher_evaluations_list, name='teacher_evaluations_list'),
    path('teacher-portal/evaluations/<int:evaluation_id>/', views.teacher_evaluation_detail, name='teacher_evaluation_detail'),
    path('teacher-portal/register-schedule/', views.teacher_register_schedule, name='teacher_register_schedule'),
    path('teacher-portal/curriculum/', views.teacher_curriculum, name='teacher_curriculum'),
    path('teacher-portal/quran/', views.teacher_quran_reader, name='teacher_quran_reader'),
    path('teacher-portal/curriculum/<int:doc_id>/', views.teacher_curriculum_view, name='teacher_curriculum_view'),
    path('teacher-portal/curriculum/<int:doc_id>/stream/', views.teacher_curriculum_stream, name='teacher_curriculum_stream'),
    path('teacher-portal/whiteboard/', views.teacher_whiteboard, name='teacher_whiteboard'),
    path('teacher-portal/games/', views.teacher_games, name='teacher_games'),

    # إدارة المشرفات (من لوحة الأدمن)
    path('supervisors/', views.supervisors_list, name='supervisors_list'),
    path('supervisors/add/', views.add_supervisor, name='add_supervisor'),
    path('supervisor/<int:supervisor_id>/create-login/', views.create_supervisor_login, name='create_supervisor_login'),
    path('supervisor/<int:supervisor_id>/reset-login-password/', views.reset_supervisor_login_password, name='reset_supervisor_login_password'),
    path('supervisor/<int:supervisor_id>/revoke-login/', views.revoke_supervisor_login, name='revoke_supervisor_login'),

    # بورتال المشرفة (صلاحيات محدودة - معلماتها بس)
    path('supervisor-portal/login/', views.supervisor_login, name='supervisor_login'),
    path('supervisor-portal/logout/', views.supervisor_logout, name='supervisor_logout'),
    path('supervisor-portal/', views.supervisor_portal_home, name='supervisor_portal_home'),
    path('supervisor-portal/teacher/<int:teacher_id>/', views.supervisor_teacher_detail, name='supervisor_teacher_detail'),
    path('supervisor-portal/lessons/<int:lesson_id>/mark/', views.supervisor_mark_lesson, name='supervisor_mark_lesson'),
    path('supervisor-portal/student/<int:student_id>/schedule/register/', views.supervisor_register_student_schedule, name='supervisor_register_student_schedule'),
    path('supervisor-portal/student/<int:student_id>/schedule/', views.supervisor_student_schedule_view, name='supervisor_student_schedule_view'),
    path('supervisor-portal/student/<int:student_id>/evaluation/add/', views.supervisor_add_evaluation, name='supervisor_add_evaluation'),
    path('supervisor-portal/evaluation/<int:evaluation_id>/', views.supervisor_evaluation_detail, name='supervisor_evaluation_detail'),
    path('supervisor-portal/schedule-requests/', views.supervisor_schedule_requests_list, name='supervisor_schedule_requests_list'),
    path('supervisor-portal/schedule-requests/<int:request_id>/review/', views.supervisor_review_schedule_request, name='supervisor_review_schedule_request'),

    # نموذج تقييم ومتابعة الأداء الشهري
    path('evaluations/', views.evaluations_list, name='evaluations_list'),
    path('add-evaluation/', views.add_evaluation, name='add_evaluation'),
    path('evaluation/<int:evaluation_id>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluation/<int:evaluation_id>/delete/', views.delete_evaluation, name='delete_evaluation'),
    path('report/<uuid:token>/', views.public_evaluation, name='public_evaluation'),
]
