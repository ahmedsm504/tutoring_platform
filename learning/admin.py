from django.contrib import admin

from .models import Homework, StudentActivity, Submission


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ('submitted_at', 'reviewed_at')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'teacher', 'kind', 'due_date', 'created_at')
    list_filter = ('kind', 'teacher')
    search_fields = ('title', 'student__name', 'teacher__name', 'instructions')
    inlines = [SubmissionInline]


@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    list_display = ('student', 'kind', 'detail', 'points', 'created_at')
    list_filter = ('kind',)
    search_fields = ('student__name',)
