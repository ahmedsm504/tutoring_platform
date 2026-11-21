import csv

from django.contrib import admin
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import Application, ApplicationFile, FormQuestion, FormStep, JobOpening


def _size(n):
    n = n or 0
    return f'{n / 1024 / 1024:.1f} ميجا' if n >= 1024 * 1024 else f'{n // 1024} ك.ب'


class StepInline(admin.TabularInline):
    model = FormStep
    extra = 0
    fields = ('order', 'title')
    verbose_name_plural = 'خطوات النموذج (احفظ بعد إضافة خطوة جديدة عشان تقدر تختارها للأسئلة)'


class QuestionInline(admin.StackedInline):
    model = FormQuestion
    extra = 0
    show_change_link = True
    classes = ['collapse']
    fieldsets = (
        (None, {'fields': (('step', 'order', 'is_active'), ('qtype', 'required', 'role'), 'label', 'help_text',
                           'placeholder', 'choices')}),
        ('خيارات إضافية', {'classes': ['collapse'], 'fields': (
            'intro', ('required_answer', 'reject_message'), ('policy_title', 'policy_text'),
            ('min_words', 'min_length'), ('min_value', 'max_value'), ('max_files', 'file_kind'), 'quran_ref',
            ('half_width', 'highlight'))}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'step':
            job_id = request.resolver_match.kwargs.get('object_id')
            kwargs['queryset'] = FormStep.objects.filter(job_id=job_id) if job_id else FormStep.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'page_link', 'n_questions', 'n_apps', 'new_apps', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {}
    inlines = [StepInline, QuestionInline]
    save_on_top = True
    fieldsets = (
        ('الأساسيات', {'fields': (('title', 'slug'), ('is_active', 'order', 'icon'), 'card_text')}),
        ('أعلى الصفحة', {'fields': ('chip', 'h1', 'subtitle', 'intro', 'features', 'summary', 'important_note')}),
        ('الشروط والخطوات والأسئلة الشائعة', {'fields': ('requirements', 'process', 'faq', 'thanks_text')}),
        ('جوجل والسيو', {'classes': ['collapse'], 'fields': (
            'meta_title', 'meta_description', 'keywords', 'og_image', ('employment_type', 'date_posted', 'valid_through'),
            ('salary_value', 'salary_max', 'salary_unit', 'salary_currency'), ('experience_months', 'requires_degree'))}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _q=Count('questions', distinct=True), _a=Count('applications', distinct=True))

    @admin.display(description='الصفحة')
    def page_link(self, obj):
        return format_html('<a href="{}" target="_blank">فتح ↗</a>', obj.get_absolute_url())

    @admin.display(description='عدد الأسئلة', ordering='_q')
    def n_questions(self, obj):
        return obj._q

    @admin.display(description='الطلبات', ordering='_a')
    def n_apps(self, obj):
        url = reverse('admin:careers_application_changelist') + f'?job__id__exact={obj.pk}'
        return format_html('<a href="{}">{}</a>', url, obj._a)

    @admin.display(description='جديد')
    def new_apps(self, obj):
        n = obj.applications.filter(status='new').count()
        return format_html('<b style="color:#c00">{}</b>', n) if n else '0'


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    """تعديل سؤال واحد بالتفصيل (أو من داخل صفحة الوظيفة)"""
    list_display = ('label', 'job', 'step', 'order', 'qtype', 'required', 'is_active')
    list_filter = ('job', 'qtype', 'is_active')
    list_editable = ('order', 'required', 'is_active')
    search_fields = ('label',)
    fieldsets = (
        (None, {'fields': ('job',) + QuestionInline.fieldsets[0][1]['fields']}),
        ('خيارات إضافية', {'fields': QuestionInline.fieldsets[1][1]['fields']}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'step':
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                q = FormQuestion.objects.filter(pk=obj_id).first()
                if q:
                    kwargs['queryset'] = FormStep.objects.filter(job_id=q.job_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'job', 'wa_link', 'age', 'city', 'files_count', 'status', 'created_at')
    list_display_links = ('name',)
    list_editable = ('status',)
    list_filter = ('status', 'job', 'created_at', 'city')
    search_fields = ('name', 'phone', 'city', 'answers')
    date_hierarchy = 'created_at'
    actions = ['mark_reviewing', 'mark_interview', 'mark_accepted', 'mark_rejected', 'export_csv']
    readonly_fields = ('job', 'created_at', 'wa_link', 'name', 'age', 'city', 'attachments', 'answers_table')
    fieldsets = (
        ('القرار', {'fields': ('status', 'admin_notes')}),
        ('المتقدمة', {'fields': (('name', 'wa_link'), ('age', 'city'), ('job', 'created_at'))}),
        ('المرفقات والتسجيلات الصوتية', {'fields': ('attachments',)}),
        ('كل الإجابات', {'fields': ('answers_table',)}),
    )

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job').annotate(_files=Count('files'))

    @admin.display(description='واتساب', ordering='phone')
    def wa_link(self, obj):
        if not obj.phone:
            return '—'
        return format_html('<a href="https://wa.me/{}" target="_blank" rel="noopener" dir="ltr">{}</a>',
                           obj.phone.lstrip('+'), obj.phone)

    @admin.display(description='مرفقات', ordering='_files')
    def files_count(self, obj):
        return getattr(obj, '_files', 0)

    @admin.display(description='الإجابات')
    def answers_table(self, obj):
        rows, last = [], None
        for a in obj.answers or []:
            step = a.get('step', '')
            head = step if step != last else ''
            last = step
            rows.append((head, a.get('label', ''), a.get('value', '')))
        return format_html(
            '<table style="width:100%;border-collapse:collapse">{}</table>',
            format_html_join('', '{}<tr><th style="text-align:right;vertical-align:top;padding:8px;border-bottom:1px solid #eee;width:38%">{}</th>'
                                 '<td style="padding:8px;border-bottom:1px solid #eee;white-space:pre-wrap">{}</td></tr>',
                             ((format_html('<tr><td colspan="2" style="background:#eaf0ff;padding:6px 8px;font-weight:700">{}</td></tr>', h) if h else '', l, v)
                              for h, l, v in rows)))

    @admin.display(description='المرفقات والتسجيلات')
    def attachments(self, obj):
        files = obj.files.defer('data').order_by('pk')
        if not files:
            return '—'
        rows = []
        for f in files:
            url = reverse('careers:file', args=[f.pk])
            if f.is_image:
                body = format_html('<a href="{0}" target="_blank"><img src="{0}" alt="" style="max-width:260px;max-height:220px;border-radius:8px;border:1px solid #ddd"></a>', url)
            elif f.is_audio:
                body = format_html('<audio controls preload="none" src="{}" style="width:340px;max-width:100%"></audio>', url)
            else:
                body = format_html('<a href="{}" target="_blank">📄 فتح الملف</a>', url)
            rows.append((f.label, body, url, f.name, _size(f.size)))
        total = files.aggregate(s=Sum('size'))['s']
        return format_html(
            '<div style="display:grid;gap:16px">{}</div><p style="color:#666">إجمالي الحجم: {}</p>',
            format_html_join('', '<div><strong>{}</strong><br>{}<br><a href="{}?dl=1" style="font-size:12px">⬇ تنزيل: {}</a> '
                                 '<span style="color:#888;font-size:12px">({})</span></div>', rows),
            _size(total))

    def _mark(self, request, qs, status, label):
        self.message_user(request, f'تم تحديث {qs.update(status=status)} طلب إلى «{label}».')

    @admin.action(description='تحويل إلى: قيد المراجعة')
    def mark_reviewing(self, request, qs):
        self._mark(request, qs, 'reviewing', 'قيد المراجعة')

    @admin.action(description='تحويل إلى: اختبار / مقابلة')
    def mark_interview(self, request, qs):
        self._mark(request, qs, 'interview', 'اختبار / مقابلة')

    @admin.action(description='تحويل إلى: مقبول')
    def mark_accepted(self, request, qs):
        self._mark(request, qs, 'accepted', 'مقبول')

    @admin.action(description='تحويل إلى: مرفوض')
    def mark_rejected(self, request, qs):
        self._mark(request, qs, 'rejected', 'مرفوض')

    @admin.action(description='تصدير الطلبات المحددة إلى Excel (CSV)')
    def export_csv(self, request, qs):
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="job-applications.csv"'
        resp.write('﻿')
        labels = []
        for a in qs:
            for x in a.answers or []:
                if x.get('label') not in labels:
                    labels.append(x.get('label'))
        w = csv.writer(resp)
        w.writerow(['الوظيفة', 'الحالة', 'تاريخ التقديم'] + labels)
        for a in qs.select_related('job'):
            vals = {x.get('label'): x.get('value') for x in a.answers or []}
            w.writerow([a.job.title, a.get_status_display(), f'{a.created_at:%Y-%m-%d %H:%M}'] + [vals.get(l, '') for l in labels])
        return resp


@admin.register(ApplicationFile)
class ApplicationFileAdmin(admin.ModelAdmin):
    list_display = ('application', 'label', 'name', 'mime', 'size_txt', 'created_at')
    search_fields = ('application__name', 'name', 'label')
    readonly_fields = ('application', 'question', 'label', 'name', 'mime', 'size', 'created_at')

    def get_queryset(self, request):
        return super().get_queryset(request).defer('data').select_related('application')

    def has_add_permission(self, request):
        return False

    @admin.display(description='الحجم', ordering='size')
    def size_txt(self, obj):
        return _size(obj.size)
