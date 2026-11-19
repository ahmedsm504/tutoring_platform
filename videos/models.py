"""مكتبة فيديوهات المؤسسة: الحلقات والفيديوهات اللي بترفعها على يوتيوب، وكل فيديو له صفحة خاصة بيه
على الموقع (/videos/<slug>/) فيها الفيديو + وصف مكتوب + VideoObject - عشان جوجل يفهرس الفيديو
في نتايج البحث وتبويب الفيديوهات، والزائر يتفرج من غير ما يخرج من الموقع."""
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

YT_ID = re.compile(r'(?:youtu\.be/|watch\?(?:.*&)?v=|/embed/|/shorts/|/live/)([A-Za-z0-9_-]{11})')


def parse_youtube_id(url):
    url = (url or '').strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', url):
        return url
    m = YT_ID.search(url)
    return m.group(1) if m else ''


def parse_duration(text):
    """'12:34' أو '1:02:03' أو '754' (ثواني) -> ثواني"""
    text = (text or '').strip()
    if not text:
        return None
    try:
        parts = [int(p) for p in text.split(':')]
    except ValueError:
        return None
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    return secs or None


class Video(models.Model):
    CATEGORY_CHOICES = [
        ('tajweed', 'التجويد'),
        ('hifz', 'الحفظ والمراجعة'),
        ('kids', 'للأطفال'),
        ('recitation', 'تلاوات'),
        ('classes', 'من حلقاتنا'),
        ('tafsir', 'معاني وتدبر'),
        ('english', 'English'),
        ('other', 'متنوع'),
    ]
    LANG_CHOICES = [('ar', 'عربي'), ('en', 'English')]

    title = models.CharField('عنوان الفيديو', max_length=200, blank=True,
                             help_text='لو سبتيه فاضي هيتجاب من يوتيوب تلقائي')
    slug = models.SlugField('الرابط', max_length=80, unique=True, blank=True, allow_unicode=True)
    youtube_url = models.CharField('رابط يوتيوب', max_length=300,
                                   help_text='الصق رابط الفيديو أو الشورتس من يوتيوب')
    youtube_id = models.CharField(max_length=11, editable=False, db_index=True)
    description = models.TextField('وصف الفيديو', blank=True,
                                   help_text='اكتب 3-6 سطور عن الفيديو: بيشرح إيه وبيفيد مين (ده اللي جوجل بيقراه)')
    transcript = models.TextField('نص الفيديو / النقاط المهمة (اختياري)', blank=True,
                                  help_text='كل ما زاد النص المكتوب، كل ما فرص ظهور الفيديو في البحث زادت')
    category = models.CharField('التصنيف', max_length=20, choices=CATEGORY_CHOICES, default='other')
    language = models.CharField('اللغة', max_length=2, choices=LANG_CHOICES, default='ar')
    duration = models.CharField('المدة (اختياري)', max_length=10, blank=True, help_text='مثلاً 12:34')
    is_short = models.BooleanField('فيديو شورتس (طولي)', default=False)
    related_post = models.ForeignKey('blog.Post', null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name='library_videos', verbose_name='مقال مرتبط (اختياري)')
    is_published = models.BooleanField('منشور', default=True)
    is_featured = models.BooleanField('مميز (يظهر فوق)', default=False)
    published_at = models.DateTimeField('تاريخ النشر', default=timezone.now)
    views_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-published_at']
        verbose_name = 'فيديو'
        verbose_name_plural = 'الفيديوهات'

    def __str__(self):
        return self.title or self.youtube_url

    def save(self, *args, **kwargs):
        self.youtube_id = parse_youtube_id(self.youtube_url)
        if '/shorts/' in (self.youtube_url or ''):
            self.is_short = True
        if not self.title and self.youtube_id:
            self.title = fetch_youtube_title(self.youtube_id) or ''
        if not self.slug:
            base = slugify(self.title or '', allow_unicode=True)[:60].strip('-') or f'video-{self.youtube_id.lower()}'
            slug, n = base, 2
            while Video.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('video_detail', args=[self.slug])

    @property
    def thumbnail_url(self):
        return f'https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg'

    @property
    def thumbnail_max(self):
        return f'https://i.ytimg.com/vi/{self.youtube_id}/maxresdefault.jpg'

    @property
    def embed_url(self):
        return f'https://www.youtube-nocookie.com/embed/{self.youtube_id}'

    @property
    def watch_url(self):
        return f'https://www.youtube.com/watch?v={self.youtube_id}'

    @property
    def duration_seconds(self):
        return parse_duration(self.duration)

    @property
    def iso_duration(self):
        s = self.duration_seconds
        if not s:
            return ''
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return 'PT' + (f'{h}H' if h else '') + (f'{m}M' if m else '') + f'{sec}S'

    @property
    def is_english(self):
        return self.language == 'en'


def fetch_youtube_title(video_id):
    """عنوان الفيديو من يوتيوب (oEmbed - من غير مفتاح API). مابيرميش أخطاء."""
    try:
        import requests
        r = requests.get('https://www.youtube.com/oembed',
                         params={'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'}, timeout=6)
        if r.ok:
            return (r.json().get('title') or '')[:200]
    except Exception:
        pass
    return ''
