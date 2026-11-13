"""مفتاح IndexNow اتغيّر، فبنمسح سجل التبليغات عشان كل روابط الـ sitemap تتبعت تاني بالمفتاح الجديد مع أول تشغيل."""
from django.db import migrations


def reset(apps, schema_editor):
    apps.get_model('core', 'IndexNowPing').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0015_pushlog')]
    operations = [migrations.RunPython(reset, migrations.RunPython.noop)]
