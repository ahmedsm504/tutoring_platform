import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Post, Category, Comment, PostVideo

def _indexable_categories():
    """التصنيفات اللي فيها مقالات مفهرسة، مع عددها"""
    counts = {}
    for cid in Post.objects.indexable().values_list('category_id', flat=True):
        counts[cid] = counts.get(cid, 0) + 1
    cats = list(Category.objects.filter(pk__in=[c for c in counts if c]))
    for c in cats:
        c.posts_count = counts[c.pk]
    return cats


def blog_list(request):
    """عرض قائمة المقالات مع البحث والفلترة"""
    # القوائم العامة بتعرض المقالات الطويلة المفهرسة بس (انظر INDEX_MIN_CHARS)، والبحث بيدور في كل المنشور
    search_query = request.GET.get('search', '')
    base_qs = Post.objects.published() if search_query else Post.objects.indexable()
    posts_list = base_qs.select_related('author', 'category')
    
    # البحث
    if search_query:
        posts_list = posts_list.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # الفلترة حسب التصنيف
    category_slug = request.GET.get('category', '')
    if category_slug:
        posts_list = posts_list.filter(category__slug=category_slug)
    
    # الترتيب
    sort_by = request.GET.get('sort', 'latest')
    if sort_by == 'popular':
        posts_list = posts_list.order_by('-views_count')
    elif sort_by == 'oldest':
        posts_list = posts_list.order_by('created_at')
    else:  # latest
        posts_list = posts_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # المقالات المميزة
    featured_posts = Post.objects.indexable().filter(is_featured=True)[:3]
    
    # التصنيفات مع عدد المقالات
    categories = _indexable_categories()
    
    # المقالات الأكثر قراءة
    popular_posts = Post.objects.indexable().order_by('-views_count')[:5]
    
    # مجموع المشاهدات ✅
    total_views = Post.objects.indexable().aggregate(
        total=Sum('views_count')
    )['total'] or 0

    # ✅ جديد: أحدث الفيديوهات من كل المقالات المنشورة (لعرضها في الشريط الجانبي)
    recent_videos = PostVideo.objects.filter(
        post__status='published'
    ).select_related('post').order_by('-id')[:4]

    # عدادات المدونة (كل المنشور، مش المفلتر)
    total_posts = Post.objects.indexable().count()
    try:
        from qna.models import PublicQuestion
        total_questions = PublicQuestion.objects.filter(status='approved').count()
    except Exception:
        total_questions = 0

    context = {
        'total_posts': total_posts,
        'total_questions': total_questions,
        'posts': posts,
        'featured_posts': featured_posts,
        'categories': categories,
        'popular_posts': popular_posts,
        'search_query': search_query,
        'current_category': category_slug,
        'current_sort': sort_by,
        'total_views': total_views,
        'recent_videos': recent_videos,
    }
    
    return render(request, 'blog/blog_list.html', context)


def _surah_link(post):
    from learning.quran import surah_from_title
    return surah_from_title(post.title)


def _listen_surah(post):
    """السورة اللي المقال عنها (للمشغل الصوتي): من العنوان العربي، أو للمقال الإنجليزي من المقال العربي المقابل"""
    r = _surah_link(post)
    if r:
        return r
    try:
        from content_seed import translation_pairs
        other = translation_pairs().get(post.slug)
    except Exception:
        other = None
    if other:
        title = Post.objects.filter(slug=other, status='published').values_list('title', flat=True).first()
        if title:
            return _surah_link(Post(title=title))
    return None


def _section_surahs(post, limit=8):
    """الصفحات الشاملة (مقالات مدموجة): السور اللي أقسامها بتتكلم عنها -> [(رقم، اسم)]"""
    if _surah_link(post):
        return []
    from core.templatetags.content_tags import toc
    from learning.quran import surah_from_title
    out = []
    for _, heading in toc(post.content):
        s = surah_from_title(heading)
        if s and s not in out:
            out.append(s)
    return out[:limit]


@lru_cache(maxsize=1)
def merged_redirects():
    """{slug قديم: 'slug_الصفحة_الشاملة#القسم'} للمقالات القصيرة اللي اتدمجت"""
    path = Path(settings.BASE_DIR) / 'content_seed' / 'merged_redirects.json'
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}


# slugs قديمة اتغيرت -> الـ slug الصحيح
SLUG_ALIASES = {
    'allah-name-al-awwal-al-akhir-az-zahir-al-batin-meaning': 'allah-names-al-awwal-al-akhir-meaning',
}


def blog_detail(request, slug):
    """عرض تفاصيل مقال واحد"""
    post = Post.objects.filter(slug=slug, status='published').first()
    if post is None:
        alias = SLUG_ALIASES.get(slug)
        if alias and alias not in merged_redirects():
            return redirect('blog_detail', slug=alias, permanent=True)
        # مقالات قصيرة اتدمجت في صفحة شاملة -> 301 للقسم بتاعها جوه الصفحة
        merged = merged_redirects().get(alias or slug)
        if merged:
            target, _, anchor = merged.partition('#')
            url = reverse('blog_detail', args=[target]) + (f'#{anchor}' if anchor else '')
            return HttpResponsePermanentRedirect(iri_to_uri(url))
        # لينكات قديمة أو مقطوعة (زي /blog/waqf-and-ibtid/) -> لو في مقال واحد بيبدأ بنفس الكلام نحوّل عليه
        if len(slug) >= 8:
            matches = list(Post.objects.filter(slug__startswith=slug, status='published').values_list('slug', flat=True)[:2])
            if len(matches) == 1:
                return redirect('blog_detail', slug=matches[0], permanent=True)
        raise Http404
    
    # زيادة عدد المشاهدات
    post.increment_views()
    
    # التعليقات المعتمدة فقط
    comments = post.comments.filter(is_approved=True).order_by('-created_at')
    
    # مقالات ذات صلة (من نفس التصنيف)
    from .related import related_posts as _related, prev_next
    related_posts = _related(post, limit=4)
    prev_post, next_post = prev_next(post)

    # ✅ جديد: معرض الصور وفيديوهات المقال
    gallery_images = post.gallery_images.all()
    videos = post.videos.all()
    
    # معالجة إرسال التعليق
    if request.method == 'POST' and post.allow_comments:
        author_name = request.POST.get('author_name', '').strip()
        author_email = request.POST.get('author_email', '').strip()
        content = request.POST.get('content', '').strip()
        
        if author_name and author_email and content:
            Comment.objects.create(
                post=post,
                author_name=author_name,
                author_email=author_email,
                content=content
            )
            messages.success(request, 'Thank you! Your comment will appear after review.' if post.title.isascii() or post.title[:1].isascii() else 'تم إرسال تعليقك بنجاح! سيتم عرضه بعد الموافقة عليه.')
            return redirect('blog_detail', slug=slug)
        else:
            messages.error(request, 'Please fill in all fields.' if post.title[:1].isascii() else 'الرجاء ملء جميع الحقول!')
    
    context = {
        'post': post,
        'comments': comments,
        'comments_count': comments.count(),
        'related_posts': related_posts,
        'quran_surah': _listen_surah(post),
        'quran_surahs': _section_surahs(post),
        'prev_post': prev_post,
        'next_post': next_post,
        'gallery_images': gallery_images,
        'videos': videos,
        'indexable': post.is_indexable,
    }
    
    from django.template.loader import render_to_string
    from core.templatetags.content_tags import is_latin
    context['mid_cta_html'] = render_to_string('blog/_mid_cta.html', {'en': is_latin(post.title)}, request=request)
    response = render(request, 'blog/blog_detail.html', context)
    if request.method == 'GET' and not request.user.is_authenticated:
        from django.utils.http import http_date
        changed = post.updated_at or post.published_at
        if changed:
            response['Last-Modified'] = http_date(changed.timestamp())
    return response


def category_posts(request, slug):
    """عرض مقالات تصنيف معين"""
    category = get_object_or_404(Category, slug=slug)
    posts_list = Post.objects.indexable().filter(
        category=category
    ).select_related('category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    # الشريط الجانبي (نفس بيانات صفحة المدونة)
    categories = _indexable_categories()
    popular_posts = Post.objects.indexable().order_by('-views_count')[:5]
    
    context = {
        'category': category,
        'posts': posts,
        'categories': categories,
        'popular_posts': popular_posts,
    }
    
    return render(request, 'blog/category_posts.html', context)
