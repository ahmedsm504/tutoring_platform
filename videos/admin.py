from django.contrib import admin
from django.utils.html import format_html

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'title', 'category', 'language', 'is_published', 'is_featured', 'published_at', 'views_count')
    list_display_links = ('thumb', 'title')
    list_filter = ('category', 'language', 'is_published', 'is_featured')
    list_editable = ('is_published', 'is_featured')
    search_fields = ('title', 'description', 'youtube_url')
    autocomplete_fields = ('related_post',)
    readonly_fields = ('preview', 'views_count')
    fieldsets = (
        (None, {'fields': ('youtube_url', 'preview', 'title', 'slug', 'description', 'transcript')}),
        ('التصنيف والعرض', {'fields': ('category', 'language', 'duration', 'is_short', 'related_post',
                                       'is_published', 'is_featured', 'published_at', 'views_count')}),
    )

    @admin.display(description='')
    def thumb(self, obj):
        return format_html('<img src="{}" width="96" style="border-radius:8px">', obj.thumbnail_url) if obj.youtube_id else '-'

    @admin.display(description='معاينة')
    def preview(self, obj):
        if not obj.youtube_id:
            return 'هتظهر بعد الحفظ'
        return format_html('<a href="{}" target="_blank"><img src="{}" width="320" style="border-radius:12px"></a>',
                           obj.get_absolute_url(), obj.thumbnail_url)
