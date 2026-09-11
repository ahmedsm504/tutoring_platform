# Generated for: نظام بورتال المشرفة + المنهج PDF + حالة "عذر" للحلقة

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_lesson_started_at_alter_lesson_auto_flagged'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Supervisor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='اسم المشرفة')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='رقم الهاتف')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشطة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor_profile', to=settings.AUTH_USER_MODEL, verbose_name='حساب الدخول')),
            ],
            options={
                'verbose_name': 'مشرفة',
                'verbose_name_plural': 'المشرفات',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CurriculumDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان الملف')),
                ('file', models.FileField(upload_to='curriculum/%Y/%m/', verbose_name='ملف PDF')),
                ('is_quran', models.BooleanField(default=False, verbose_name='هل هو المصحف؟')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='الترتيب')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط (ظاهر للمعلمات)')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')),
            ],
            options={
                'verbose_name': 'ملف منهج',
                'verbose_name_plural': 'ملفات المنهج',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.AddField(
            model_name='teacher',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teachers', to='core.supervisor', verbose_name='المشرفة المسؤولة'),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='status',
            field=models.CharField(
                choices=[
                    ('scheduled', 'مجدولة'),
                    ('completed', 'تمت'),
                    ('student_absent', 'الطالب غائب'),
                    ('excused', 'عذر'),
                    ('teacher_absent', 'المعلمة لم تتمكن من الحضور'),
                    ('cancelled', 'مؤجلة'),
                    ('unregistered', 'غير مسجلة'),
                ],
                default='scheduled', max_length=20, verbose_name='الحالة'
            ),
        ),
    ]
