import json
import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .engine import validate
from .models import Application, ApplicationFile, JobOpening

logger = logging.getLogger(__name__)
RATE = 4  # أقصى عدد طلبات من نفس الجهاز في الساعة


def _ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR')) or None


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')


def _site():
    return settings.CANONICAL_URL.rstrip('/')


def _notify(app):
    try:
        from accounts.notifications import send_admin_notification, send_in_background
        url = _site() + reverse('admin:careers_application_change', args=[app.pk])
        send_in_background(send_admin_notification, f'📩 طلب توظيف جديد: {app.job.title}',
                           f'{app.name or "متقدمة جديدة"}{" – " + app.city if app.city else ""}', url)
    except Exception:
        logger.exception('تعذر إرسال إشعار طلب التوظيف')


def job_posting(job, url):
    site = _site()
    req = ''.join(f'<li>{t}{": " + d if d else ""}</li>' for _, t, d in job.requirements_list())
    desc = f'<p>{job.intro or job.h1}</p>' + (f'<p><strong>الشروط:</strong></p><ul>{req}</ul>' if req else '')
    if job.important_note:
        desc += f'<p>{job.important_note}</p>'
    data = {
        '@context': 'https://schema.org', '@type': 'JobPosting', 'title': job.title, 'description': desc,
        'datePosted': job.date_posted.isoformat(), 'employmentType': job.employment_type,
        'hiringOrganization': {'@type': 'Organization', 'name': 'مؤسسة العجمي لتحفيظ القرآن الكريم',
                               'sameAs': site + '/', 'logo': site + static('images/logo.png')},
        'jobLocationType': 'TELECOMMUTE',
        'applicantLocationRequirements': {'@type': 'Country', 'name': 'Egypt'},
        'directApply': True, 'url': url,
        'identifier': {'@type': 'PropertyValue', 'name': 'مؤسسة العجمي', 'value': job.slug},
    }
    if job.valid_through:
        data['validThrough'] = job.valid_through.isoformat() + 'T23:59'
    if job.salary_value:
        data['baseSalary'] = {'@type': 'MonetaryAmount', 'currency': job.salary_currency,
                              'value': {'@type': 'QuantitativeValue', 'value': float(job.salary_value),
                                        'unitText': job.salary_unit}}
    if job.experience_months:
        data['experienceRequirements'] = {'@type': 'OccupationalExperienceRequirements',
                                          'monthsOfExperience': job.experience_months}
    if job.requires_degree:
        data['educationRequirements'] = {'@type': 'EducationalOccupationalCredential',
                                         'credentialCategory': 'bachelor degree'}
    return data


def jobs_list(request):
    jobs = JobOpening.objects.filter(is_active=True)
    site = _site()
    items = {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'url': site + j.get_absolute_url(), 'name': j.title}
        for i, j in enumerate(jobs, 1)]}
    return render(request, 'careers/list.html', {'jobs': jobs, 'ldjson': [_ld(items)]})


def _questions(job):
    return list(job.questions.filter(is_active=True).select_related('step').order_by('step__order', 'order', 'pk'))


@require_http_methods(['GET', 'POST'])
def apply(request, slug):
    job = get_object_or_404(JobOpening, slug=slug)
    if not job.is_active and not request.user.is_staff:
        raise Http404
    ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    questions = _questions(job)
    errors, posted = {}, {}
    if request.method == 'POST':
        done_url = reverse('careers:done', args=[job.slug])
        if request.POST.get('website'):  # فخ للسبام
            return JsonResponse({'ok': True, 'redirect': done_url}) if ajax else redirect(done_url)
        rate_key = f'careers-rate:{_ip(request)}'
        if cache.get(rate_key, 0) >= RATE:
            errors = {'__all__': 'تم إرسال طلبات كثيرة من هذا الجهاز. حاولي مرة أخرى بعد ساعة.'}
        else:
            answers, files, meta, errors = validate(questions, request.POST, request.FILES)
            if not errors:
                with transaction.atomic():
                    app = Application.objects.create(job=job, answers=answers, ip=_ip(request),
                                                     **{k: meta.get(k, '') for k in ('name', 'phone', 'age', 'city')})
                    ApplicationFile.objects.bulk_create([
                        ApplicationFile(application=app, question=q, label=lbl[:250], name=n, mime=m, size=len(b), data=b)
                        for q, lbl, n, m, b in files])
                cache.set(rate_key, cache.get(rate_key, 0) + 1, 3600)
                _notify(app)
                return JsonResponse({'ok': True, 'redirect': done_url}) if ajax else redirect(done_url)
        if ajax:
            return JsonResponse({'ok': False, 'errors': errors}, status=429 if '__all__' in errors and len(errors) == 1 else 400)
        posted = request.POST

    steps = []
    for st in job.steps.all():
        qs = []
        for q in questions:
            if q.step_id != st.pk:
                continue
            q.value = posted.get(q.key, '') if posted else ''
            q.values = posted.getlist(q.key) if posted else []
            q.error = errors.get(q.key, '')
            q.verses = q.quran_verses() if q.qtype == 'audio' else []
            qs.append(q)
        if qs:
            steps.append({'step': st, 'questions': qs})

    site = _site()
    url = site + job.get_absolute_url()
    lds = [_ld(job_posting(job, url)),
           _ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
               {'@type': 'ListItem', 'position': 1, 'name': 'الرئيسية', 'item': site + '/'},
               {'@type': 'ListItem', 'position': 2, 'name': 'وظائف مؤسسة العجمي', 'item': site + reverse('careers:list')},
               {'@type': 'ListItem', 'position': 3, 'name': job.title, 'item': url}]})]
    faq = job.faq_list()
    if faq:
        lds.append(_ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}))
    others = JobOpening.objects.filter(is_active=True).exclude(pk=job.pk)
    return render(request, 'careers/apply.html', {
        'job': job, 'steps': steps, 'n_steps': len(steps), 'errors': errors, 'top_error': errors.get('__all__', ''), 'bound': bool(posted),
        'ldjson': lds, 'others': others,
    })


def done(request, slug):
    job = get_object_or_404(JobOpening, slug=slug)
    return render(request, 'careers/done.html', {'job': job})


@staff_member_required
def file_view(request, pk):
    f = get_object_or_404(ApplicationFile, pk=pk)
    data = bytes(f.data or b'')
    if not data:
        raise Http404
    resp = HttpResponse(data, content_type=f.mime)
    inline = (f.is_image or f.is_audio or f.mime == 'application/pdf') and request.GET.get('dl') != '1'
    resp['Content-Disposition'] = f"{'inline' if inline else 'attachment'}; filename*=UTF-8''{quote(f.name)}"
    resp['X-Content-Type-Options'] = 'nosniff'
    if f.mime != 'application/pdf':  # عارض PDF في كروم مبيشتغلش مع sandbox
        resp['Content-Security-Policy'] = "sandbox; default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'"
    resp['Cache-Control'] = 'private, max-age=3600'
    resp['X-Robots-Tag'] = 'noindex, nofollow'
    return resp
