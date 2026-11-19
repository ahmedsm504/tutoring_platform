from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import Video


def video_list(request):
    qs = Video.objects.filter(is_published=True)
    cat = request.GET.get('category', '')
    valid = dict(Video.CATEGORY_CHOICES)
    if cat in valid:
        qs = qs.filter(category=cat)
    else:
        cat = ''
    page = Paginator(qs, 18).get_page(request.GET.get('page'))
    used = set(Video.objects.filter(is_published=True).values_list('category', flat=True))
    featured = None
    if not cat and page.number == 1:
        featured = qs.filter(is_featured=True).first() or qs.first()
    return render(request, 'videos/video_list.html', {
        'videos': page, 'featured': featured, 'current_category': cat,
        'categories': [(k, v) for k, v in Video.CATEGORY_CHOICES if k in used],
        'total': Video.objects.filter(is_published=True).count(),
    })


def video_detail(request, slug):
    video = get_object_or_404(Video, slug=slug, is_published=True)
    Video.objects.filter(pk=video.pk).update(views_count=F('views_count') + 1)
    related = list(Video.objects.filter(is_published=True, category=video.category).exclude(pk=video.pk)[:6])
    if len(related) < 6:
        related += list(Video.objects.filter(is_published=True).exclude(pk__in=[video.pk] + [v.pk for v in related])[:6 - len(related)])
    ctx = {'video': video, 'related': related}
    if video.is_english:
        ctx['LANG'] = 'en'
        ctx['ALT_URL'] = '/videos/'
    return render(request, 'videos/video_detail.html', ctx)
