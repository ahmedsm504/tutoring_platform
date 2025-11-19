# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .models import StudentProfile, Message, Session, TrialBooking
from .forms import TrialBookingForm

User = get_user_model()


# ==========================================
# تسجيل مستخدم جديد
# ==========================================
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        country = request.POST.get('country', '').strip()
        phone = request.POST.get('phone', '').strip()
        parent_phone = request.POST.get('parent_phone', '').strip()
        age = request.POST.get('age', '').strip()
        lessons_count = request.POST.get('lessons_count')
        session_duration = request.POST.get('session_duration')
        package_name = request.POST.get('package_name', '').strip()

        # التحقق من الحقول
        if not all([username, email, password, full_name, country, phone,
                    parent_phone, age, lessons_count, session_duration, package_name]):
            messages.error(request, "الرجاء ملء جميع الحقول المطلوبة.")
            return redirect('register')

        # التحقق من القيم الرقمية
        try:
            age = int(age)
            lessons_count = int(lessons_count)
            session_duration = int(session_duration)
        except ValueError:
            messages.error(request, "يجب إدخال قيم رقمية صحيحة.")
            return redirect('register')

        # التحقق من اسم المستخدم
        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم مستخدم بالفعل.")
            return redirect('register')

        # إنشاء المستخدم
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type='student'
            )

            # إنشاء/تحديث البروفايل
            profile, created = StudentProfile.objects.get_or_create(user=user)
            profile.full_name = full_name
            profile.country = country
            profile.phone = phone
            profile.parent_phone = parent_phone
            profile.age = age
            profile.lessons_count = lessons_count
            profile.session_duration = session_duration
            profile.package_name = package_name
            profile.save()

            messages.success(request, "تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول.")
            return redirect('login')
        
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء التسجيل: {str(e)}")
            return redirect('register')

    return render(request, 'accounts/register.html')


# ==========================================
# تسجيل الدخول
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        # إعادة توجيه المستخدم المسجل بالفعل
        if request.user.user_type == 'student':
            return redirect('student_dashboard')
        elif request.user.user_type in ['supervisor', 'admin']:
            return redirect('supervisor_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً {user.username}! تم تسجيل الدخول بنجاح.')

            # إعادة التوجيه حسب نوع المستخدم
            if user.user_type == 'student':
                return redirect('student_dashboard')
            elif user.user_type in ['supervisor', 'admin']:
                return redirect('supervisor_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')

    return render(request, 'accounts/login.html')


# ==========================================
# تسجيل الخروج
# ==========================================
@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'وداعاً {username}! تم تسجيل الخروج بنجاح.')
    return redirect('home')


# ==========================================
# صفحة التواصل وحجز التجربة
# ==========================================
def contact_view(request):
    if request.method == "POST":
        form = TrialBookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم الحجز بنجاح ✅ سنتواصل معك قريباً")
            return redirect('contact')
        else:
            messages.error(request, "حدث خطأ في الحجز. الرجاء المحاولة مرة أخرى.")
    else:
        form = TrialBookingForm()
    
    return render(request, 'accounts/contact.html', {'form': form})


# ==========================================
# لوحة تحكم الطالب
# ==========================================
@login_required
def student_dashboard(request):
    # التحقق من أن المستخدم طالب
    if request.user.user_type != 'student':
        messages.error(request, 'غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'الملف الشخصي غير موجود. الرجاء التسجيل أولاً.')
        return redirect('register')

    # جلب الجلسات
    sessions = profile.sessions.all().order_by('-date')
    
    # جلب الرسائل بين الطالب والمشرف
    if profile.supervisor:
        messages_list = Message.objects.filter(
            Q(sender=request.user, recipient=profile.supervisor) |
            Q(sender=profile.supervisor, recipient=request.user)
        ).order_by('created_at')
    else:
        messages_list = []

    context = {
        'profile': profile,
        'sessions': sessions,
        'messages': messages_list,
    }

    return render(request, 'accounts/dashboard.html', context)


# ==========================================
# إرسال رسالة (للطالب)
# ==========================================
@login_required
def send_message(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, 'الرسالة فارغة!')
            return redirect('student_dashboard')

        try:
            # جلب بروفايل الطالب
            profile = StudentProfile.objects.get(user=request.user)
            
            # التحقق من وجود مشرف
            if not profile.supervisor:
                messages.error(request, 'لم يتم تعيين مشرف لك بعد.')
                return redirect('student_dashboard')

            # إنشاء الرسالة
            Message.objects.create(
                sender=request.user,
                recipient=profile.supervisor,
                content=content,
                is_read=False
            )
            
            messages.success(request, 'تم إرسال الرسالة بنجاح ✅')
        
        except StudentProfile.DoesNotExist:
            messages.error(request, 'الملف الشخصي غير موجود.')
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')

    return redirect('student_dashboard')


# ==========================================
# صفحة الملف الشخصي
# ==========================================
@login_required
def profile_view(request):
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'الملف الشخصي غير موجود. الرجاء التسجيل أولاً.')
        return redirect('register')

    # جلب الجلسات
    sessions = profile.sessions.all().order_by('-date')

    context = {
        'profile': profile,
        'sessions': sessions,
    }

    return render(request, 'accounts/profile.html', context)


# ==========================================
# لوحة تحكم المشرف
# ==========================================
@login_required
def supervisor_dashboard(request):
    # التحقق من صلاحيات المشرف
    if request.user.user_type not in ['supervisor', 'admin']:
        messages.error(request, 'غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect('home')
    
    # جلب الطلاب
    students = StudentProfile.objects.filter(
        supervisor=request.user
    ).select_related('user').prefetch_related('sessions')
    
    # معالجة POST requests
    if request.method == 'POST':
        # إضافة جلسة
        if 'add_session' in request.POST:
            student_id = request.POST.get('student_id')
            date = request.POST.get('date')
            
            try:
                student = StudentProfile.objects.get(user__id=student_id)
                Session.objects.create(
                    student=student,
                    date=date,
                    status=''
                )
                messages.success(request, f'✅ تم إضافة الجلسة بنجاح للطالب {student.full_name}')
            except StudentProfile.DoesNotExist:
                messages.error(request, '❌ الطالب غير موجود')
            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')
        
        # تحديث حالة جلسة
        elif 'update_status' in request.POST:
            session_id = request.POST.get('session_id')
            status = request.POST.get('status')
            
            try:
                session = Session.objects.get(id=session_id)
                session.status = status
                session.save()
                
                status_text = {'present': 'حاضر ✓', 'absent': 'غائب ✗'}.get(status, 'غير محدد')
                messages.success(request, f'✅ تم تحديث الحالة إلى: {status_text}')
            except Session.DoesNotExist:
                messages.error(request, '❌ الجلسة غير موجودة')
            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')
        
        # حذف جلسة
        elif 'delete_session' in request.POST:
            session_id = request.POST.get('session_id')
            
            try:
                session = Session.objects.get(id=session_id)
                student_name = session.student.full_name
                session.delete()
                messages.success(request, f'✅ تم حذف جلسة {student_name}')
            except Session.DoesNotExist:
                messages.error(request, '❌ الجلسة غير موجودة')
            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')
        
        # إرسال رسالة
        elif 'send_message' in request.POST:
            student_id = request.POST.get('student_id')
            content = request.POST.get('content', '').strip()
            
            if not content:
                messages.error(request, '❌ الرسالة فارغة!')
            else:
                try:
                    student_user = User.objects.get(id=student_id)
                    Message.objects.create(
                        sender=request.user,
                        recipient=student_user,
                        content=content,
                        is_read=False
                    )
                    messages.success(request, '✅ تم إرسال الرسالة')
                except User.DoesNotExist:
                    messages.error(request, '❌ الطالب غير موجود')
                except Exception as e:
                    messages.error(request, f'❌ خطأ: {str(e)}')
        
        # تحديد رسائل كمقروءة
        elif 'mark_as_read' in request.POST:
            student_id = request.POST.get('student_id')
            
            try:
                updated_count = Message.objects.filter(
                    sender_id=student_id,
                    recipient=request.user,
                    is_read=False
                ).update(is_read=True)
                
                if updated_count > 0:
                    messages.success(request, f'✅ تم تحديد {updated_count} رسالة كمقروءة')
                else:
                    messages.info(request, 'ℹ️ لا توجد رسائل جديدة')
            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')
        
        return redirect('supervisor_dashboard')
    
    # حساب إجمالي الرسائل غير المقروءة
    total_unread = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # إعداد بيانات الطلاب
    students_data = []
    for student in students:
        # عدد الرسائل غير المقروءة
        student.unread_messages_count = Message.objects.filter(
            sender=student.user,
            recipient=request.user,
            is_read=False
        ).count()
        
        # جميع الرسائل
        student.all_messages = Message.objects.filter(
            Q(sender=request.user, recipient=student.user) |
            Q(sender=student.user, recipient=request.user)
        ).order_by('created_at')
        
        students_data.append(student)
    
    # ترتيب: الطلاب بأحدث رسائل أولاً
    students_data.sort(key=lambda x: x.unread_messages_count, reverse=True)
    
    context = {
        'students': students_data,
        'total_unread': total_unread,
    }
    
    return render(request, 'accounts/supervisor_dashboard.html', context)


# ==========================================
# تحديد رسالة واحدة كمقروءة
# ==========================================
@login_required
def mark_message_as_read(request, message_id):
    """تحديد رسالة معينة كمقروءة"""
    try:
        message = Message.objects.get(id=message_id, recipient=request.user)
        message.is_read = True
        message.save()
        messages.success(request, 'تم تحديد الرسالة كمقروءة')
    except Message.DoesNotExist:
        messages.error(request, 'الرسالة غير موجودة')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
    
    return redirect('supervisor_dashboard')


# ==========================================
# تحديد كل رسائل طالب كمقروءة
# ==========================================
@login_required
def mark_student_messages_read(request, student_id):
    """تحديد كل رسائل طالب معين كمقروءة"""
    try:
        updated_count = Message.objects.filter(
            sender_id=student_id,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        if updated_count > 0:
            messages.success(request, f'تم تحديد {updated_count} رسالة كمقروءة')
        else:
            messages.info(request, 'لا توجد رسائل جديدة')
    except Exception as e:
        messages.error(request, f'خطأ: {str(e)}')
    
    return redirect('supervisor_dashboard')


# ==========================================
# API: عدد الرسائل غير المقروءة (JSON)
# ==========================================
@login_required
def get_unread_count(request):
    """
    API endpoint لجلب عدد الرسائل غير المقروءة
    يمكن استخدامه مع AJAX للتحديث التلقائي
    """
    unread_count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({
        'unread_count': unread_count,
        'success': True
    })