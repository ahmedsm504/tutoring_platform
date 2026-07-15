from django.contrib import admin
from .models import Country, Teacher, Student, StudentNote, Expense

class StudentNoteInline(admin.TabularInline):
    model = StudentNote
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'flag_icon', 'is_active')
    search_fields = ('name',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'current_students_count', 'net_salary')
    search_fields = ('name', 'phone')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'teacher', 'status', 'payment_status', 'subscription_fee')
    list_filter = ('status', 'payment_status', 'country', 'teacher')
    search_fields = ('name', 'phone', 'governorate')
    inlines = [StudentNoteInline]
    readonly_fields = ('join_date',)

@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'note_text', 'created_at')
    search_fields = ('student__name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'date')
    list_filter = ('date',)