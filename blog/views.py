from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Post, Category, Comment

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
        posts_list = posts_list.order_by('published_at')
    else:  # latest
        posts_list = posts_list.order_by('-published_at')
    
    # Pagination
    paginator = Paginator(posts_list, 9)  # 9 مقالات في الصفحة
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
    
    context = {
        'posts': posts,
        'featured_posts': featured_posts,
        'categories': categories,
        'popular_posts': popular_posts,
        'search_query': search_query,
        'current_category': category_slug,
        'current_sort': sort_by,
    }
    
    return render(request, 'blog/blog_list.html', context)


def blog_detail(request, slug):
    """عرض تفاصيل مقال واحد"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    # زيادة عدد المشاهدات
    post.increment_views()
    
    # التعليقات المعتمدة فقط
    comments = post.comments.filter(is_approved=True).order_by('-created_at')
    
    # مقالات ذات صلة (من نفس التصنيف)
    related_posts = Post.objects.filter(
        status='published',
        category=post.category
    ).exclude(id=post.id)[:3]
    
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
    }
    
    return render(request, 'blog/blog_detail.html', context)


def category_posts(request, slug):
    """عرض مقالات تصنيف معين"""
    category = get_object_or_404(Category, slug=slug)
    posts_list = Post.objects.filter(status='published', category=category).order_by('-published_at')
    
    # Pagination
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
    }
    
    return render(request, 'blog/category_posts.html', context)