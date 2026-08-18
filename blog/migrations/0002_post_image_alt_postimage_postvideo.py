# Generated manually to match Django's migration format (2025)
# ملحوظة: هذه الميجريشن إضافية فقط (Additive) - لا تحذف ولا تعدّل أي حقل قديم،
# لذلك آمنة تماماً على الـ 180 مقال المرفوعين بالتصميم القديم.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image_alt',
            field=models.CharField(blank=True, help_text='اختياري - لو تُرك فارغاً سيُستخدم عنوان المقال تلقائياً', max_length=200, verbose_name='النص البديل للصورة (Alt)'),
        ),
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='blog/gallery/', verbose_name='الصورة')),
                ('cloud_url', models.URLField(blank=True, null=True, verbose_name='رابط الصورة على كلاود')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='وصف الصورة (Alt/Caption)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='الترتيب')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='blog.post', verbose_name='المقال')),
            ],
            options={
                'verbose_name': 'صورة إضافية',
                'verbose_name_plural': '📷 معرض الصور',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PostVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('youtube', 'يوتيوب'), ('tiktok', 'تيك توك')], default='youtube', max_length=10, verbose_name='المنصة')),
                ('url', models.URLField(help_text='الصق رابط يوتيوب أو تيك توك هنا مباشرة', verbose_name='رابط الفيديو')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='عنوان الفيديو (اختياري)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='الترتيب')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='blog.post', verbose_name='المقال')),
            ],
            options={
                'verbose_name': 'فيديو',
                'verbose_name_plural': '🎬 الفيديوهات',
                'ordering': ['order', 'id'],
            },
        ),
    ]
