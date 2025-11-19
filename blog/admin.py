from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Post, Category, Comment

# ------------------ Category Admin ------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon_display', 'name', 'slug', 'posts_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def icon_display(self, obj):
        return format_html('<span style="font-size: 24px;">{}</span>', obj.icon or '📁')
    icon_display.short_description = 'الأيقونة'
    
    def posts_count(self, obj):
        count = obj.posts.filter(status='published').count()
        return format_html('<span style="font-weight: bold; color: #27ae60;">{} مقال</span>', count)
    posts_count.short_description = 'عدد المقالات'


# ------------------ Post Admin ------------------
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category_badge', 'status_badge', 'views_badge', 'reading_time_badge', 'featured_badge', 'published_at')
    list_filter = ('status', 'category', 'is_featured', 'created_at', 'published_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ('-created_at',)
    
    readonly_fields = ('views_count', 'reading_time', 'created_at', 'updated_at', 'image_preview')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'slug', 'author', 'category', 'status', 'is_featured')
        }),
        ('المحتوى', {
            'fields': ('excerpt', 'content', 'image', 'image_preview')
        }),
        ('التواريخ', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'reading_time'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        ('الإعدادات', {
            'fields': ('allow_comments',),
            'classes': ('collapse',)
        }),
    )
    
    def category_badge(self, obj):
        if obj.category:
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
                obj.category.icon or '📁',
                obj.category.name
            )
        return format_html('<span style="color: #95a5a6;">غير مصنف</span>')
    category_badge.short_description = 'التصنيف'
    
    def status_badge(self, obj):
        colors = {
            'published': '#27ae60',
            'draft': '#95a5a6'
        }
        icons = {
            'published': '✓',
            'draft': '○'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.status, '#95a5a6'),
            icons.get(obj.status, '○'),
            obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'
    
    def views_badge(self, obj):
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">👁 {}</span>',
            obj.views_count
        )
    views_badge.short_description = 'المشاهدات'
    
    def reading_time_badge(self, obj):
        return format_html(
            '<span style="color: #9b59b6;">⏱ {} دقيقة</span>',
            obj.reading_time
        )
    reading_time_badge.short_description = 'وقت القراءة'
    
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: #f39c12; font-size: 18px;">⭐</span>')
        return ''
    featured_badge.short_description = 'مميز'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px;"/>', obj.image.url)
        return 'لا توجد صورة'
    image_preview.short_description = 'معاينة الصورة'
    
    actions = ['make_published', 'make_draft', 'make_featured']
    
    def make_published(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'تم نشر {updated} مقال')
    make_published.short_description = 'نشر المقالات المحددة'
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'تم تحويل {updated} مقال إلى مسودة')
    make_draft.short_description = 'تحويل إلى مسودة'
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'تم تمييز {updated} مقال')
    make_featured.short_description = 'تمييز المقالات'


# ------------------ Comment Admin ------------------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'content_preview', 'approved_badge', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('معلومات المعلق', {
            'fields': ('author_name', 'author_email')
        }),
        ('التعليق', {
            'fields': ('post', 'content', 'is_approved', 'created_at')
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    content_preview.short_description = 'المحتوى'
    
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓</span> موافق عليه')
        return format_html('<span style="color: orange;">⏳</span> بانتظار الموافقة')
    approved_badge.short_description = 'الحالة'
    
    actions = ['approve_comments', 'unapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'تمت الموافقة على {updated} تعليق')
    approve_comments.short_description = 'الموافقة على التعليقات'
    
    def unapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'تم إلغاء الموافقة على {updated} تعليق')
    unapprove_comments.short_description = 'إلغاء الموافقة'