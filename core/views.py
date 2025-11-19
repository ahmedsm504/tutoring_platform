from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Teacher, Student, Expense
import json
from django.contrib.admin.views.decorators import staff_member_required

# =======================
# صفحات الموقع العامة
# =======================
def home(request):
    # أسماء الصور في static/images/
    reviews = [
        'review1.jpeg', 'review2.jpeg', 'review3.jpeg', 'review4.jpeg',
        'review5.jpeg', 'review6.jpeg', 'review7.jpeg', 'review8.jpeg',
        'review9.jpeg', 'review10.jpeg', 'review11.jpeg', 'review12.jpeg',
        'review13.jpeg', 'review14.jpeg'
    ]
    return render(request, 'core/home.html', {'reviews': reviews})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def pricing(request):
    return render(request, 'core/pricing.html')

def quality_standards(request):
    return render(request, 'core/quality_standards.html')

# =======================
# لوحة التحكم المالية المتطورة
# =======================
@staff_member_required
def dashboard(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # الحصول على معاملات الفلترة
    filter_type = request.GET.get('filter_type', 'all')
    
    # تحديد نطاق التاريخ بناءً على الفلتر
    if filter_type == 'day':
        selected_date = request.GET.get('date')
        if selected_date:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            students = Student.objects.filter(join_date=selected_date)
            expenses = Expense.objects.filter(date=selected_date)
            # الرواتب لليوم الواحد = الراتب الشهري / 30
            teachers = Teacher.objects.all()
            total_salaries = sum((t.salary + t.bonus - t.deduction) / 30 for t in teachers)
        else:
            students = Student.objects.all()
            expenses = Expense.objects.all()
            teachers = Teacher.objects.all()
            total_salaries = sum(t.salary + t.bonus - t.deduction for t in teachers)
            
    elif filter_type == 'month':
        month = request.GET.get('month')
        year = request.GET.get('year')
        if month and year:
            students = Student.objects.filter(join_date__year=year, join_date__month=month)
            expenses = Expense.objects.filter(date__year=year, date__month=month)
            # الرواتب لشهر كامل
            teachers = Teacher.objects.all()
            total_salaries = sum(t.salary + t.bonus - t.deduction for t in teachers)
        else:
            students = Student.objects.all()
            expenses = Expense.objects.all()
            teachers = Teacher.objects.all()
            total_salaries = sum(t.salary + t.bonus - t.deduction for t in teachers)
            
    elif filter_type == 'range':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            students = Student.objects.filter(join_date__range=[start_date, end_date])
            expenses = Expense.objects.filter(date__range=[start_date, end_date])
            # حساب الرواتب حسب عدد الأيام في الفترة
            days_count = (end_date - start_date).days + 1
            teachers = Teacher.objects.all()
            total_salaries = sum((t.salary + t.bonus - t.deduction) * days_count / 30 for t in teachers)
        else:
            students = Student.objects.all()
            expenses = Expense.objects.all()
            teachers = Teacher.objects.all()
            total_salaries = sum(t.salary + t.bonus - t.deduction for t in teachers)
    else:
        # all - عرض كل البيانات
        students = Student.objects.all()
        expenses = Expense.objects.all()
        teachers = Teacher.objects.all()
        # إجمالي الرواتب (شامل المكافآت والخصومات)
        total_salaries = sum(t.salary + t.bonus - t.deduction for t in teachers)
    
    # إجمالي الإيرادات
    total_income = sum(s.total_paid() for s in students)
    
    # إجمالي المصروفات
    total_expenses = sum(e.amount for e in expenses)
    
    # صافي الربح
    net_profit = total_income - (total_salaries + total_expenses)

    # =======================
    # حساب التغيرات اليومية (مقارنة بالأمس)
    # =======================
    yesterday_students = Student.objects.filter(join_date=yesterday)
    yesterday_expenses_qs = Expense.objects.filter(date=yesterday)
    
    yesterday_income = sum(s.total_paid() for s in yesterday_students)
    yesterday_expenses_total = sum(e.amount for e in yesterday_expenses_qs)
    yesterday_profit = yesterday_income - (total_salaries + yesterday_expenses_total)

    def calc_change(current, previous):
        """حساب نسبة التغيير"""
        if previous == 0:
            return 0, current >= 0
        change = round((current - previous) / previous * 100, 2)
        return abs(change), change >= 0

    total_income_change, income_up = calc_change(total_income, yesterday_income)
    total_expenses_change, expenses_up = calc_change(total_expenses, yesterday_expenses_total)
    net_profit_change, profit_up = calc_change(net_profit, yesterday_profit)

    # =======================
    # الإيرادات اليومية - آخر 7 أيام
    # =======================
    daily_revenue = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_students = Student.objects.filter(join_date=day)
        day_total = sum(s.total_paid() for s in day_students)
        daily_revenue.append({
            'date': day.strftime('%d %b'),
            'total': float(day_total)
        })
    daily_revenue.reverse()

    # =======================
    # المقارنة الشهرية - آخر 6 أشهر
    # =======================
    monthly_comparison = []
    for i in range(5, -1, -1):
        # حساب أول يوم من الشهر
        first_day = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        year = first_day.year
        month = first_day.month
        
        # الطلاب والمصروفات لهذا الشهر
        month_students = Student.objects.filter(
            join_date__year=year,
            join_date__month=month
        )
        month_expenses = Expense.objects.filter(
            date__year=year,
            date__month=month
        )
        
        # الحسابات
        month_income = sum(s.total_paid() for s in month_students)
        month_expenses_total = sum(e.amount for e in month_expenses)
        month_profit = month_income - (total_salaries + month_expenses_total)
        
        monthly_comparison.append({
            'month': first_day.strftime('%b %Y'),
            'income': float(month_income),
            'expenses': float(month_expenses_total),
            'salaries': float(total_salaries),
            'profit': float(month_profit)
        })

    # تحويل البيانات إلى JSON للرسوم البيانية
    daily_revenue_json = json.dumps(daily_revenue, ensure_ascii=False)
    monthly_comparison_json = json.dumps(monthly_comparison, ensure_ascii=False)

    context = {
        # الإحصائيات الأساسية
        "total_salaries": total_salaries,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        
        # التغيرات اليومية
        "total_income_change": total_income_change,
        "income_up": income_up,
        "total_expenses_change": total_expenses_change,
        "expenses_up": expenses_up,
        "net_profit_change": net_profit_change,
        "profit_up": profit_up,
        
        # البيانات للرسوم البيانية
        "daily_revenue": daily_revenue_json,
        "monthly_comparison": monthly_comparison_json,
        
        # معلومات الفلتر
        "filter_type": filter_type,
        "selected_date": request.GET.get('date', ''),
        "selected_month": request.GET.get('month', ''),
        "selected_year": request.GET.get('year', ''),
        "start_date": request.GET.get('start_date', ''),
        "end_date": request.GET.get('end_date', ''),
    }

    return render(request, "core/dashboard.html", context)