# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, Session, Message, TrialBooking
from accounts import models


# ==========================================
# تخصيص User Admin
# ==========================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone', 'country')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('user_type', 'phone', 'country')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('معلومات إضافية', {'fields': ('user_type', 'phone', 'country')}),
    )


# ==========================================
# تخصيص StudentProfile Admin
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'supervisor', 'package_name', 'lessons_count', 'age', 'country', 'created_at')
    list_filter = ('supervisor', 'lessons_count', 'session_duration', 'country', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email', 'phone', 'package_name')
    list_select_related = ('user', 'supervisor')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user', 'supervisor')
        }),
        ('المعلومات الشخصية', {
            'fields': ('full_name', 'age', 'country', 'phone', 'parent_phone')
        }),
        ('معلومات الباقة', {
            'fields': ('package_name', 'lessons_count', 'session_duration')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # المشرفون يرون طلابهم فقط
            if request.user.user_type == 'supervisor':
                qs = qs.filter(supervisor=request.user)
        return qs


# ==========================================
# تخصيص Session Admin
# ==========================================
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'get_status_icon', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('student__full_name', 'student__user__username', 'notes')
    list_select_related = ('student', 'student__user')
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('معلومات الجلسة', {
            'fields': ('student', 'date', 'status')
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_status_icon(self, obj):
        """عرض أيقونة الحالة"""
        icons = {
            'present': '✓',
            'absent': '✗',
            '': '-'
        }
        colors = {
            'present': 'green',
            'absent': 'red',
            '': 'gray'
        }
        icon = icons.get(obj.status, '-')
        color = colors.get(obj.status, 'gray')
        return f'<span style="color: {color}; font-size: 18px; font-weight: bold;">{icon}</span>'
    
    get_status_icon.short_description = 'الحالة'
    get_status_icon.allow_tags = True
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # المشرفون يرون جلسات طلابهم فقط
            if request.user.user_type == 'supervisor':
                qs = qs.filter(student__supervisor=request.user)
        return qs


# ==========================================
# تخصيص Message Admin
# ==========================================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content_preview', 'is_read', 'get_read_icon', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'content')
    list_select_related = ('sender', 'recipient')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الرسالة', {
            'fields': ('sender', 'recipient', 'content', 'is_read')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        """عرض معاينة المحتوى"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'المحتوى'
    
    def get_read_icon(self, obj):
        """عرض أيقونة القراءة"""
        if obj.is_read:
            return '<span style="color: green; font-size: 18px;">✓</span>'
        return '<span style="color: red; font-size: 18px;">✗</span>'
    
    get_read_icon.short_description = 'مقروءة'
    get_read_icon.allow_tags = True
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # المستخدمون يرون رسائلهم فقط
            qs = qs.filter(
                models.Q(sender=request.user) | models.Q(recipient=request.user)
            )
        return qs
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """تحديد الرسائل كمقروءة"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'تم تحديد {updated} رسالة كمقروءة')
    
    mark_as_read.short_description = 'تحديد كمقروءة'
    
    def mark_as_unread(self, request, queryset):
        """تحديد الرسائل كغير مقروءة"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'تم تحديد {updated} رسالة كغير مقروءة')
    
    mark_as_unread.short_description = 'تحديد كغير مقروءة'


# ==========================================
# تخصيص TrialBooking Admin
# ==========================================
@admin.register(TrialBooking)
class TrialBookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'gender', 'country', 'is_contacted', 'created_at')
    list_filter = ('is_contacted', 'gender', 'country', 'created_at')
    search_fields = ('name', 'phone', 'email', 'country')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الحجز', {
            'fields': ('name', 'gender', 'country', 'phone', 'email')
        }),
        ('ملاحظات', {
            'fields': ('notes',)
        }),
        ('الحالة', {
            'fields': ('is_contacted', 'created_at'),
        }),
    )
    
    readonly_fields = ('created_at',)
    
    actions = ['mark_as_contacted', 'mark_as_not_contacted']
    
    def mark_as_contacted(self, request, queryset):
        """تحديد الحجوزات كتم التواصل معها"""
        updated = queryset.update(is_contacted=True)
        self.message_user(request, f'تم تحديد {updated} حجز كتم التواصل معه')
    
    mark_as_contacted.short_description = 'تحديد كتم التواصل'
    
    def mark_as_not_contacted(self, request, queryset):
        """تحديد الحجوزات كلم يتم التواصل معها"""
        updated = queryset.update(is_contacted=False)
        self.message_user(request, f'تم تحديد {updated} حجز كلم يتم التواصل معه')
    
    mark_as_not_contacted.short_description = 'تحديد كلم يتم التواصل'