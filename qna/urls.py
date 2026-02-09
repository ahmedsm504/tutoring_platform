# qna/urls.py
from django.urls import path, re_path
from . import views

app_name = 'qna'

urlpatterns = [
    # صفحات رئيسية
    path('', views.QuestionListView.as_view(), name='question_list'),
    path('ask/', views.AskQuestionView.as_view(), name='ask'),
    
    # صفحة السؤال - تدعم GET و POST
    re_path(r'^question/(?P<slug>[\w\-]+)/$', views.QuestionDetailView.as_view(), name='question_detail'),
    
    # ✅ حذف AddCommunityAnswerView لأن النموذج الآن يُرسل لنفس صفحة السؤال
    # re_path(r'^question/(?P<slug>[\w\-]+)/answer/$', views.AddCommunityAnswerView.as_view(), name='add_community_answer'),
    
    # AJAX endpoints للتصويت
    path('vote/<int:answer_id>/', views.vote_answer, name='vote_answer'),
    path('vote-community/<int:answer_id>/', views.vote_community_answer, name='vote_community_answer'),
    
    # AJAX endpoints للمشرفين
    path('verify-community/<int:answer_id>/', views.verify_community_answer, name='verify_community_answer'),
    path('delete-community/<int:answer_id>/', views.delete_community_answer, name='delete_community_answer'),
    
    # AJAX endpoints للتفاعل
    re_path(r'^report/(?P<slug>[\w\-]+)/$', views.report_content, name='report_content'),
    re_path(r'^subscribe/(?P<slug>[\w\-]+)/$', views.subscribe_to_question, name='subscribe_to_question'),
]