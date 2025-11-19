from django.contrib import admin
from .models import Teacher, Student, Expense

# ===============================
#        Teacher Admin
# ===============================
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'job_title', 
        'salary', 
        'working_hours', 
        'bonus', 
        'deduction', 
        'start_date', 
        'total_students_count'
    )
    search_fields = ('name', 'job_title')
    list_filter = ('job_title', 'start_date')
    ordering = ('-start_date',)

    # دالة لحساب عدد الطلاب المرتبطين بالمعلم
    def total_students_count(self, obj):
        return obj.total_students()
    total_students_count.short_description = "عدد الطلاب"


# ===============================
#        Student Admin
# ===============================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'teacher', 
        'session_duration', 
        'lessons_count', 
        'payment_type', 
        'paid_amount', 
        'total_paid_amount'
    )
    search_fields = ('name', 'teacher__name')
    list_filter = ('session_duration', 'lessons_count', 'payment_type', 'teacher')
    ordering = ('-join_date',)

    # دالة لحساب المبلغ الكلي حسب نوع الدفع
    def total_paid_amount(self, obj):
        return obj.total_paid()
    total_paid_amount.short_description = "الإجمالي المدفوع"


# ===============================
#        Expense Admin
# ===============================
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'date')
    search_fields = ('title',)
    list_filter = ('date',)
    ordering = ('-date',)
