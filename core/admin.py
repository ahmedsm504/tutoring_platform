from django.contrib import admin
from .models import (
    Country, Teacher, Student, StudentNote, Expense, Payment, TeacherSalaryRecord, MonthlyEvaluation,
    Lesson, ScheduleRequest, TeacherComplaint,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'flag_icon', 'is_active')
    list_editable = ('is_active',)


class SalaryRecordInline(admin.TabularInline):
    model = TeacherSalaryRecord
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'governorate', 'commission_percent', 'fixed_salary', 'calculated_salary', 'current_students_count', 'previous_students_count')
    search_fields = ('name', 'phone')
    inlines = [SalaryRecordInline]


class StudentNoteInline(admin.TabularInline):
    model = StudentNote
    extra = 1
    readonly_fields = ('created_at',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'teacher', 'month', 'status', 'payment_status', 'enrollment_type', 'acquisition_source')
    list_filter = ('country', 'status', 'payment_status', 'teacher', 'enrollment_type', 'acquisition_source')
    search_fields = ('name', 'phone')
    inlines = [StudentNoteInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'date', 'note')
    list_filter = ('date',)
    search_fields = ('student__name',)


@admin.register(TeacherSalaryRecord)
class TeacherSalaryRecordAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'payout_date', 'base_amount', 'bonus', 'deduction', 'leave_days', 'net_amount')
    list_filter = ('payout_date', 'teacher')
    search_fields = ('teacher__name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title',)


@admin.register(MonthlyEvaluation)
class MonthlyEvaluationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'month_label', 'teacher_name', 'template', 'created_at')
    list_filter = ('template', 'month_label')
    search_fields = ('student_name', 'teacher_name')
    readonly_fields = ('public_token', 'created_at')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'scheduled_at', 'status', 'was_late', 'status_recorded_at')
    list_filter = ('status', 'teacher', 'was_late')
    search_fields = ('student__name', 'teacher__name')
    readonly_fields = ('created_at',)


@admin.register(ScheduleRequest)
class ScheduleRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'request_type', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'request_type', 'teacher')
    search_fields = ('student__name', 'teacher__name')
    readonly_fields = ('created_at', 'reviewed_at')


@admin.register(TeacherComplaint)
class TeacherComplaintAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'description')
    list_filter = ('teacher', 'date')
    search_fields = ('teacher__name', 'description')
