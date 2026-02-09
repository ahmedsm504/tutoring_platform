from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order', 'get_questions_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(PublicQuestion)
class PublicQuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'visitor_name', 'category', 'status', 'view_count', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'is_frequent']
    search_fields = ['title', 'question_text', 'visitor_name']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    actions = ['mark_approved', 'mark_rejected', 'mark_spam']
    
    def mark_approved(self, request, queryset):
        queryset.update(status='approved')
    mark_approved.short_description = "اعتماد الأسئلة المحددة"
    
    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_rejected.short_description = "رفض الأسئلة المحددة"
    
    def mark_spam(self, request, queryset):
        queryset.update(status='spam')
    mark_spam.short_description = "تحديد كـ سبام"

@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'answered_by', 'is_featured', 'likes', 'answered_at']
    list_filter = ['is_featured', 'answered_at']
    search_fields = ['answer_text', 'question__title']
    readonly_fields = ['answered_at', 'updated_at']

@admin.register(CommunityAnswer)
class CommunityAnswerAdmin(admin.ModelAdmin):
    list_display = ['get_question_title', 'get_answerer_name', 'is_verified', 'likes', 'created_at']
    list_filter = ['is_verified', 'is_spam', 'created_at']
    search_fields = ['answer_text', 'visitor_name']
    actions = ['verify_answers', 'mark_as_spam']
    
    def get_question_title(self, obj):
        return obj.question.title[:50]
    get_question_title.short_description = "السؤال"
    
    def get_answerer_name(self, obj):
        return obj.get_answerer_name()
    get_answerer_name.short_description = "المجيب"
    
    def verify_answers(self, request, queryset):
        queryset.update(is_verified=True)
    verify_answers.short_description = "التحقق من الإجابات المحددة"
    
    def mark_as_spam(self, request, queryset):
        queryset.update(is_spam=True)
    mark_as_spam.short_description = "تحديد كـ غير مرغوب"

@admin.register(UserVote)
class UserVoteAdmin(admin.ModelAdmin):
    list_display = ['answer', 'ip_address', 'created_at']
    list_filter = ['created_at']

@admin.register(CommunityAnswerVote)
class CommunityAnswerVoteAdmin(admin.ModelAdmin):
    list_display = ['answer', 'ip_address', 'created_at']
    list_filter = ['created_at']

@admin.register(QuestionReport)
class QuestionReportAdmin(admin.ModelAdmin):
    list_display = ['question', 'report_type', 'is_resolved', 'created_at']
    list_filter = ['report_type', 'is_resolved', 'created_at']
    actions = ['mark_resolved']

@admin.register(QuestionSubscription)
class QuestionSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'get_subscriber', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    
    def get_subscriber(self, obj):
        if obj.user:
            return obj.user.username
        return obj.email
    get_subscriber.short_description = "المشترك"