"""الدفعة الحادية والثلاثون: دليل أجزاء القرآن الثلاثين (عربي وإنجليزي)، المقالان 2217-2218، وتوسيع مقال حفظ بدايات الأجزاء، وربط أدلة الأجزاء الستين بالدليل الجامع."""
from django.db import migrations

REFRESH = ['memorizing-juz-and-hizb-starts', 'juz-1-themes-and-summary', 'juz-1-of-the-quran-summary-english', 'juz-2-themes-and-summary', 'juz-2-of-the-quran-summary-english', 'juz-3-themes-and-summary', 'juz-3-of-the-quran-summary-english', 'juz-4-themes-and-summary', 'juz-4-of-the-quran-summary-english', 'juz-5-themes-and-summary', 'juz-5-of-the-quran-summary-english', 'juz-6-themes-and-summary', 'juz-6-of-the-quran-summary-english', 'juz-7-themes-and-summary', 'juz-7-of-the-quran-summary-english', 'juz-8-themes-and-summary', 'juz-8-of-the-quran-summary-english', 'juz-9-themes-and-summary', 'juz-9-of-the-quran-summary-english', 'juz-10-themes-and-summary', 'juz-10-of-the-quran-summary-english', 'juz-11-themes-and-summary', 'juz-11-of-the-quran-summary-english', 'juz-12-themes-and-summary', 'juz-12-of-the-quran-summary-english', 'juz-13-themes-and-summary', 'juz-13-of-the-quran-summary-english', 'juz-14-themes-and-summary', 'juz-14-of-the-quran-summary-english', 'juz-15-themes-and-summary', 'juz-15-of-the-quran-summary-english', 'juz-16-themes-and-summary', 'juz-16-of-the-quran-summary-english', 'juz-17-themes-and-summary', 'juz-17-of-the-quran-summary-english', 'juz-18-themes-and-summary', 'juz-18-of-the-quran-summary-english', 'juz-19-themes-and-summary', 'juz-19-of-the-quran-summary-english', 'juz-20-themes-and-summary', 'juz-20-of-the-quran-summary-english', 'juz-21-themes-and-summary', 'juz-21-of-the-quran-summary-english', 'juz-22-themes-and-summary', 'juz-22-of-the-quran-summary-english', 'juz-23-themes-and-summary', 'juz-23-of-the-quran-summary-english', 'juz-24-themes-and-summary', 'juz-24-of-the-quran-summary-english', 'juz-25-themes-and-summary', 'juz-25-of-the-quran-summary-english', 'juz-26-themes-and-summary', 'juz-26-of-the-quran-summary-english', 'juz-27-themes-and-summary', 'juz-27-of-the-quran-summary-english', 'juz-28-themes-and-summary', 'juz-28-of-the-quran-summary-english', 'juz-29-themes-and-summary', 'juz-29-of-the-quran-summary-english', 'juz-30-themes-and-summary', 'juz-30-of-the-quran-summary-english', 'history-of-juz-and-hizb-divisions']


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles, refresh_articles
    seed_articles(apps, schema_editor)
    refresh_articles(apps, REFRESH)


class Migration(migrations.Migration):
    dependencies = [('blog', '0033_seed_articles_wave30'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
