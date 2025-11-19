from django.urls import path, register_converter
from . import views

# تسجيل converter مخصص يدعم العربي
class UnicodeSlugConverter:
    regex = r'[\w\-]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value

register_converter(UnicodeSlugConverter, 'uslug')

urlpatterns = [
    # صفحة قائمة المقالات
    path("", views.blog_list, name="blog_list"),
    
    # صفحة مقالات تصنيف معين (تدعم العربي)
    path("category/<uslug:slug>/", views.category_posts, name="category_posts"),
    
    # صفحة تفاصيل المقال (تدعم العربي - يجب أن تكون آخر path)
    path("<uslug:slug>/", views.blog_detail, name="blog_detail"),
]