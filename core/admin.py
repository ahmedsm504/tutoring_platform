from django.contrib import admin
from .models import Country, Teacher, Student, StudentNote, Expense, Payment


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'flag_icon', 'is_active')
    list_editable = ('is_active',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'governorate', 'net_salary', 'current_students_count', 'previous_students_count')
    search_fields = ('name', 'phone')


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


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title',)
