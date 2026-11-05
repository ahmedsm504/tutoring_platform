"""تحديث تاريخ التعديل ووقت القراءة للمقالات اللي اتوسعت في الدفعات 31-37.
refresh_articles القديمة كانت بتحدث المحتوى بـ update() من غير ما تلمس updated_at، فكان dateModified
و lastmod في السايت ماب ثابتين على تاريخ النشر الأول. ده بيصلحها مرة واحدة."""
from django.db import migrations

SLUGS = ['common-mistakes-surat-al-fatiha', 'history-of-juz-and-hizb-divisions', 'how-to-memorize-quran-plan', 'how-to-memorize-quran-step-by-step', 'juz-1-of-the-quran-summary-english', 'juz-1-themes-and-summary', 'juz-10-of-the-quran-summary-english', 'juz-10-themes-and-summary', 'juz-11-of-the-quran-summary-english', 'juz-11-themes-and-summary', 'juz-12-of-the-quran-summary-english', 'juz-12-themes-and-summary', 'juz-13-of-the-quran-summary-english', 'juz-13-themes-and-summary', 'juz-14-of-the-quran-summary-english', 'juz-14-themes-and-summary', 'juz-15-of-the-quran-summary-english', 'juz-15-themes-and-summary', 'juz-16-of-the-quran-summary-english', 'juz-16-themes-and-summary', 'juz-17-of-the-quran-summary-english', 'juz-17-themes-and-summary', 'juz-18-of-the-quran-summary-english', 'juz-18-themes-and-summary', 'juz-19-of-the-quran-summary-english', 'juz-19-themes-and-summary', 'juz-2-of-the-quran-summary-english', 'juz-2-themes-and-summary', 'juz-20-of-the-quran-summary-english', 'juz-20-themes-and-summary', 'juz-21-of-the-quran-summary-english', 'juz-21-themes-and-summary', 'juz-22-of-the-quran-summary-english', 'juz-22-themes-and-summary', 'juz-23-of-the-quran-summary-english', 'juz-23-themes-and-summary', 'juz-24-of-the-quran-summary-english', 'juz-24-themes-and-summary', 'juz-25-of-the-quran-summary-english', 'juz-25-themes-and-summary', 'juz-26-of-the-quran-summary-english', 'juz-26-themes-and-summary', 'juz-27-of-the-quran-summary-english', 'juz-27-themes-and-summary', 'juz-28-of-the-quran-summary-english', 'juz-28-themes-and-summary', 'juz-29-of-the-quran-summary-english', 'juz-29-themes-and-summary', 'juz-3-of-the-quran-summary-english', 'juz-3-themes-and-summary', 'juz-30-of-the-quran-summary-english', 'juz-30-themes-and-summary', 'juz-4-of-the-quran-summary-english', 'juz-4-themes-and-summary', 'juz-5-of-the-quran-summary-english', 'juz-5-themes-and-summary', 'juz-6-of-the-quran-summary-english', 'juz-6-themes-and-summary', 'juz-7-of-the-quran-summary-english', 'juz-7-themes-and-summary', 'juz-8-of-the-quran-summary-english', 'juz-8-themes-and-summary', 'juz-9-of-the-quran-summary-english', 'juz-9-themes-and-summary', 'learn-quran-online-for-kids', 'learn-tajweed-roadmap', 'learn-tajweed-roadmap-english', 'madd-rules-tajweed-english', 'madd-types-tajweed', 'makharij-al-huruf', 'makharij-al-huruf-english', 'meem-sakinah-rules', 'meem-sakinah-rules-english', 'memorizing-juz-and-hizb-starts', 'noon-sakinah-tanween-rules', 'noon-sakinah-tanween-rules-english', 'qalqalah-rules', 'qalqalah-rules-english', 'quran-revision-system', 'quran-revision-system-english', 'surah-al-fatiha-common-mistakes', 'teaching-quran-to-kids']


def bump(apps, schema_editor):
    from django.utils import timezone
    from content_seed import load_articles
    Post = apps.get_model('blog', 'Post')
    by_slug = {a['slug']: a for a in load_articles()}
    now = timezone.now()
    for slug in SLUGS:
        a = by_slug.get(slug)
        if a:
            Post.objects.filter(slug=slug).update(updated_at=now, reading_time=int(a.get('reading', 5)))


class Migration(migrations.Migration):
    dependencies = [('blog', '0040_seed_articles_wave37')]
    operations = [migrations.RunPython(bump, migrations.RunPython.noop)]
