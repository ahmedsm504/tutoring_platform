from django.contrib import admin

from .models import ChatMessage, Conversation


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    can_delete = False
    fields = ('created_at', 'sender_type', 'teacher', 'body', 'attachment_kind', 'status', 'flagged', 'flag_reasons', 'read_at')
    readonly_fields = fields
    ordering = ('-id',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('student', 'is_flagged', 'is_locked', 'teacher_unread', 'student_unread', 'last_message_at')
    list_filter = ('is_flagged', 'is_locked')
    search_fields = ('student__name',)
    raw_id_fields = ('student',)
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'conversation', 'sender_type', 'teacher', 'attachment_kind', 'status', 'flagged', 'read_at')
    list_filter = ('sender_type', 'status', 'flagged', 'attachment_kind', 'teacher')
    search_fields = ('body', 'conversation__student__name')
    raw_id_fields = ('conversation', 'sender_user', 'teacher')
    date_hierarchy = 'created_at'
