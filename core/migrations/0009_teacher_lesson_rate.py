# Generated for: سعر الحصة لكل معلمة (الراتب بالحلقات اللي تمت)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_supervisor_curriculum'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='lesson_rate',
            field=models.DecimalField(decimal_places=2, default=20, max_digits=8, verbose_name='سعر الحصة'),
        ),
    ]
