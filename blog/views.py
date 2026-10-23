from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Post, Category, Comment, PostVideo

def blog_list(request):
    """عرض قائمة المقالات مع البحث والفلترة"""
    posts_list = Post.objects.filter(status='published').select_related('author', 'category')
    
    # البحث
    search_query = request.GET.get('search', '')
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
    featured_posts = Post.objects.filter(status='published', is_featured=True)[:3]
    
    # التصنيفات مع عدد المقالات
    categories = Category.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(posts_count__gt=0)
    
    # المقالات الأكثر قراءة
    popular_posts = Post.objects.filter(status='published').order_by('-views_count')[:5]
    
    # مجموع المشاهدات ✅
    total_views = Post.objects.filter(status='published').aggregate(
        total=Sum('views_count')
    )['total'] or 0

    # ✅ جديد: أحدث الفيديوهات من كل المقالات المنشورة (لعرضها في الشريط الجانبي)
    recent_videos = PostVideo.objects.filter(
        post__status='published'
    ).select_related('post').order_by('-id')[:4]

    # عدادات المدونة (كل المنشور، مش المفلتر)
    total_posts = Post.objects.filter(status='published').count()
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


def blog_detail(request, slug):
    """عرض تفاصيل مقال واحد"""
    post = Post.objects.filter(slug=slug, status='published').first()
    if post is None:
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
            messages.success(request, 'تم إرسال تعليقك بنجاح! سيتم عرضه بعد الموافقة عليه.')
            return redirect('blog_detail', slug=slug)
        else:
            messages.error(request, 'الرجاء ملء جميع الحقول!')
    
    context = {
        'post': post,
        'comments': comments,
        'comments_count': comments.count(),
        'related_posts': related_posts,
        'quran_surah': _surah_link(post),
        'prev_post': prev_post,
        'next_post': next_post,
        'gallery_images': gallery_images,
        'videos': videos,
    }
    
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
    posts_list = Post.objects.filter(
        status='published', category=category
    ).select_related('category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    # الشريط الجانبي (نفس بيانات صفحة المدونة)
    categories = Category.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(posts_count__gt=0)
    popular_posts = Post.objects.filter(status='published').order_by('-views_count')[:5]
    
    context = {
        'category': category,
        'posts': posts,
        'categories': categories,
        'popular_posts': popular_posts,
    }
    
    return render(request, 'blog/category_posts.html', context)
